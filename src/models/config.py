"""
Configuration data models for the application.
"""

import json
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TelegramConfig(BaseModel):
    """Telegram API configuration."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "app_id": 12345,
                "app_hash": "0123456789abcdef0123456789abcdef",
                "session_name": "telegram_session",
            }
        }
    )

    app_id: Optional[int] = None
    app_hash: Optional[str] = None
    session_name: str = "telegram_session"

    def is_valid(self) -> bool:
        """Check if configuration has required fields."""
        return self.app_id is not None and self.app_hash is not None


class ExportConfig(BaseModel):
    """Configuration for exporting deleted messages."""

    chat_id: Optional[int] = None
    chat_title: Optional[str] = None
    output_directory: str = "exported_messages"
    export_mode: Literal["all", "media_only", "text_only"] = "all"
    min_message_id: int = Field(default=0, ge=0)
    max_message_id: int = Field(default=0, ge=0)

    @field_validator("output_directory")
    @classmethod
    def validate_output_directory(cls, v: str) -> str:
        """Validate output directory is not empty."""
        if not v or not v.strip():
            raise ValueError("Output directory cannot be empty")
        return v.strip()


class ResendConfig(BaseModel):
    """Configuration for re-sending messages."""

    target_chat_id: Optional[int] = None
    target_chat_title: Optional[str] = None
    source_directory: str = "exported_messages"
    include_media: bool = True
    include_text: bool = True

    # Header component toggles (granular control)
    show_sender_name: bool = True
    show_sender_username: bool = True
    show_date: bool = True
    show_reply_link: bool = True

    # Timezone configuration
    timezone_offset_hours: int = 0  # UTC offset (e.g., 3 for Moscow)

    # Reply link formatting
    use_hidden_reply_links: bool = True  # Use HTML <a> tags

    # Message batching
    enable_batching: bool = False
    batch_max_messages: int = 7  # Merge up to 7 messages
    batch_time_window_minutes: int = 10  # Within 10 minutes
    batch_max_message_length: int = 150  # Only batch short messages

    @field_validator("source_directory")
    @classmethod
    def validate_source_directory(cls, v: str) -> str:
        """Validate source directory is not empty."""
        if not v or not v.strip():
            raise ValueError("Source directory cannot be empty")
        return v.strip()


class AppConfig(BaseModel):
    """Main application configuration."""

    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)
    resend: ResendConfig = Field(default_factory=ResendConfig)
    config_file: str = "app_config.json"

    def save(self, file_path: Optional[str] = None) -> None:
        """Save configuration to file."""
        path = Path(file_path or self.config_file)
        data = {
            "telegram": self.telegram.model_dump(),
            "export": self.export.model_dump(),
            "resend": self.resend.model_dump(),
        }

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write configuration to file
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, file_path: str = "app_config.json") -> "AppConfig":
        """Load configuration from file."""
        path = Path(file_path)

        if not path.exists():
            return cls(config_file=file_path)

        # Load configuration from file
        data = json.loads(path.read_text(encoding="utf-8"))

        return cls(
            telegram=TelegramConfig(**data.get("telegram", {})),
            export=ExportConfig(**data.get("export", {})),
            resend=ResendConfig(**data.get("resend", {})),
            config_file=file_path,
        )
