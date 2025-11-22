"""
Tests for TelegramService.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from telethon.tl.types import Channel, Chat, User

from src.models.chat import ChatInfo
from src.models.config import TelegramConfig
from src.services.telegram_service import TelegramService


@pytest.mark.asyncio
class TestTelegramService:
    """Tests for TelegramService class."""

    async def test_connect_success(self, telegram_config, mock_telegram_client):
        """Test successful connection."""
        service = TelegramService(telegram_config, client=mock_telegram_client)

        result = await service.connect()

        assert result is True
        assert service.is_connected is True
        mock_telegram_client.connect.assert_called_once()
        mock_telegram_client.is_user_authorized.assert_called_once()

    async def test_connect_invalid_config(self):
        """Test connection with invalid config."""
        invalid_config = TelegramConfig(app_id=None, app_hash=None)
        service = TelegramService(invalid_config)

        with pytest.raises(ValueError, match="Invalid Telegram configuration"):
            await service.connect()

    async def test_disconnect(self, telegram_config, mock_telegram_client):
        """Test disconnect."""
        service = TelegramService(telegram_config, client=mock_telegram_client)
        await service.connect()

        await service.disconnect()

        assert service.is_connected is False
        mock_telegram_client.disconnect.assert_called_once()

    async def test_get_recent_chats_not_connected(self, telegram_config):
        """Test getting chats when not connected."""
        service = TelegramService(telegram_config)

        with pytest.raises(RuntimeError, match="Not connected to Telegram"):
            await service.get_recent_chats()

    async def test_get_recent_chats_success(
        self, telegram_config, mock_telegram_client
    ):
        """Test getting recent chats successfully."""
        # Create mock dialog with mock channel
        mock_dialog = MagicMock()
        mock_channel = MagicMock(spec=Channel)
        mock_channel.id = 123456789
        mock_channel.title = "Test Channel"
        mock_channel.broadcast = True
        mock_channel.username = "testchannel"
        mock_dialog.entity = mock_channel
        mock_dialog.message = None

        mock_telegram_client.get_dialogs = AsyncMock(return_value=[mock_dialog])

        service = TelegramService(telegram_config, client=mock_telegram_client)
        await service.connect()

        chats = await service.get_recent_chats(limit=20)

        assert len(chats) == 1
        assert isinstance(chats[0], ChatInfo)
        assert chats[0].chat_id == 123456789
        assert chats[0].title == "Test Channel"
        assert chats[0].chat_type == "channel"
        mock_telegram_client.get_dialogs.assert_called_once_with(limit=20)

    async def test_search_chats_success(self, telegram_config, mock_telegram_client):
        """Test searching chats successfully."""
        # Create mock dialogs
        mock_dialog1 = MagicMock()
        mock_chat1 = MagicMock(spec=Chat)
        mock_chat1.id = 111
        mock_chat1.title = "Test Group"
        mock_dialog1.entity = mock_chat1
        mock_dialog1.message = None

        mock_dialog2 = MagicMock()
        mock_chat2 = MagicMock(spec=Chat)
        mock_chat2.id = 222
        mock_chat2.title = "Another Chat"
        mock_dialog2.entity = mock_chat2
        mock_dialog2.message = None

        mock_telegram_client.get_dialogs = AsyncMock(
            return_value=[mock_dialog1, mock_dialog2]
        )

        service = TelegramService(telegram_config, client=mock_telegram_client)
        await service.connect()

        chats = await service.search_chats("Test", limit=20)

        assert len(chats) == 1
        assert chats[0].title == "Test Group"

    async def test_get_chat_by_id_success(self, telegram_config, mock_telegram_client):
        """Test getting chat by ID successfully."""
        mock_user = MagicMock(spec=User)
        mock_user.id = 123
        mock_user.first_name = "John"
        mock_user.last_name = "Doe"
        mock_user.username = "johndoe"
        mock_telegram_client.get_entity = AsyncMock(return_value=mock_user)

        service = TelegramService(telegram_config, client=mock_telegram_client)
        await service.connect()

        chat = await service.get_chat_by_id(123)

        assert chat is not None
        assert isinstance(chat, ChatInfo)
        assert chat.chat_id == 123
        assert chat.title == "John Doe"
        assert chat.chat_type == "user"
        assert chat.username == "johndoe"

    async def test_create_chat_info_from_user(self, telegram_config):
        """Test creating ChatInfo from User entity."""
        service = TelegramService(telegram_config)
        user = MagicMock(spec=User)
        user.id = 123
        user.first_name = "John"
        user.last_name = "Doe"
        user.username = "johndoe"

        chat_info = service._create_chat_info(user)

        assert chat_info is not None
        assert chat_info.chat_id == 123
        assert chat_info.title == "John Doe"
        assert chat_info.chat_type == "user"
        assert chat_info.username == "johndoe"

    async def test_create_chat_info_from_channel(self, telegram_config):
        """Test creating ChatInfo from Channel entity."""
        service = TelegramService(telegram_config)
        channel = MagicMock(spec=Channel)
        channel.id = 456
        channel.title = "Test Channel"
        channel.broadcast = True
        channel.username = "testchannel"

        chat_info = service._create_chat_info(channel)

        assert chat_info is not None
        assert chat_info.chat_id == 456
        assert chat_info.title == "Test Channel"
        assert chat_info.chat_type == "channel"
        assert chat_info.username == "testchannel"
