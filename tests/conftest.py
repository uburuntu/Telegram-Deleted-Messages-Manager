"""
Pytest configuration and fixtures.
"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from src.models.chat import ChatInfo
from src.models.config import ExportConfig, ResendConfig, TelegramConfig
from src.models.message import DeletedMessage


@pytest.fixture
def telegram_config():
    """Fixture for TelegramConfig."""
    return TelegramConfig(
        app_id=12345,
        app_hash="0123456789abcdef0123456789abcdef",
        session_name="test_session",
    )


@pytest.fixture
def export_config():
    """Fixture for ExportConfig."""
    return ExportConfig(
        chat_id=123456789,
        chat_title="Test Chat",
        output_directory="test_exports",
        export_mode="all",
        min_message_id=0,
        max_message_id=0,
        include_metadata=True,
    )


@pytest.fixture
def resend_config():
    """Fixture for ResendConfig."""
    return ResendConfig(
        target_chat_id=987654321,
        target_chat_title="Target Chat",
        source_directory="test_exports",
        include_media=True,
        include_text=True,
        add_original_info=True,
    )


@pytest.fixture
def sample_chat():
    """Fixture for ChatInfo."""
    return ChatInfo(
        chat_id=123456789,
        title="Test Chat",
        chat_type="group",
        username="testchat",
        participant_count=100,
        description="A test chat",
        last_message_date=datetime(2025, 1, 1, 12, 0, 0),
    )


@pytest.fixture
def sample_deleted_message():
    """Fixture for DeletedMessage."""
    return DeletedMessage(
        message_id=1001,
        chat_id=123456789,
        sender_id=111222333,
        sender_name="Test User",
        sender_username="testuser",
        text="This is a test message",
        date=datetime(2025, 1, 1, 12, 0, 0),
        has_media=False,
        media_type=None,
        media_file_path=None,
        reply_to_msg_id=None,
        reply_to_top_id=None,
        quote_text=None,
        raw_data={},
    )


@pytest.fixture
def mock_telegram_client():
    """Fixture for mocked Telegram client."""
    client = AsyncMock()
    client.connect = AsyncMock()
    client.start = AsyncMock()
    client.disconnect = AsyncMock()
    client.is_user_authorized = AsyncMock(return_value=True)
    client.get_dialogs = AsyncMock(return_value=[])
    client.get_entity = AsyncMock()
    client.iter_admin_log = AsyncMock()
    client.download_media = AsyncMock()
    client.send_file = AsyncMock()
    client.send_message = AsyncMock()
    client.send_code_request = AsyncMock()
    client.sign_in = AsyncMock()
    return client
