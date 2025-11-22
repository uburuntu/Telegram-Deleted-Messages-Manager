"""
Path utilities for handling file locations in standalone builds.
"""

import sys
from pathlib import Path


def get_app_directory() -> Path:
    """
    Get the application directory.

    This returns different paths depending on how the app is run:
    - When run from source: the project root directory
    - When run as PyInstaller bundle: the directory containing the executable
    - When run as macOS .app: the Resources directory inside the bundle

    Returns:
        Path object pointing to the app directory
    """
    if getattr(sys, "frozen", False):
        # Running as compiled executable
        if sys.platform == "darwin" and ".app/" in sys.executable:
            # macOS .app bundle - use the Resources directory
            app_path = Path(sys.executable).parent.parent / "Resources"
        else:
            # Regular executable - use the directory containing the executable
            app_path = Path(sys.executable).parent
    else:
        # Running from source - use current working directory
        app_path = Path.cwd()

    return app_path


def get_session_file_path(session_name: str = "telegram_session") -> str:
    """
    Get the full path for a Telethon session file.

    Args:
        session_name: Base name for the session file (without .session extension)

    Returns:
        Absolute path to the session file
    """
    app_dir = get_app_directory()
    session_path = app_dir / f"{session_name}.session"
    return str(session_path)


def get_config_file_path(config_name: str = "app_config.json") -> str:
    """
    Get the full path for the config file.

    Args:
        config_name: Name of the config file

    Returns:
        Absolute path to the config file
    """
    app_dir = get_app_directory()
    config_path = app_dir / config_name
    return str(config_path)


def ensure_app_directory() -> Path:
    """
    Ensure the app directory exists and return it.

    Returns:
        Path object pointing to the app directory
    """
    app_dir = get_app_directory()
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_user_data_directory() -> Path:
    """
    Get the user data directory for exports and user-generated content.

    This directory is always writable, unlike the app directory which may be
    read-only in standalone builds (especially macOS .app bundles).

    Returns different paths depending on the platform and run mode:
    - macOS: ~/Documents/TelegramDeletedMessagesManager/
    - Windows: ~/Documents/TelegramDeletedMessagesManager/
    - Linux: ~/Documents/TelegramDeletedMessagesManager/
    - Development mode: project root directory

    Returns:
        Path object pointing to the user data directory
    """
    if getattr(sys, "frozen", False):
        # Running as standalone - use Documents folder
        home = Path.home()
        user_data_dir = home / "Documents" / "TelegramDeletedMessagesManager"
    else:
        # Running from source - use project root
        user_data_dir = Path.cwd()

    # Ensure directory exists
    user_data_dir.mkdir(parents=True, exist_ok=True)
    return user_data_dir
