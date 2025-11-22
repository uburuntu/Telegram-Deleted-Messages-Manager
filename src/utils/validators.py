"""
Input validation utilities.
"""

import re
from typing import Optional, Tuple


def validate_api_id(api_id_str: str) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Validate Telegram API ID.

    Returns:
        Tuple of (is_valid, error_message, parsed_value)
    """
    if not api_id_str or not api_id_str.strip():
        return False, "API ID cannot be empty", None

    api_id_str = api_id_str.strip()

    if not api_id_str.isdigit():
        return False, "API ID must contain only digits", None

    try:
        api_id = int(api_id_str)
        if api_id <= 0:
            return False, "API ID must be a positive number", None
        return True, None, api_id
    except ValueError:
        return False, "Invalid API ID format", None


def validate_api_hash(api_hash: str) -> Tuple[bool, Optional[str]]:
    """
    Validate Telegram API Hash.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not api_hash or not api_hash.strip():
        return False, "API Hash cannot be empty"

    api_hash = api_hash.strip()

    # API hash should be 32 characters hexadecimal
    if len(api_hash) != 32:
        return False, "API Hash must be exactly 32 characters"

    if not re.match(r"^[a-fA-F0-9]{32}$", api_hash):
        return False, "API Hash must contain only hexadecimal characters (0-9, a-f)"

    return True, None


def validate_chat_id(chat_id_str: str) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Validate Telegram chat ID.

    Returns:
        Tuple of (is_valid, error_message, parsed_value)
    """
    if not chat_id_str or not chat_id_str.strip():
        return False, "Chat ID cannot be empty", None

    chat_id_str = chat_id_str.strip()

    # Remove leading minus if present (for negative IDs)
    if chat_id_str.startswith("-"):
        chat_id_str_check = chat_id_str[1:]
    else:
        chat_id_str_check = chat_id_str

    if not chat_id_str_check.isdigit():
        return False, "Chat ID must be a number", None

    try:
        chat_id = int(chat_id_str)
        if chat_id == 0:
            return False, "Chat ID cannot be zero", None
        return True, None, chat_id
    except ValueError:
        return False, "Invalid chat ID format", None


def validate_message_id(
    msg_id_str: str, allow_zero: bool = True
) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Validate message ID.

    Args:
        msg_id_str: Message ID as string
        allow_zero: Whether to allow 0 as valid value (for min/max ranges)

    Returns:
        Tuple of (is_valid, error_message, parsed_value)
    """
    if not msg_id_str or not msg_id_str.strip():
        if allow_zero:
            return True, None, 0
        return False, "Message ID cannot be empty", None

    msg_id_str = msg_id_str.strip()

    if not msg_id_str.isdigit():
        return False, "Message ID must be a positive number", None

    try:
        msg_id = int(msg_id_str)
        if msg_id < 0:
            return False, "Message ID cannot be negative", None
        if msg_id == 0 and not allow_zero:
            return False, "Message ID cannot be zero", None
        return True, None, msg_id
    except ValueError:
        return False, "Invalid message ID format", None


def validate_directory_path(path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate directory path.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path or not path.strip():
        return False, "Directory path cannot be empty"

    path = path.strip()

    # Check for invalid characters (basic validation)
    invalid_chars = ["<", ">", ":", '"', "|", "?", "*"]
    for char in invalid_chars:
        if char in path:
            return False, f"Directory path cannot contain '{char}'"

    # Check if path is absolute or relative (allow both)
    if len(path) < 1:
        return False, "Directory path is too short"

    return True, None


def validate_search_query(query: str) -> Tuple[bool, Optional[str]]:
    """
    Validate chat search query.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not query or not query.strip():
        return False, "Search query cannot be empty"

    query = query.strip()

    if len(query) < 2:
        return False, "Search query must be at least 2 characters"

    if len(query) > 100:
        return False, "Search query is too long (max 100 characters)"

    return True, None
