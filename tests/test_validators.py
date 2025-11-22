"""
Tests for validators module.
"""

from src.utils.validators import (
    validate_api_hash,
    validate_api_id,
    validate_chat_id,
    validate_directory_path,
    validate_message_id,
    validate_search_query,
)


class TestValidateApiId:
    """Tests for validate_api_id function."""

    def test_valid_api_id(self):
        """Test with valid API ID."""
        is_valid, error, value = validate_api_id("12345")
        assert is_valid is True
        assert error is None
        assert value == 12345

    def test_empty_api_id(self):
        """Test with empty API ID."""
        is_valid, error, value = validate_api_id("")
        assert is_valid is False
        assert "cannot be empty" in error
        assert value is None

    def test_non_numeric_api_id(self):
        """Test with non-numeric API ID."""
        is_valid, error, value = validate_api_id("abc123")
        assert is_valid is False
        assert "digits" in error
        assert value is None

    def test_negative_api_id(self):
        """Test with negative API ID."""
        is_valid, error, value = validate_api_id("-123")
        assert is_valid is False
        assert value is None

    def test_zero_api_id(self):
        """Test with zero API ID."""
        is_valid, error, value = validate_api_id("0")
        assert is_valid is False
        assert "positive" in error
        assert value is None


class TestValidateApiHash:
    """Tests for validate_api_hash function."""

    def test_valid_api_hash(self):
        """Test with valid API hash."""
        is_valid, error = validate_api_hash("0123456789abcdef0123456789abcdef")
        assert is_valid is True
        assert error is None

    def test_empty_api_hash(self):
        """Test with empty API hash."""
        is_valid, error = validate_api_hash("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_short_api_hash(self):
        """Test with short API hash."""
        is_valid, error = validate_api_hash("0123456789abcdef")
        assert is_valid is False
        assert "32 characters" in error

    def test_long_api_hash(self):
        """Test with long API hash."""
        is_valid, error = validate_api_hash("0123456789abcdef0123456789abcdef00")
        assert is_valid is False
        assert "32 characters" in error

    def test_invalid_characters_api_hash(self):
        """Test with invalid characters in API hash."""
        is_valid, error = validate_api_hash("0123456789abcdefghij0123456789ab")
        assert is_valid is False
        assert "hexadecimal" in error


class TestValidateChatId:
    """Tests for validate_chat_id function."""

    def test_valid_positive_chat_id(self):
        """Test with valid positive chat ID."""
        is_valid, error, value = validate_chat_id("123456789")
        assert is_valid is True
        assert error is None
        assert value == 123456789

    def test_valid_negative_chat_id(self):
        """Test with valid negative chat ID."""
        is_valid, error, value = validate_chat_id("-123456789")
        assert is_valid is True
        assert error is None
        assert value == -123456789

    def test_empty_chat_id(self):
        """Test with empty chat ID."""
        is_valid, error, value = validate_chat_id("")
        assert is_valid is False
        assert "cannot be empty" in error
        assert value is None

    def test_non_numeric_chat_id(self):
        """Test with non-numeric chat ID."""
        is_valid, error, value = validate_chat_id("abc")
        assert is_valid is False
        assert "number" in error
        assert value is None

    def test_zero_chat_id(self):
        """Test with zero chat ID."""
        is_valid, error, value = validate_chat_id("0")
        assert is_valid is False
        assert "cannot be zero" in error
        assert value is None


class TestValidateMessageId:
    """Tests for validate_message_id function."""

    def test_valid_message_id(self):
        """Test with valid message ID."""
        is_valid, error, value = validate_message_id("123", allow_zero=False)
        assert is_valid is True
        assert error is None
        assert value == 123

    def test_zero_message_id_allowed(self):
        """Test with zero when allowed."""
        is_valid, error, value = validate_message_id("0", allow_zero=True)
        assert is_valid is True
        assert error is None
        assert value == 0

    def test_zero_message_id_not_allowed(self):
        """Test with zero when not allowed."""
        is_valid, error, value = validate_message_id("0", allow_zero=False)
        assert is_valid is False
        assert "cannot be zero" in error
        assert value is None

    def test_empty_message_id_allowed(self):
        """Test with empty when zero is allowed."""
        is_valid, error, value = validate_message_id("", allow_zero=True)
        assert is_valid is True
        assert error is None
        assert value == 0

    def test_negative_message_id(self):
        """Test with negative message ID."""
        is_valid, error, value = validate_message_id("-123", allow_zero=True)
        assert is_valid is False
        assert "positive number" in error or "cannot be negative" in error
        assert value is None


class TestValidateDirectoryPath:
    """Tests for validate_directory_path function."""

    def test_valid_directory_path(self):
        """Test with valid directory path."""
        is_valid, error = validate_directory_path("exports/messages")
        assert is_valid is True
        assert error is None

    def test_empty_directory_path(self):
        """Test with empty directory path."""
        is_valid, error = validate_directory_path("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_invalid_characters_in_path(self):
        """Test with invalid characters in path."""
        is_valid, error = validate_directory_path("exports/messages<test>")
        assert is_valid is False
        assert "cannot contain" in error


class TestValidateSearchQuery:
    """Tests for validate_search_query function."""

    def test_valid_search_query(self):
        """Test with valid search query."""
        is_valid, error = validate_search_query("Test Chat")
        assert is_valid is True
        assert error is None

    def test_empty_search_query(self):
        """Test with empty search query."""
        is_valid, error = validate_search_query("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_short_search_query(self):
        """Test with short search query."""
        is_valid, error = validate_search_query("a")
        assert is_valid is False
        assert "at least 2 characters" in error

    def test_long_search_query(self):
        """Test with very long search query."""
        long_query = "a" * 101
        is_valid, error = validate_search_query(long_query)
        assert is_valid is False
        assert "too long" in error
