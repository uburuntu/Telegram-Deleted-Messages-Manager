"""
Telegram API service for managing connections and chat operations.
"""

from typing import Awaitable, Callable, List, Optional, Protocol

from telethon import TelegramClient
from telethon.errors import RPCError, SessionPasswordNeededError
from telethon.tl.types import Channel, Chat, Dialog, User

from ..models.chat import ChatInfo
from ..models.config import TelegramConfig
from ..utils.paths import get_session_file_path


class TelegramClientProtocol(Protocol):
    """Protocol for Telegram client to enable testing."""

    async def start(self, phone: Optional[str] = None) -> None: ...
    async def disconnect(self) -> None: ...
    async def is_user_authorized(self) -> bool: ...
    async def get_dialogs(self, limit: int = 20) -> List[Dialog]: ...
    async def get_entity(self, entity_id: int): ...


class TelegramService:
    """Service for interacting with Telegram API."""

    def __init__(
        self, config: TelegramConfig, client: Optional[TelegramClientProtocol] = None
    ):
        """
        Initialize Telegram service.

        Args:
            config: Telegram configuration
            client: Optional client for testing (dependency injection)
        """
        self.config = config
        self._client: Optional[TelegramClientProtocol] = client
        self._is_connected = False
        self._phone_callback: Optional[Callable[[], Awaitable[str]]] = None
        self._code_callback: Optional[Callable[[], Awaitable[str]]] = None
        self._password_callback: Optional[Callable[[], Awaitable[str]]] = None
        self._entity_cache: dict = {}  # Cache for get_entity calls

    @property
    def client(self) -> Optional[TelegramClientProtocol]:
        """Get the Telegram client."""
        return self._client

    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._is_connected

    async def connect(
        self,
        phone_callback: Optional[Callable[[], Awaitable[str]]] = None,
        code_callback: Optional[Callable[[], Awaitable[str]]] = None,
        password_callback: Optional[Callable[[], Awaitable[str]]] = None,
    ) -> bool:
        """
        Connect to Telegram with custom authentication callbacks.

        Args:
            phone_callback: Async function to get phone number
            code_callback: Async function to get verification code
            password_callback: Async function to get 2FA password

        Returns:
            True if connection successful, False otherwise
        """
        if not self.config.is_valid():
            raise ValueError("Invalid Telegram configuration")

        # Store callbacks
        self._phone_callback = phone_callback
        self._code_callback = code_callback
        self._password_callback = password_callback

        try:
            if self._client is None:
                # Use proper session file path for standalone builds
                session_path = get_session_file_path(self.config.session_name)

                self._client = TelegramClient(
                    session_path,
                    self.config.app_id,
                    self.config.app_hash,
                )

            # Connect to Telegram
            await self._client.connect()

            # Check if already authorized
            if await self._client.is_user_authorized():
                self._is_connected = True
                return True

            # Need to authenticate - this will be handled separately
            return False

        except RPCError as e:
            raise ConnectionError(f"Failed to connect to Telegram: {e}")

    async def authenticate(
        self,
        phone: Optional[str] = None,
        code: Optional[str] = None,
        password: Optional[str] = None,
    ) -> dict:
        """
        Authenticate with Telegram.

        Args:
            phone: Phone number (for sending code)
            code: Verification code
            password: 2FA password

        Returns:
            Dictionary with authentication status and next step
        """
        if not self._client:
            raise RuntimeError("Client not connected. Call connect() first.")

        try:
            # Step 1: Send code
            if phone and not code:
                await self._client.send_code_request(phone)
                return {"status": "code_sent", "phone": phone}

            # Step 2: Sign in with code
            if phone and code and not password:
                try:
                    await self._client.sign_in(phone, code)
                    self._is_connected = True
                    return {"status": "success"}
                except SessionPasswordNeededError:
                    # 2FA is enabled
                    return {"status": "password_required", "phone": phone}

            # Step 3: Sign in with password
            if password:
                await self._client.sign_in(password=password)
                self._is_connected = True
                return {"status": "success"}

            return {"status": "error", "message": "Invalid authentication parameters"}

        except RPCError as e:
            return {"status": "error", "message": str(e)}

    async def disconnect(self) -> None:
        """Disconnect from Telegram."""
        if self._client:
            await self._client.disconnect()
            self._is_connected = False

    async def get_entity_cached(self, entity_id: int):
        """
        Get entity with caching to avoid redundant API calls.

        Args:
            entity_id: Entity ID to look up

        Returns:
            Entity object (User, Chat, or Channel)
        """
        if entity_id not in self._entity_cache:
            self._entity_cache[entity_id] = await self._client.get_entity(entity_id)
        return self._entity_cache[entity_id]

    async def get_recent_chats(self, limit: int = 20) -> List[ChatInfo]:
        """
        Get recent chats/dialogs.

        Args:
            limit: Maximum number of chats to retrieve

        Returns:
            List of ChatInfo objects
        """
        if not self._is_connected or not self._client:
            raise RuntimeError("Not connected to Telegram")

        try:
            dialogs = await self._client.get_dialogs(limit=limit)
            chat_list = []

            for dialog in dialogs:
                entity = dialog.entity
                chat_info = self._create_chat_info(entity, dialog)
                if chat_info:
                    chat_list.append(chat_info)

            return chat_list
        except RPCError as e:
            raise RuntimeError(f"Failed to retrieve chats: {e}")

    async def search_chats(self, query: str, limit: int = 20) -> List[ChatInfo]:
        """
        Search for chats by name.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching ChatInfo objects
        """
        if not self._is_connected or not self._client:
            raise RuntimeError("Not connected to Telegram")

        try:
            dialogs = await self._client.get_dialogs(limit=100)
            query_lower = query.lower()
            results = []

            for dialog in dialogs:
                entity = dialog.entity
                title = self._get_entity_title(entity)

                if title and query_lower in title.lower():
                    chat_info = self._create_chat_info(entity, dialog)
                    if chat_info:
                        results.append(chat_info)

                    if len(results) >= limit:
                        break

            return results
        except RPCError as e:
            raise RuntimeError(f"Failed to search chats: {e}")

    async def get_chat_by_id(self, chat_id: int) -> Optional[ChatInfo]:
        """
        Get chat information by ID.

        Args:
            chat_id: Chat ID

        Returns:
            ChatInfo object or None if not found
        """
        if not self._is_connected or not self._client:
            raise RuntimeError("Not connected to Telegram")

        try:
            entity = await self._client.get_entity(chat_id)
            return self._create_chat_info(entity)
        except RPCError as e:
            raise RuntimeError(f"Failed to get chat {chat_id}: {e}")

    def _create_chat_info(
        self, entity, dialog: Optional[Dialog] = None
    ) -> Optional[ChatInfo]:
        """
        Create ChatInfo from Telegram entity.

        Args:
            entity: Telegram entity (User, Chat, or Channel)
            dialog: Optional dialog for additional info

        Returns:
            ChatInfo object or None
        """
        chat_id = None
        title = None
        chat_type = None
        username = None
        participant_count = None
        description = None
        last_message_date = None

        if isinstance(entity, User):
            chat_id = entity.id
            title = (
                " ".join(filter(None, [entity.first_name, entity.last_name])) or "User"
            )
            chat_type = "user"
            username = entity.username
        elif isinstance(entity, Chat):
            chat_id = entity.id
            title = entity.title
            chat_type = "group"
            participant_count = getattr(entity, "participants_count", None)
        elif isinstance(entity, Channel):
            chat_id = entity.id
            title = entity.title
            chat_type = "channel" if entity.broadcast else "supergroup"
            username = entity.username
            participant_count = getattr(entity, "participants_count", None)
        else:
            return None

        if dialog:
            last_message_date = getattr(dialog.message, "date", None)

        return ChatInfo(
            chat_id=chat_id,
            title=title,
            chat_type=chat_type,
            username=username,
            participant_count=participant_count,
            description=description,
            last_message_date=last_message_date,
        )

    def _get_entity_title(self, entity) -> Optional[str]:
        """
        Get title/name from entity.

        Args:
            entity: Telegram entity

        Returns:
            Title string or None
        """
        if isinstance(entity, User):
            return " ".join(filter(None, [entity.first_name, entity.last_name])) or None
        elif isinstance(entity, (Chat, Channel)):
            return entity.title
        return None

    async def can_export_from_chat(self, chat_id: int) -> bool:
        """
        Check if user can export deleted messages from a chat.
        Admin logs are only available for channels/supergroups where user has admin rights.

        Args:
            chat_id: Chat ID to check

        Returns:
            True if user can access admin logs, False otherwise
        """
        if not self._is_connected or not self._client:
            return False

        try:
            entity = await self._client.get_entity(chat_id)

            # Admin logs only work for channels and supergroups
            if not isinstance(entity, Channel):
                return False

            # Best way to check: actually try to access the admin log with limit=1
            # This is more reliable than checking permissions, as permission flags
            # can be inconsistent or missing
            try:
                # Try to get one admin log entry
                async for _ in self._client.iter_admin_log(entity, limit=1):
                    # If we get here, we have access
                    return True
                # If no entries but no error, we still have access (just empty log)
                return True
            except Exception:
                # If we get an error trying to access the log, we don't have permission
                return False

        except Exception:
            # If we can't even get the entity, return False
            return False

    async def can_send_to_chat(self, chat_id: int) -> bool:
        """
        Check if user can send messages to a chat.

        Args:
            chat_id: Chat ID to check

        Returns:
            True if user can send messages, False otherwise
        """
        if not self._is_connected or not self._client:
            return False

        try:
            entity = await self._client.get_entity(chat_id)

            # Get user's permissions
            permissions = await self._client.get_permissions(entity)

            # Check if user can send messages based on entity type
            if isinstance(entity, User):
                # Can always send to users (private chats)
                return True

            elif isinstance(entity, Chat):
                # For regular groups, check if user is still a member
                # send_messages defaults to True for members
                if getattr(permissions, "has_left", False):
                    return False
                return getattr(permissions, "send_messages", True)

            elif isinstance(entity, Channel):
                # For channels/supergroups, check permissions
                if entity.broadcast:
                    # It's a broadcast channel - need post_messages right
                    return getattr(permissions, "post_messages", False)
                else:
                    # It's a supergroup - regular members can usually send
                    # Check if user is banned/restricted first
                    if getattr(permissions, "send_messages", None) is False:
                        return False
                    # If send_messages is True or None (default allowed), they can send
                    return getattr(permissions, "send_messages", True)

            return False

        except Exception:
            # If we can't check permissions, assume False for safety
            return False
