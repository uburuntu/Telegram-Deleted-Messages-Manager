"""
Service for re-sending exported messages to Telegram.
"""

import asyncio
import html
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Awaitable, Callable, List, Optional

from telethon.errors import FloodWaitError, RPCError

from ..models.config import ResendConfig
from ..models.message import DeletedMessage, ExportProgress
from ..utils.logger import get_logger
from .telegram_service import TelegramService

logger = get_logger(__name__)

ProgressCallback = Callable[[ExportProgress], Awaitable[None]]

# Constants
TELEGRAM_FILE_SIZE_LIMIT = 2_000_000_000  # 2GB
TELEGRAM_CAPTION_LIMIT = 1024
MESSAGE_SEND_DELAY = 2  # seconds between messages
MAX_SEND_RETRIES = 3  # Maximum retries for sending messages/media


def safe_truncate_utf8(text: str, max_length: int) -> str:
    """
    Safely truncate text without breaking UTF-8 multibyte characters.

    Args:
        text: Text to truncate
        max_length: Maximum length in characters

    Returns:
        Truncated text with "..." suffix if truncated
    """
    if len(text) <= max_length:
        return text

    # Reserve 3 characters for "..."
    truncate_at = max_length - 3
    truncated = text[:truncate_at]

    # Verify UTF-8 encoding is valid at this boundary
    try:
        truncated.encode("utf-8")
        return truncated + "..."
    except UnicodeEncodeError:
        # If broken, try one character less recursively
        return safe_truncate_utf8(text, max_length - 1)


class ResendService:
    """Service for re-sending deleted messages to Telegram."""

    def __init__(self, telegram_service: TelegramService):
        """
        Initialize resend service.

        Args:
            telegram_service: TelegramService instance
        """
        self.telegram_service = telegram_service
        self._current_progress: Optional[ExportProgress] = None
        self._should_cancel = False

    @property
    def current_progress(self) -> Optional[ExportProgress]:
        """Get current resend progress."""
        return self._current_progress

    def cancel(self):
        """Cancel the current resend operation."""
        logger.info("Resend cancellation requested")
        self._should_cancel = True

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

    async def resend_messages(
        self,
        config: ResendConfig,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> ExportProgress:
        """
        Re-send exported messages to a chat.

        Args:
            config: Resend configuration
            progress_callback: Optional callback for progress updates

        Returns:
            ExportProgress with final statistics
        """
        if not self.telegram_service.is_connected:
            raise RuntimeError("Telegram service is not connected")

        if not config.target_chat_id:
            raise ValueError("Target chat ID is required for resend")

        # Reset cancellation flag
        self._should_cancel = False

        # Initialize progress tracking with start time
        self._current_progress = ExportProgress(start_time=datetime.now(timezone.utc))

        # Load messages from metadata file
        source_dir = Path(config.source_directory)
        metadata_file = source_dir / "messages_metadata.json"

        if not metadata_file.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_file}")

        try:
            # Load and parse messages
            messages_data = json.loads(metadata_file.read_text(encoding="utf-8"))

            # Convert to DeletedMessage objects and sort by date
            messages = [DeletedMessage(**msg_data) for msg_data in messages_data]
            messages = sorted(messages, key=lambda m: m.date or datetime.min)

            self._current_progress.total_messages = len(messages)

            # Create batches (groups consecutive short messages if batching enabled)
            message_batches = self._create_message_batches(messages, config)
            logger.info(
                f"Created {len(message_batches)} batches from {len(messages)} messages"
            )

            # Get target chat entity
            target_entity = await self.telegram_service.client.get_entity(
                config.target_chat_id
            )

            # Process each batch
            for batch in message_batches:
                # Check for cancellation
                if self._should_cancel:
                    logger.info("Resend cancelled by user")
                    self._current_progress.error_message = "Cancelled by user"
                    self._current_progress.is_cancelled = True
                    self._current_progress.is_complete = True
                    await self._call_progress_callback(
                        progress_callback, self._current_progress
                    )
                    break

                # Process this batch (may be 1 message or multiple combined)
                await self._resend_message_batch(
                    batch, target_entity, config, progress_callback
                )

            # Mark as complete (if not cancelled)
            if not self._should_cancel:
                self._current_progress.is_complete = True

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

    async def _resend_single_message(
        self,
        message: DeletedMessage,
        target_entity,
        config: ResendConfig,
        progress_callback: Optional[ProgressCallback],
    ) -> None:
        """
        Resend a single message.

        Args:
            message: DeletedMessage to resend
            target_entity: Target Telegram entity
            config: Resend configuration
            progress_callback: Optional progress callback
        """
        self._current_progress.processed_messages += 1
        self._current_progress.current_message_id = message.message_id

        try:
            # Build message content
            message_text = await self._build_message_text(message, config)

            # Check if we should send this message
            if not config.include_text and not message.has_media:
                return
            if not config.include_media and message.has_media and not message.has_text:
                return

            sent_media = False

            # Send media if present and configured
            if message.has_media and config.include_media and message.media_file_path:
                # Use the media_file_path from metadata directly
                # The path is relative to the current working directory
                media_file = Path(message.media_file_path)

                # Validate file exists and is readable
                if not media_file.exists():
                    logger.warning(
                        f"Media file not found for message {message.message_id}: {media_file}"
                    )
                else:
                    # Check file size (Telegram limits: 2GB for most files)
                    file_size = media_file.stat().st_size

                    if file_size > TELEGRAM_FILE_SIZE_LIMIT:
                        logger.warning(
                            f"File too large ({file_size / 1_000_000:.1f}MB) for message {message.message_id}: {media_file}"
                        )
                    else:
                        # Retry logic for sending media
                        retry_count = 0
                        while retry_count < MAX_SEND_RETRIES:
                            try:
                                # Prepare caption with length validation
                                caption = None
                                if config.include_text and message_text:
                                    # Telegram caption limit
                                    caption = safe_truncate_utf8(
                                        message_text, TELEGRAM_CAPTION_LIMIT
                                    )

                                # Send file (Telethon automatically detects media type from file extension)
                                logger.debug(
                                    f"Sending media file ({file_size / 1_000:.1f}KB): {media_file.name}"
                                )
                                await self.telegram_service.client.send_file(
                                    entity=target_entity,
                                    file=str(media_file),
                                    caption=caption,
                                    silent=True,
                                    force_document=False,  # Let Telegram detect type automatically
                                )
                                sent_media = True
                                self._current_progress.exported_media_messages += 1
                                logger.debug(
                                    f"Successfully sent media: {media_file.name}"
                                )
                                break  # Success, exit retry loop

                            except FloodWaitError as e:
                                retry_count += 1
                                logger.warning(
                                    f"Rate limit hit while sending media for message {message.message_id}. "
                                    f"Telegram requires waiting {e.seconds} seconds. "
                                    f"(Retry {retry_count}/{MAX_SEND_RETRIES})"
                                )
                                if retry_count < MAX_SEND_RETRIES:
                                    await asyncio.sleep(e.seconds)
                                else:
                                    logger.error(
                                        f"Max retries reached for message {message.message_id} after rate limiting"
                                    )
                                    self._current_progress.failed_messages += 1
                                    break

                            except Exception as e:
                                logger.error(
                                    f"Failed to send media {media_file.name} for message {message.message_id}: {e}"
                                )
                                self._current_progress.failed_messages += 1
                                break

            # Send text message if media wasn't sent and we have text
            if not sent_media and config.include_text and message_text:
                retry_count = 0
                while retry_count < MAX_SEND_RETRIES:
                    try:
                        await self.telegram_service.client.send_message(
                            entity=target_entity,
                            message=message_text,
                            silent=True,
                            parse_mode="html",
                        )
                        self._current_progress.exported_text_messages += 1
                        break  # Success, exit retry loop

                    except FloodWaitError as e:
                        retry_count += 1
                        logger.warning(
                            f"Rate limit hit while sending text message for message {message.message_id}. "
                            f"Telegram requires waiting {e.seconds} seconds. "
                            f"(Retry {retry_count}/{MAX_SEND_RETRIES})"
                        )
                        if retry_count < MAX_SEND_RETRIES:
                            await asyncio.sleep(e.seconds)
                        else:
                            logger.error(
                                f"Max retries reached for message {message.message_id} after rate limiting"
                            )
                            self._current_progress.failed_messages += 1
                            break

                    except Exception as e:
                        logger.error(f"Failed to send text message: {e}")
                        self._current_progress.failed_messages += 1
                        break

            # Call progress callback
            await self._call_progress_callback(
                progress_callback, self._current_progress
            )

        except Exception as e:
            logger.error(f"Error resending message {message.message_id}: {e}")
            self._current_progress.failed_messages += 1

    async def _build_message_text(
        self, message: DeletedMessage, config: ResendConfig
    ) -> str:
        """
        Build message text with configurable header components.

        Args:
            message: DeletedMessage
            config: Resend configuration

        Returns:
            Formatted message text
        """
        text_parts = []

        # Build header with granular controls
        header_parts = []

        # Sender info (name and/or username)
        if config.show_sender_name or config.show_sender_username:
            sender_parts = []

            if config.show_sender_name and message.sender_name:
                sender_parts.append(message.sender_name)

            if config.show_sender_username and message.sender_username:
                username_part = f"@{message.sender_username}"
                if sender_parts:  # Already have name
                    sender_parts[0] = f"{sender_parts[0]} ({username_part})"
                else:  # Only username
                    sender_parts.append(username_part)

            if sender_parts:
                header_parts.append(sender_parts[0])

        # Reply link (hidden or visible)
        if config.show_reply_link and message.reply_to_msg_id and message.chat_id:
            if message.reply_to_top_id:
                reply_link = f"https://t.me/c/{message.chat_id}/{message.reply_to_top_id}/{message.reply_to_msg_id}"
            else:
                reply_link = f"https://t.me/c/{message.chat_id}/{message.reply_to_msg_id}"

            if config.use_hidden_reply_links:
                # HTML hidden link
                header_parts.append(f'<a href="{reply_link}">↩️ Reply</a>')
            else:
                header_parts.append(reply_link)

        # Date with timezone adjustment
        if config.show_date and message.date:
            formatted_date = message.get_formatted_date(config.timezone_offset_hours)
            header_parts.append(formatted_date)

        if header_parts:
            text_parts.append(" - ".join(header_parts))

        # Quote text
        if message.quote_text:
            escaped_quote = html.escape(message.quote_text)
            text_parts.append(f"<pre>❝ {escaped_quote} ❞</pre>")

        # Message text
        if message.text:
            text_parts.append(message.text)

        # Fallback
        if not text_parts and message.date:
            text_parts.append(message.get_formatted_date(config.timezone_offset_hours))

        return "\n\n".join(text_parts)

    def _create_message_batches(
        self, messages: List[DeletedMessage], config: ResendConfig
    ) -> List[List[DeletedMessage]]:
        """
        Group consecutive short text messages into batches.

        Strategy:
        - Only batch text-only messages (no media)
        - Same sender only
        - Within time window
        - Short messages only
        - Don't batch replies (preserve context)
        - Keep total under 4000 chars (safe margin)

        Returns:
            List of message batches (each batch is a list of messages)
        """
        if not config.enable_batching:
            # Return each message as its own batch
            return [[msg] for msg in messages]

        batches = []
        current_batch = []

        for message in messages:
            # Check if message is batchable
            can_batch = (
                not message.has_media
                and message.has_text
                and not message.reply_to_msg_id  # Don't batch replies
                and message.text
                and len(message.text) <= config.batch_max_message_length
            )

            if not can_batch:
                # Flush current batch and add this message separately
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                batches.append([message])
                continue

            # Check if we can add to current batch
            can_add_to_batch = False

            if current_batch:
                first_msg = current_batch[0]
                last_msg = current_batch[-1]

                # Check constraints
                same_sender = message.sender_id == first_msg.sender_id
                within_time = (
                    message.date
                    and last_msg.date
                    and (message.date - last_msg.date)
                    <= timedelta(minutes=config.batch_time_window_minutes)
                )
                not_full = len(current_batch) < config.batch_max_messages

                # Estimate total length if we add this message
                total_length = sum(len(msg.text or "") for msg in current_batch) + len(
                    message.text or ""
                )
                # Account for separators and header (rough estimate: 200 chars)
                estimated_total = total_length + (len(current_batch) * 2) + 200
                under_limit = estimated_total < 4000

                can_add_to_batch = (
                    same_sender and within_time and not_full and under_limit
                )

            if can_add_to_batch or not current_batch:
                current_batch.append(message)
            else:
                # Start new batch
                batches.append(current_batch)
                current_batch = [message]

        # Don't forget last batch
        if current_batch:
            batches.append(current_batch)

        return batches

    async def _build_batched_message_text(
        self, batch: List[DeletedMessage], config: ResendConfig
    ) -> str:
        """
        Build message text for a batch of messages.
        Uses header from first message, combines all texts with \\n\\n separator.

        Args:
            batch: List of messages to combine
            config: Resend configuration

        Returns:
            Formatted batched message text
        """
        if len(batch) == 1:
            return await self._build_message_text(batch[0], config)

        first_message = batch[0]
        text_parts = []

        # Build header from first message only
        header_parts = []

        # Sender info
        if config.show_sender_name or config.show_sender_username:
            sender_parts = []
            if config.show_sender_name and first_message.sender_name:
                sender_parts.append(first_message.sender_name)
            if config.show_sender_username and first_message.sender_username:
                username_part = f"@{first_message.sender_username}"
                if sender_parts:
                    sender_parts[0] = f"{sender_parts[0]} ({username_part})"
                else:
                    sender_parts.append(username_part)
            if sender_parts:
                header_parts.append(sender_parts[0])

        # Reply link from first message (shouldn't happen in batches, but handle it)
        if (
            config.show_reply_link
            and first_message.reply_to_msg_id
            and first_message.chat_id
        ):
            if first_message.reply_to_top_id:
                reply_link = f"https://t.me/c/{first_message.chat_id}/{first_message.reply_to_top_id}/{first_message.reply_to_msg_id}"
            else:
                reply_link = f"https://t.me/c/{first_message.chat_id}/{first_message.reply_to_msg_id}"

            if config.use_hidden_reply_links:
                header_parts.append(f'<a href="{reply_link}">↩️ Reply</a>')
            else:
                header_parts.append(reply_link)

        # Date from first message
        if config.show_date and first_message.date:
            formatted_date = first_message.get_formatted_date(
                config.timezone_offset_hours
            )
            header_parts.append(formatted_date)

        if header_parts:
            text_parts.append(" - ".join(header_parts))

        # Combine all message texts with \\n\\n separator
        message_texts = [msg.text for msg in batch if msg.text]
        combined_text = "\n\n".join(message_texts)

        if combined_text:
            text_parts.append(combined_text)

        return "\n\n".join(text_parts)

    async def _resend_message_batch(
        self,
        batch: List[DeletedMessage],
        target_entity,
        config: ResendConfig,
        progress_callback: Optional[ProgressCallback],
    ) -> None:
        """
        Resend a batch of messages (may be 1 message or multiple combined).

        Args:
            batch: List of messages in this batch
            target_entity: Target Telegram entity
            config: Resend configuration
            progress_callback: Optional progress callback
        """
        # For single-message batches, use existing single-message logic
        if len(batch) == 1:
            await self._resend_single_message(
                batch[0], target_entity, config, progress_callback
            )
            return

        # For multi-message batches, send as combined text
        # Update progress for all messages in batch
        for message in batch:
            self._current_progress.processed_messages += 1
            self._current_progress.current_message_id = message.message_id

        try:
            # Build combined message text
            message_text = await self._build_batched_message_text(batch, config)

            if not message_text:
                return

            # Send combined text message with retry logic
            retry_count = 0
            while retry_count < MAX_SEND_RETRIES:
                try:
                    await self.telegram_service.client.send_message(
                        entity=target_entity,
                        message=message_text,
                        silent=True,
                        parse_mode="html",
                    )
                    self._current_progress.exported_text_messages += len(batch)
                    logger.debug(f"Successfully sent batch of {len(batch)} messages")
                    break  # Success, exit retry loop

                except FloodWaitError as e:
                    retry_count += 1
                    logger.warning(
                        f"Rate limit hit while sending batch. "
                        f"Telegram requires waiting {e.seconds} seconds. "
                        f"(Retry {retry_count}/{MAX_SEND_RETRIES})"
                    )
                    if retry_count < MAX_SEND_RETRIES:
                        await asyncio.sleep(e.seconds)
                    else:
                        logger.error("Max retries reached for batch after rate limiting")
                        self._current_progress.failed_messages += len(batch)
                        break

                except Exception as e:
                    logger.error(f"Failed to send batched text message: {e}")
                    self._current_progress.failed_messages += len(batch)
                    break

            # Call progress callback
            await self._call_progress_callback(
                progress_callback, self._current_progress
            )

        except Exception as e:
            logger.error(f"Error resending batch: {e}")
            self._current_progress.failed_messages += len(batch)
