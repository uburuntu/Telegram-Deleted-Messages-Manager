"""
Configuration screen for API credentials setup.
"""

from typing import Awaitable, Callable

import flet as ft

from ...models.config import TelegramConfig
from ...utils.validators import validate_api_hash, validate_api_id


class ConfigScreen(ft.Column):
    """Screen for setting up Telegram API credentials."""

    def __init__(
        self,
        config: TelegramConfig,
        on_save: Callable[[TelegramConfig], Awaitable[None]],
    ):
        """
        Initialize config screen.

        Args:
            config: Current TelegramConfig
            on_save: Callback when configuration is saved
        """
        super().__init__()
        self.config = config
        self.on_save_callback = on_save

        # UI Controls
        self.api_id_field = ft.TextField(
            label="API ID",
            hint_text="Enter your API ID (numbers only)",
            value=str(config.app_id) if config.app_id else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            autofocus=True,
            expand=True,
        )

        self.api_hash_field = ft.TextField(
            label="API Hash",
            hint_text="Enter your API Hash (32 hex characters)",
            value=config.app_hash or "",
            max_length=32,
            expand=True,
        )

        self.session_name_field = ft.TextField(
            label="Session Name",
            hint_text="Enter a session name",
            value=config.session_name,
            expand=True,
        )

        self.error_text = ft.Text(
            "",
            color=ft.Colors.RED_400,
            visible=False,
        )

        self.success_text = ft.Text(
            "",
            color=ft.Colors.GREEN_400,
            visible=False,
        )

        # Build UI
        self._build_ui()

    def _build_ui(self):
        """Build the UI layout."""
        # Header
        header = ft.Column(
            [
                ft.Text(
                    "Telegram API Configuration",
                    size=26,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "Set up your Telegram API credentials to get started",
                    size=13,
                    color=ft.Colors.GREY_700,
                ),
                ft.Divider(height=15),
            ],
            spacing=8,
        )

        # Info card with instructions
        info_card = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.BLUE_400),
                            ft.Text(
                                "How to get your API credentials:",
                                weight=ft.FontWeight.BOLD,
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Text(
                        "1. Go to https://my.telegram.org/auth",
                        size=13,
                    ),
                    ft.Text(
                        "2. Log in with your phone number",
                        size=13,
                    ),
                    ft.Text(
                        "3. Navigate to 'API development tools'",
                        size=13,
                    ),
                    ft.Text(
                        "4. Create an app and copy your API ID and API Hash",
                        size=13,
                    ),
                    ft.Container(
                        content=ft.TextButton(
                            "Open Telegram API Page",
                            icon=ft.Icons.OPEN_IN_NEW,
                            on_click=lambda _: self.page.launch_url(
                                "https://my.telegram.org/auth"
                            ),
                        ),
                        alignment=ft.alignment.center_left,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=ft.Colors.BLUE_50,
            border=ft.border.all(1, ft.Colors.BLUE_200),
            border_radius=8,
            padding=15,
        )

        # Form fields
        form = ft.Column(
            [
                self.api_id_field,
                self.api_hash_field,
                self.session_name_field,
            ],
            spacing=15,
        )

        # Messages
        messages = ft.Column(
            [self.error_text, self.success_text],
            spacing=5,
        )

        # Buttons
        save_button = ft.ElevatedButton(
            "Save and Continue",
            icon=ft.Icons.SAVE,
            on_click=self._on_save_clicked,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE_700,
            ),
        )

        # Main layout
        self.controls = [
            header,
            info_card,
            ft.Container(height=15),
            form,
            messages,
            ft.Container(height=5),
            save_button,
        ]
        self.spacing = 0
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO

    async def _on_save_clicked(self, e):
        """Handle save button click."""
        # Validate API ID
        is_valid_id, id_error, parsed_id = validate_api_id(self.api_id_field.value)
        if not is_valid_id:
            self._show_error(f"API ID Error: {id_error}")
            self.api_id_field.error_text = id_error
            self.update()
            return

        # Validate API Hash
        is_valid_hash, hash_error = validate_api_hash(self.api_hash_field.value)
        if not is_valid_hash:
            self._show_error(f"API Hash Error: {hash_error}")
            self.api_hash_field.error_text = hash_error
            self.update()
            return

        # Clear errors
        self.api_id_field.error_text = None
        self.api_hash_field.error_text = None

        # Update config
        self.config.app_id = parsed_id
        self.config.app_hash = self.api_hash_field.value.strip()
        self.config.session_name = (
            self.session_name_field.value.strip() or "telegram_session"
        )

        # Show success message
        self._show_success("Configuration saved successfully!")
        self.update()

        # Call the callback
        if self.on_save_callback:
            await self.on_save_callback(self.config)

    def _show_error(self, message: str):
        """Show error message."""
        self.error_text.value = message
        self.error_text.visible = True
        self.success_text.visible = False

    def _show_success(self, message: str):
        """Show success message."""
        self.success_text.value = message
        self.success_text.visible = True
        self.error_text.visible = False
