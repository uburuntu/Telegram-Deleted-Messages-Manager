"""
Message data models.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, computed_field


class DeletedMessage(BaseModel):
    """Represents a deleted Telegram message."""

    model_config = ConfigDict(ser_json_timedelta="iso8601")

    message_id: int
    chat_id: int
    sender_id: Optional[int] = None
    sender_name: Optional[str] = None
    sender_username: Optional[str] = None
    text: Optional[str] = None
    date: Optional[datetime] = None
    has_media: bool = False
    media_type: Optional[str] = None
    media_file_path: Optional[str] = None
    reply_to_msg_id: Optional[int] = None
    reply_to_top_id: Optional[int] = None
    quote_text: Optional[str] = None

    def get_formatted_date(self, timezone_offset_hours: int = 0) -> str:
        """
        Get formatted date string with timezone adjustment.

        Args:
            timezone_offset_hours: UTC offset in hours (e.g., 3 for Moscow UTC+3)

        Returns:
            Formatted date string without timezone indicator
        """
        if not self.date:
            return "Unknown date"

        adjusted_date = self.date + timedelta(hours=timezone_offset_hours)
        return adjusted_date.strftime("%Y %b %d, %H:%M")

    @computed_field
    @property
    def sender_display(self) -> str:
        """Get display name for sender."""
        if self.sender_name:
            if self.sender_username:
                return f"{self.sender_name} (@{self.sender_username})"
            return self.sender_name
        if self.sender_username:
            return f"@{self.sender_username}"
        return "Unknown User"

    @computed_field
    @property
    def has_text(self) -> bool:
        """Check if message has text content."""
        return bool(self.text and self.text.strip())

    def __str__(self) -> str:
        """String representation."""
        media_info = f" [Media: {self.media_type}]" if self.has_media else ""
        text_preview = (
            self.text[:50] + "..."
            if self.text and len(self.text) > 50
            else self.text or ""
        )
        return f"Message {self.message_id} from {self.sender_display}{media_info}: {text_preview}"


class ExportProgress(BaseModel):
    """Track export progress."""

    total_messages: int = 0
    processed_messages: int = 0
    exported_text_messages: int = 0
    exported_media_messages: int = 0
    failed_messages: int = 0
    current_message_id: Optional[int] = None
    is_complete: bool = False
    is_cancelled: bool = False
    error_message: Optional[str] = None
    start_time: Optional[datetime] = None

    @computed_field
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_messages == 0:
            return 0.0
        return (self.processed_messages / self.total_messages) * 100

    @computed_field
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.processed_messages == 0:
            return 0.0
        successful = self.processed_messages - self.failed_messages
        return (successful / self.processed_messages) * 100

    @computed_field
    @property
    def elapsed_seconds(self) -> float:
        """Calculate elapsed time in seconds."""
        if not self.start_time:
            return 0.0
        now = datetime.now(timezone.utc)
        elapsed = now - self.start_time.replace(tzinfo=timezone.utc)
        return elapsed.total_seconds()

    @computed_field
    @property
    def estimated_total_seconds(self) -> Optional[float]:
        """Calculate estimated total time in seconds based on current progress."""
        if self.processed_messages == 0 or not self.start_time:
            return None
        if self.total_messages == 0:
            return None
        avg_time_per_message = self.elapsed_seconds / self.processed_messages
        return avg_time_per_message * self.total_messages

    @computed_field
    @property
    def estimated_remaining_seconds(self) -> Optional[float]:
        """Calculate estimated remaining time in seconds."""
        if not self.estimated_total_seconds:
            return None
        remaining = self.estimated_total_seconds - self.elapsed_seconds
        return max(0.0, remaining)

    @computed_field
    @property
    def formatted_elapsed_time(self) -> str:
        """Get formatted elapsed time string (HH:MM:SS)."""
        elapsed = int(self.elapsed_seconds)
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    @computed_field
    @property
    def formatted_eta(self) -> str:
        """Get formatted ETA string (HH:MM:SS)."""
        if not self.estimated_remaining_seconds:
            return "Calculating..."
        remaining = int(self.estimated_remaining_seconds)
        hours, remainder = divmod(remaining, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
