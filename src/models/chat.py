"""
Chat data models.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, computed_field


class ChatInfo(BaseModel):
    """Information about a Telegram chat."""

    chat_id: int
    title: str
    chat_type: Literal["channel", "group", "supergroup", "user", "chat"]
    username: Optional[str] = None
    participant_count: Optional[int] = Field(default=None, ge=0)
    description: Optional[str] = None
    last_message_date: Optional[datetime] = None

    @computed_field
    @property
    def display_name(self) -> str:
        """Get display name for the chat."""
        if self.username:
            return f"{self.title} (@{self.username})"
        return self.title

    @computed_field
    @property
    def chat_type_display(self) -> str:
        """Get human-readable chat type."""
        type_map = {
            "channel": "Channel",
            "group": "Group",
            "supergroup": "Supergroup",
            "user": "User",
            "chat": "Chat",
        }
        return type_map.get(self.chat_type, self.chat_type.capitalize())

    def __str__(self) -> str:
        """String representation."""
        return f"{self.display_name} [{self.chat_type_display}]"

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat() if v else None}
