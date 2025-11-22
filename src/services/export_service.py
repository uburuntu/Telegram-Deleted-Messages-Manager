"""
Service for exporting deleted messages from Telegram.
"""

import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Callable, List, Optional

from telethon.errors import FloodWaitError, RPCError
from telethon.tl.types import Channel, Message, PeerChannel, PeerChat, PeerUser, User

from ..models.config import ExportConfig
from ..models.message import DeletedMessage, ExportProgress
from ..utils.logger import get_logger
from .telegram_service import TelegramService

logger = get_logger(__name__)
ProgressCallback = Callable[[ExportProgress], Awaitable[None]]

# Constants
MAX_PARALLEL_DOWNLOADS = 4
ADMIN_LOG_BATCH_SIZE = 100
MAX_DOWNLOAD_RETRIES = 3
MAX_METADATA_RETRIES = 3
RETRY_BACKOFF_BASE = 1  # seconds
CHUNK_SIZE = 500  # Process media downloads in chunks to manage memory


class ExportService:
    """Service for exporting deleted Telegram messages."""

    def __init__(self, telegram_service: TelegramService):
        """
        Initialize export service.

        Args:
            telegram_service: TelegramService instance
        """
        self.telegram_service = telegram_service
        self._current_progress: Optional[ExportProgress] = None
        self._progress_lock = asyncio.Lock()

    @property
    def current_progress(self) -> Optional[ExportProgress]:
        """Get current export progress."""
        return self._current_progress

    def _sanitize_folder_name(self, name: str, chat_id: int) -> str:
        """
        Sanitize folder name by removing invalid characters.

        Args:
            name: Chat title or name
            chat_id: Chat ID to append for uniqueness

        Returns:
            Sanitized folder name
        """
        # Remove or replace invalid characters for folder names
        sanitized = re.sub(r'[<>:"/\\|?*]', "_", name)
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip(". ")
        # Limit length to 100 characters
        sanitized = sanitized[:100]
        # Append chat ID for uniqueness
        return f"{sanitized}_{chat_id}"

    async def _call_progress_callback(
        self, callback: Optional[ProgressCallback], progress: ExportProgress
    ) -> None:
        """
        Safely call progress callback.

        Args:
            callback: Progress callback function
            progress: Progress object to pass to callback
        """
        if callback:
            result = callback(progress)
            if asyncio.iscoroutine(result):
                await result

    async def export_deleted_messages(
        self,
        config: ExportConfig,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> ExportProgress:
        """
        Export deleted messages from a chat.

        Args:
            config: Export configuration
            progress_callback: Optional callback for progress updates

        Returns:
            ExportProgress with final statistics
        """
        if not self.telegram_service.is_connected:
            raise RuntimeError("Telegram service is not connected")

        if not config.chat_id:
            raise ValueError("Chat ID is required for export")

        # Initialize progress tracking with start time
        self._current_progress = ExportProgress(start_time=datetime.now(timezone.utc))
        logger.info(
            f"Starting export for chat {config.chat_id} to {config.output_directory}"
        )

        try:
            # Get chat entity first to get the title
            logger.debug(f"Fetching chat entity for ID: {config.chat_id}")
            chat_entity = await self.telegram_service.client.get_entity(config.chat_id)

            # Validate that this is a channel/supergroup (admin logs only work for these)
            if not isinstance(chat_entity, Channel):
                entity_type = type(chat_entity).__name__
                title = getattr(chat_entity, "title", None) or getattr(
                    chat_entity, "first_name", "Unknown"
                )
                error_msg = (
                    f"Cannot export from '{title}' ({entity_type}). "
                    f"Admin logs are only available for channels and supergroups. "
                    f"Private chats, regular groups, and 'Saved Messages' are not supported."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

            chat_title = getattr(chat_entity, "title", "Unknown")
            logger.info(f"Connected to chat: {chat_title}")

            # Create chat-specific output directory
            base_dir = Path(config.output_directory)
            chat_folder = self._sanitize_folder_name(chat_title, config.chat_id)
            output_dir = base_dir / chat_folder
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")

            # Prepare metadata file using Path
            metadata_file = output_dir / "messages_metadata.json"
            messages_dict: dict[
                int, dict
            ] = {}  # message_id -> message_data for O(1) lookups

            # PHASE 1: Fast metadata extraction
            # Iterate through admin log and collect all messages with metadata
            limit_per_batch = ADMIN_LOG_BATCH_SIZE
            current_max_id = config.max_message_id or 0
            messages_with_media = []  # Store (raw_message, deleted_msg, output_dir)

            logger.info("Phase 1: Extracting metadata from admin log")
            while True:
                logger.debug(f"Fetching admin log batch (max_id={current_max_id})")
                events = [
                    event
                    async for event in self.telegram_service.client.iter_admin_log(
                        chat_entity,
                        min_id=config.min_message_id or 0,
                        max_id=current_max_id or 0,
                        limit=limit_per_batch,
                        delete=True,
                    )
                ]

                if not events:
                    logger.debug("No more events found")
                    break

                logger.info(
                    f"Processing {len(events)} deleted message events (metadata)"
                )

                # Extract metadata from each deleted message (fast, no media download)
                for event in events:
                    if event.deleted_message and event.old:
                        result = await self._extract_message_metadata_with_retry(
                            event.old,
                            output_dir,
                            config,
                            messages_dict,
                        )
                        if result:  # If message has media to download
                            messages_with_media.append(result)

                # Update max_id for next batch
                current_max_id = events[-1].id - 1

                if current_max_id < config.min_message_id:
                    logger.debug("Reached minimum message ID")
                    break

            # PHASE 2: Parallel media download
            if messages_with_media:
                # Set total messages for accurate progress tracking
                self._current_progress.total_messages = len(messages_with_media)

                logger.info(
                    f"Phase 2: Downloading media for {len(messages_with_media)} messages "
                    f"(up to {MAX_PARALLEL_DOWNLOADS} parallel downloads)"
                )
                await self._download_media_parallel(
                    messages_with_media, config, progress_callback
                )

            # Save metadata (sorted by date, oldest first)
            if messages_dict:
                logger.info(f"Saving metadata for {len(messages_dict)} messages")
                # Convert dict to list and sort messages by date (oldest first)
                messages_data = list(messages_dict.values())
                messages_data.sort(key=lambda m: m.get("date") or "")
                metadata_file.write_text(
                    json.dumps(messages_data, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )

            # Mark as complete
            self._current_progress.is_complete = True
            logger.info(
                f"Export complete: {self._current_progress.exported_text_messages} text, "
                f"{self._current_progress.exported_media_messages} media, "
                f"{self._current_progress.failed_messages} failed"
            )

            await self._call_progress_callback(
                progress_callback, self._current_progress
            )

        except RPCError as e:
            error_msg = f"Telegram API error: {e}"
            logger.error(error_msg)
            self._current_progress.error_message = error_msg
            self._current_progress.is_complete = True
            await self._call_progress_callback(
                progress_callback, self._current_progress
            )
            raise RuntimeError(self._current_progress.error_message) from e
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.exception(error_msg)
            self._current_progress.error_message = error_msg
            self._current_progress.is_complete = True
            await self._call_progress_callback(
                progress_callback, self._current_progress
            )
            raise

        return self._current_progress

    async def _download_media_parallel(
        self,
        messages_with_media: List[tuple],
        config: ExportConfig,
        progress_callback: Optional[ProgressCallback],
    ) -> None:
        """
        Download media for multiple messages in parallel.

        Args:
            messages_with_media: List of (raw_message, deleted_msg, output_dir, messages_dict) tuples
            config: Export configuration
            progress_callback: Optional progress callback
        """
        semaphore = asyncio.Semaphore(MAX_PARALLEL_DOWNLOADS)

        async def download_with_semaphore(item: tuple):
            async with semaphore:
                await self._download_single_media(item, config, progress_callback)

        # Download all media in parallel
        results = await asyncio.gather(
            *[download_with_semaphore(item) for item in messages_with_media],
            return_exceptions=True,
        )

        # Log any exceptions that occurred during parallel downloads
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"Failed to download media for message at index {i}: {result}",
                    exc_info=result,
                )

    async def _download_single_media(
        self,
        item: tuple,
        config: ExportConfig,
        progress_callback: Optional[ProgressCallback],
    ) -> None:
        """
        Download media for a single message with retry logic.

        Args:
            item: Tuple of (raw_message, deleted_msg, output_dir, messages_dict)
            config: Export configuration
            progress_callback: Optional progress callback
        """
        raw_message, deleted_msg, output_dir, messages_dict = item
        message_id = raw_message.id

        media_path = output_dir / str(message_id)
        max_retries = MAX_DOWNLOAD_RETRIES
        retry_count = 0

        # Update progress (thread-safe)
        async with self._progress_lock:
            self._current_progress.processed_messages += 1
            self._current_progress.current_message_id = message_id

        while retry_count < max_retries:
            try:
                logger.debug(f"Downloading media for message {message_id}")
                downloaded_path = await self.telegram_service.client.download_media(
                    raw_message.media, file=str(media_path)
                )

                # Handle None return from download_media
                if downloaded_path:
                    # Verify file exists and has content
                    downloaded_file = Path(downloaded_path)
                    if downloaded_file.exists() and downloaded_file.stat().st_size > 0:
                        deleted_msg.media_file_path = str(downloaded_path)

                        # Update progress (thread-safe)
                        async with self._progress_lock:
                            self._current_progress.exported_media_messages += 1

                        logger.debug(
                            f"Media downloaded to: {downloaded_path} "
                            f"({downloaded_file.stat().st_size} bytes)"
                        )

                        # Update metadata with media file path (O(1) dict lookup)
                        if message_id in messages_dict:
                            messages_dict[message_id]["media_file_path"] = str(
                                downloaded_path
                            )
                    else:
                        logger.warning(
                            f"Downloaded file is empty or missing for message {message_id}: {downloaded_path}"
                        )
                        async with self._progress_lock:
                            self._current_progress.failed_messages += 1
                else:
                    logger.warning(
                        f"download_media returned None for message {message_id}"
                    )
                break  # Success, exit retry loop

            except FloodWaitError as e:
                retry_count += 1
                logger.warning(
                    f"Rate limit hit while downloading media for message {message_id}. "
                    f"Telegram requires waiting {e.seconds} seconds. "
                    f"(Retry {retry_count}/{max_retries})"
                )
                if retry_count < max_retries:
                    # Wait as required by Telegram
                    await asyncio.sleep(e.seconds)
                else:
                    logger.error(
                        f"Max retries reached for message {message_id} after rate limiting"
                    )
                    async with self._progress_lock:
                        self._current_progress.failed_messages += 1
                    break

            except Exception as e:
                logger.error(f"Failed to download media for message {message_id}: {e}")
                async with self._progress_lock:
                    self._current_progress.failed_messages += 1
                break

        # Call progress callback
        await self._call_progress_callback(progress_callback, self._current_progress)

    async def _extract_message_metadata_with_retry(
        self,
        raw_message,
        output_dir: Path,
        config: ExportConfig,
        messages_dict: dict[int, dict],
    ) -> Optional[tuple]:
        """
        Extract metadata with retry logic for transient failures.

        Args:
            raw_message: Raw message object from Telethon
            output_dir: Output directory Path
            config: Export configuration
            messages_dict: Dictionary to store message metadata

        Returns:
            Tuple if message has media to download, None otherwise
        """
        message_id = raw_message.id

        for attempt in range(MAX_METADATA_RETRIES):
            try:
                return await self._extract_message_metadata(
                    raw_message, output_dir, config, messages_dict
                )
            except Exception as e:
                if attempt == MAX_METADATA_RETRIES - 1:
                    # Final attempt failed
                    logger.error(
                        f"Failed to extract metadata for message {message_id} "
                        f"after {MAX_METADATA_RETRIES} attempts: {e}",
                        exc_info=True,
                    )
                    async with self._progress_lock:
                        self._current_progress.failed_messages += 1
                    return None
                else:
                    # Retry with exponential backoff
                    logger.warning(
                        f"Metadata extraction failed for message {message_id} "
                        f"(attempt {attempt + 1}/{MAX_METADATA_RETRIES}): {e}"
                    )
                    await asyncio.sleep(RETRY_BACKOFF_BASE * (attempt + 1))

    async def _extract_message_metadata(
        self,
        raw_message,
        output_dir: Path,
        config: ExportConfig,
        messages_dict: dict[int, dict],
    ) -> Optional[tuple]:
        """
        Extract metadata from a deleted message (fast, no media download).

        Args:
            raw_message: Raw message object from Telethon
            output_dir: Output directory Path
            config: Export configuration
            messages_dict: Dictionary to store message metadata (message_id -> data)

        Returns:
            Tuple (raw_message, deleted_msg, output_dir, messages_dict) if message has media to download, None otherwise
        """
        message_id = raw_message.id
        has_media = raw_message.media is not None
        has_text = bool(raw_message.message)

        # Check export mode
        should_export = (
            config.export_mode == "all"
            or (config.export_mode == "media_only" and has_media)
            or (config.export_mode == "text_only" and has_text and not has_media)
        )

        if not should_export:
            return None

        try:
            # Extract message data (metadata only, no media download)
            logger.debug(f"Extracting metadata for message {message_id}")
            deleted_msg = await self._extract_message_data(raw_message, config.chat_id)

            # Count text messages (thread-safe)
            if has_text:
                async with self._progress_lock:
                    self._current_progress.exported_text_messages += 1

            # Add to metadata dictionary (use Pydantic model_dump instead of to_dict)
            messages_dict[message_id] = deleted_msg.model_dump(mode="json")

            # Return info for media download if needed
            if has_media and config.export_mode in {"all", "media_only"}:
                return (raw_message, deleted_msg, output_dir, messages_dict)

            return None

        except Exception as e:
            # Re-raise to let retry wrapper handle it
            logger.debug(f"Error extracting metadata for message {message_id}: {e}")
            raise

    async def _extract_message_data(
        self, raw_message: Message, chat_id: int
    ) -> DeletedMessage:
        """
        Extract data from raw Telegram message.

        Args:
            raw_message: Message object from Telethon
            chat_id: Chat ID

        Returns:
            DeletedMessage object with extracted data
        """
        # Extract sender information
        sender_id = None
        sender_name = None
        sender_username = None

        if raw_message.from_id:
            # from_id is a Peer object (PeerUser, PeerChannel, or PeerChat)
            if isinstance(raw_message.from_id, PeerUser):
                sender_id = raw_message.from_id.user_id
                try:
                    # Use cached entity lookup to avoid redundant API calls
                    user = await self.telegram_service.get_entity_cached(sender_id)
                    if isinstance(user, User):
                        sender_name = " ".join(
                            filter(None, [user.first_name, user.last_name])
                        )
                        sender_username = user.username
                except Exception as e:
                    logger.debug(f"Could not fetch user info for {sender_id}: {e}")
            elif isinstance(raw_message.from_id, PeerChannel):
                sender_id = raw_message.from_id.channel_id
            elif isinstance(raw_message.from_id, PeerChat):
                sender_id = raw_message.from_id.chat_id

        # Extract reply information
        reply_to_msg_id = None
        reply_to_top_id = None
        quote_text = None

        if raw_message.reply_to:
            reply_to_msg_id = raw_message.reply_to.reply_to_msg_id
            reply_to_top_id = raw_message.reply_to.reply_to_top_id
            quote_text = raw_message.reply_to.quote_text

        # Determine media type
        media_type = type(raw_message.media).__name__ if raw_message.media else None

        return DeletedMessage(
            message_id=raw_message.id,
            chat_id=chat_id,
            sender_id=sender_id,
            sender_name=sender_name,
            sender_username=sender_username,
            text=raw_message.message,
            date=raw_message.date,
            has_media=raw_message.media is not None,
            media_type=media_type,
            reply_to_msg_id=reply_to_msg_id,
            reply_to_top_id=reply_to_top_id,
            quote_text=quote_text,
        )
