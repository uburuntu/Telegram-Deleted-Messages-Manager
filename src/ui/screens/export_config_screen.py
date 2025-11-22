"""
Export configuration screen.
"""

from typing import Awaitable, Callable

import flet as ft

from ...models.chat import ChatInfo
from ...models.config import ExportConfig


class ExportConfigScreen(ft.Column):
    """Screen for configuring export options."""

    def __init__(
        self,
        chat: ChatInfo,
        config: ExportConfig,
        on_start_export: Callable[[ExportConfig], Awaitable[None]],
        on_back: Callable[[], Awaitable[None]],
    ):
        """
        Initialize export config screen.

        Args:
            chat: Selected ChatInfo
            config: Export configuration
            on_start_export: Callback to start export
            on_back: Callback to go back
        """
        super().__init__()
        self.chat = chat
        self.config = config
        self.on_start_export_callback = on_start_export
        self.on_back_callback = on_back

        # Set chat info in config
        self.config.chat_id = chat.chat_id
        self.config.chat_title = chat.title

        # UI Controls
        self.output_dir_field = ft.TextField(
            label="Output Directory",
            hint_text="Where to save exported messages",
            value=config.output_directory,
            expand=True,
        )

        self.export_mode_dropdown = ft.Dropdown(
            label="Export Mode",
            hint_text="What to export",
            value=config.export_mode,
            options=[
                ft.dropdown.Option("all", "All (Text + Media)"),
                ft.dropdown.Option("media_only", "Media Only"),
                ft.dropdown.Option("text_only", "Text Only"),
            ],
            expand=True,
        )

        self.min_id_field = ft.TextField(
            label="Minimum Message ID (optional)",
            hint_text="Start from message ID (0 for beginning)",
            value=str(config.min_message_id),
            keyboard_type=ft.KeyboardType.NUMBER,
            expand=True,
        )

        self.max_id_field = ft.TextField(
            label="Maximum Message ID (optional)",
            hint_text="End at message ID (0 for all)",
            value=str(config.max_message_id),
            keyboard_type=ft.KeyboardType.NUMBER,
            expand=True,
        )

        self.error_text = ft.Text(
            "",
            color=ft.Colors.RED_400,
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
                    "Export Configuration",
                    size=26,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    f"Configure export options for: {self.chat.title}",
                    size=13,
                    color=ft.Colors.GREY_700,
                ),
                ft.Divider(height=15),
            ],
            spacing=8,
        )

        # Selected chat info
        chat_info = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.BLUE_400),
                    ft.Column(
                        [
                            ft.Text(
                                f"Chat: {self.chat.title}",
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                f"Type: {self.chat.chat_type_display}  •  ID: {self.chat.chat_id}",
                                size=12,
                                color=ft.Colors.GREY_600,
                            ),
                        ],
                        spacing=5,
                    ),
                ],
                spacing=15,
            ),
            bgcolor=ft.Colors.BLUE_50,
            border=ft.border.all(1, ft.Colors.BLUE_200),
            border_radius=8,
            padding=15,
        )

        # Form fields
        form = ft.Column(
            [
                ft.Text("Export Settings:", size=16, weight=ft.FontWeight.BOLD),
                self.output_dir_field,
                self.export_mode_dropdown,
                ft.Row(
                    [self.min_id_field, self.max_id_field],
                    spacing=10,
                ),
            ],
            spacing=15,
        )

        # Info note
        info_note = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Note:",
                        weight=ft.FontWeight.BOLD,
                        size=12,
                    ),
                    ft.Text(
                        "• This will export DELETED messages from the admin log",
                        size=12,
                    ),
                    ft.Text(
                        "• You need admin permissions to access deleted messages",
                        size=12,
                    ),
                    ft.Text(
                        "• Export may take time depending on the number of messages",
                        size=12,
                    ),
                ],
                spacing=5,
            ),
            bgcolor=ft.Colors.ORANGE_50,
            border=ft.border.all(1, ft.Colors.ORANGE_200),
            border_radius=8,
            padding=15,
        )

        # Buttons
        buttons = ft.Row(
            [
                ft.TextButton(
                    "Back",
                    icon=ft.Icons.ARROW_BACK,
                    on_click=self._on_back_clicked,
                ),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Start Export",
                    icon=ft.Icons.DOWNLOAD,
                    on_click=self._on_start_export_clicked,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.GREEN_700,
                    ),
                ),
            ],
            spacing=10,
        )

        # Main layout
        self.controls = [
            header,
            chat_info,
            ft.Container(height=8),
            form,
            ft.Container(height=8),
            info_note,
            self.error_text,
            ft.Container(height=5),
            buttons,
        ]
        self.spacing = 0
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO

    async def _on_start_export_clicked(self, e):
        """Handle start export button click."""
        # Validate and update config
        try:
            self.config.output_directory = self.output_dir_field.value.strip()
            self.config.export_mode = self.export_mode_dropdown.value
            self.config.min_message_id = int(self.min_id_field.value or "0")
            self.config.max_message_id = int(self.max_id_field.value or "0")

            # Validate
            if not self.config.output_directory:
                self._show_error("Output directory is required")
                return

            if self.config.min_message_id < 0:
                self._show_error("Minimum message ID cannot be negative")
                return

            if self.config.max_message_id < 0:
                self._show_error("Maximum message ID cannot be negative")
                return

            # Call callback
            if self.on_start_export_callback:
                await self.on_start_export_callback(self.config)

        except ValueError as ve:
            self._show_error(f"Invalid input: {str(ve)}")
            self.update()

    async def _on_back_clicked(self, e):
        """Handle back button click."""
        if self.on_back_callback:
            await self.on_back_callback()

    def _show_error(self, message: str):
        """Show error message."""
        self.error_text.value = message
        self.error_text.visible = True
        self.update()
