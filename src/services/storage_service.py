"""
Service for file and data storage management.
"""

import json
import shutil
from pathlib import Path
from typing import List, Optional

from ..models.config import AppConfig
from ..models.message import DeletedMessage
from ..utils.paths import get_config_file_path, get_user_data_directory


class StorageService:
    """Service for managing file storage and data persistence."""

    def __init__(self, base_directory: Optional[str] = None):
        """
        Initialize storage service.

        Args:
            base_directory: Base directory for storing data (uses user data directory if None)
        """
        if base_directory is None:
            self.base_directory = get_user_data_directory()
        else:
            self.base_directory = Path(base_directory)

    def ensure_directory(self, directory: str) -> Path:
        """
        Ensure a directory exists, creating it if necessary.

        Args:
            directory: Directory path (absolute or relative)

        Returns:
            Path object for the directory
        """
        dir_path = Path(directory)
        if not dir_path.is_absolute():
            dir_path = self.base_directory / directory

        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    def get_export_directory(self, directory: str) -> Path:
        """
        Get and ensure export directory exists.

        Args:
            directory: Export directory path

        Returns:
            Path object for the export directory
        """
        return self.ensure_directory(directory)

    def save_config(self, config: AppConfig, file_path: Optional[str] = None) -> None:
        """
        Save application configuration.

        Args:
            config: AppConfig to save
            file_path: Optional custom file path
        """
        path = file_path or config.config_file
        config.save(path)

    def load_config(self, file_path: Optional[str] = None) -> AppConfig:
        """
        Load application configuration.

        Args:
            file_path: Configuration file path (uses app directory if None)

        Returns:
            Loaded AppConfig
        """
        if file_path is None:
            file_path = get_config_file_path()
        return AppConfig.load(file_path)

    def config_exists(self, file_path: str = "app_config.json") -> bool:
        """
        Check if configuration file exists.

        Args:
            file_path: Configuration file path

        Returns:
            True if configuration file exists
        """
        return Path(file_path).exists()

    def save_messages_metadata(
        self, messages: List[DeletedMessage], directory: str
    ) -> None:
        """
        Save messages metadata to JSON file.

        Args:
            messages: List of DeletedMessage objects
            directory: Directory to save metadata in
        """
        dir_path = self.ensure_directory(directory)
        metadata_file = dir_path / "messages_metadata.json"

        messages_data = [msg.model_dump(mode="json") for msg in messages]

        metadata_file.write_text(
            json.dumps(messages_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def load_messages_metadata(self, directory: str) -> List[DeletedMessage]:
        """
        Load messages metadata from JSON file.

        Args:
            directory: Directory containing metadata file

        Returns:
            List of DeletedMessage objects

        Raises:
            FileNotFoundError: If metadata file doesn't exist
        """
        metadata_file = Path(directory) / "messages_metadata.json"

        if not metadata_file.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_file}")

        messages_data = json.loads(metadata_file.read_text(encoding="utf-8"))
        return [DeletedMessage(**msg_data) for msg_data in messages_data]

    def get_export_statistics(self, directory: str) -> dict:
        """
        Get statistics about an export directory.

        Args:
            directory: Export directory path

        Returns:
            Dictionary with statistics
        """
        dir_path = Path(directory)

        if not dir_path.exists():
            return {
                "exists": False,
                "total_messages": 0,
                "total_files": 0,
                "total_size_bytes": 0,
            }

        # Count files using Path methods
        files = [f for f in dir_path.glob("*") if f.is_file()]
        total_files = len(files)
        total_size = sum(f.stat().st_size for f in files)

        # Load metadata if available
        total_messages = 0
        metadata_file = dir_path / "messages_metadata.json"
        if metadata_file.exists():
            try:
                messages = self.load_messages_metadata(directory)
                total_messages = len(messages)
            except Exception:
                pass

        return {
            "exists": True,
            "total_messages": total_messages,
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }

    def list_export_directories(self) -> List[str]:
        """
        List all export directories in the base directory.

        Returns:
            List of relative directory paths (from base_directory) that contain metadata files
        """
        if not self.base_directory.exists():
            return []

        export_dirs = []

        # Look for metadata files in common export locations
        # First check direct children
        for item in self.base_directory.iterdir():
            if item.is_dir() and (item / "messages_metadata.json").exists():
                export_dirs.append(item.name)

        # Also check in exported_messages subdirectory
        exported_messages_dir = self.base_directory / "exported_messages"
        if exported_messages_dir.exists() and exported_messages_dir.is_dir():
            for item in exported_messages_dir.iterdir():
                if item.is_dir() and (item / "messages_metadata.json").exists():
                    # Return path relative to base_directory
                    export_dirs.append(f"exported_messages/{item.name}")

        return sorted(export_dirs)

    def delete_export_directory(self, directory: str, *, force: bool = False) -> bool:
        """
        Delete an export directory.

        Args:
            directory: Directory to delete
            force: If True, delete without confirmation (keyword-only)

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If force is False (safety measure)
        """
        if not force:
            raise ValueError(
                "Must set force=True to delete directory. This is a safety measure."
            )

        dir_path = Path(directory)

        if not dir_path.exists():
            return False

        # Use shutil.rmtree for recursive deletion (modern approach)
        shutil.rmtree(dir_path)
        return True
