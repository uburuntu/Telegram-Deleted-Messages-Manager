"""
Resend configuration screen.
"""

from typing import Awaitable, Callable, List, Tuple

import flet as ft

from ...models.chat import ChatInfo
from ...models.config import ResendConfig
from ...services.storage_service import StorageService


class ResendConfigScreen(ft.Column):
    """Screen for configuring resend options."""

    def __init__(
        self,
        target_chat: ChatInfo,
        config: ResendConfig,
        storage_service: StorageService,
        on_start_resend: Callable[[ResendConfig], Awaitable[None]],
        on_back: Callable[[], Awaitable[None]],
    ):
        """
        Initialize resend config screen.

        Args:
            target_chat: Target ChatInfo
            config: Resend configuration
            storage_service: StorageService for detecting export folders
            on_start_resend: Callback to start resend
            on_back: Callback to go back
        """
        super().__init__()
        self.target_chat = target_chat
        self.config = config
        self.storage_service = storage_service
        self.on_start_resend_callback = on_start_resend
        self.on_back_callback = on_back

        # Set chat info in config
        self.config.target_chat_id = target_chat.chat_id
        self.config.target_chat_title = target_chat.title

        # Load available export directories
        self.export_folders = self._load_export_folders()

        # UI Controls
        self.source_dir_field = ft.TextField(
            label="Source Directory",
            hint_text="Directory containing exported messages",
            value=config.source_directory,
            expand=True,
        )

        self.export_folders_container = ft.Column(
            [],
            spacing=10,
        )

        self.include_media_checkbox = ft.Checkbox(
            label="Include media files",
            value=config.include_media,
        )

        self.include_text_checkbox = ft.Checkbox(
            label="Include text messages",
            value=config.include_text,
        )

        # Header component controls
        self.show_sender_name_checkbox = ft.Checkbox(
            label="Show sender name",
            value=config.show_sender_name,
        )

        self.show_username_checkbox = ft.Checkbox(
            label="Show username (@handle)",
            value=config.show_sender_username,
        )

        self.show_date_checkbox = ft.Checkbox(
            label="Show date/time",
            value=config.show_date,
        )

        self.show_reply_link_checkbox = ft.Checkbox(
            label="Show reply link",
            value=config.show_reply_link,
        )

        self.use_hidden_links_checkbox = ft.Checkbox(
            label="Use hidden reply links (↩️ Reply)",
            value=config.use_hidden_reply_links,
        )

        # Timezone control
        self.timezone_offset_field = ft.TextField(
            value=str(config.timezone_offset_hours),
            width=70,
            hint_text="0",
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        # Batching controls
        self.enable_batching_checkbox = ft.Checkbox(
            label="Enable smart batching (merge short consecutive messages)",
            value=config.enable_batching,
        )

        self.batch_max_field = ft.TextField(
            value=str(config.batch_max_messages),
            width=50,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        self.batch_time_window_field = ft.TextField(
            value=str(config.batch_time_window_minutes),
            width=50,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        self.batch_max_length_field = ft.TextField(
            value=str(config.batch_max_message_length),
            width=70,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        self.error_text = ft.Text(
            "",
            color=ft.Colors.RED_400,
            visible=False,
        )

        # Build UI
        self._build_ui()

    def _load_export_folders(self) -> List[Tuple[str, str, str]]:
        """
        Load and parse export folders.

        Returns:
            List of tuples: (folder_name, display_name, full_path)
        """
        folder_names = self.storage_service.list_export_directories()
        folders = []

        for folder_name in folder_names:
            full_path = str(self.storage_service.base_directory / folder_name)
            display_name = self._parse_folder_name(folder_name)
            folders.append((folder_name, display_name, full_path))

        return folders

    def _parse_folder_name(self, folder_name: str) -> str:
        """
        Parse folder name to extract chat title and ID.

        Args:
            folder_name: Folder name or path in format {title}_{chat_id}
                        (may include parent directories like "exported_messages/...")

        Returns:
            Display name for the folder
        """
        # Extract just the folder name if it's a path
        base_name = folder_name.split("/")[-1]

        # Try to split by last underscore to separate title from ID
        parts = base_name.rsplit("_", 1)
        if len(parts) == 2:
            title, chat_id = parts
            # Check if chat_id is numeric
            if chat_id.lstrip("-").isdigit():
                return f"{title} (ID: {chat_id})"

        # If parsing fails, just return the folder name
        return base_name

    def _on_folder_selected(self, full_path: str):
        """
        Handle folder selection.

        Args:
            full_path: Full path to the selected folder
        """
        self.source_dir_field.value = full_path
        self.source_dir_field.error_text = None
        self.error_text.visible = False
        self.update()

    def _build_export_shortcuts_section(self) -> ft.Container:
        """
        Build the export shortcuts section.

        Returns:
            Container with available export folders
        """
        if not self.export_folders:
            return ft.Container(
                content=ft.Text(
                    "No exported folders found. Export messages first.",
                    size=12,
                    color=ft.Colors.GREY_600,
                    italic=True,
                ),
                padding=10,
            )

        # Build folder cards
        folder_cards = []
        for folder_name, display_name, full_path in self.export_folders:
            # Get folder stats
            stats = self.storage_service.get_export_statistics(full_path)

            card = ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.FOLDER, color=ft.Colors.ORANGE_400),
                        ft.Column(
                            [
                                ft.Text(
                                    display_name,
                                    weight=ft.FontWeight.BOLD,
                                    size=13,
                                ),
                                ft.Text(
                                    f"{stats['total_messages']} messages  •  "
                                    f"{stats['total_files']} files  •  "
                                    f"{stats['total_size_mb']} MB",
                                    size=11,
                                    color=ft.Colors.GREY_600,
                                ),
                            ],
                            spacing=3,
                            expand=True,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.ARROW_FORWARD,
                            icon_color=ft.Colors.BLUE_700,
                            tooltip="Select this folder",
                            on_click=lambda e, path=full_path: self._on_folder_selected(
                                path
                            ),
                        ),
                    ],
                    spacing=10,
                ),
                bgcolor=ft.Colors.GREY_50,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=8,
                padding=10,
                on_click=lambda e, path=full_path: self._on_folder_selected(path),
                ink=True,
            )
            folder_cards.append(card)

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Available exports:",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Column(
                        folder_cards,
                        spacing=8,
                    ),
                ],
                spacing=8,
            ),
        )

    def _build_ui(self):
        """Build the UI layout."""
        # Header
        header = ft.Column(
            [
                ft.Text(
                    "Resend Configuration",
                    size=26,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    f"Configure resend options for: {self.target_chat.title}",
                    size=13,
                    color=ft.Colors.GREY_700,
                ),
                ft.Divider(height=15),
            ],
            spacing=8,
        )

        # Target chat info
        chat_info = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.SEND, color=ft.Colors.BLUE_400),
                    ft.Column(
                        [
                            ft.Text(
                                f"Target Chat: {self.target_chat.title}",
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                f"Type: {self.target_chat.chat_type_display}  •  ID: {self.target_chat.chat_id}",
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

        # Available exports section
        export_shortcuts_section = self._build_export_shortcuts_section()

        # Header customization section
        header_section = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Header Components:", size=14, weight=ft.FontWeight.BOLD),
                    self.show_sender_name_checkbox,
                    self.show_username_checkbox,
                    self.show_date_checkbox,
                    self.show_reply_link_checkbox,
                    self.use_hidden_links_checkbox,
                ],
                spacing=8,
            ),
            padding=10,
            bgcolor=ft.Colors.GREY_50,
            border_radius=8,
        )

        # Timezone section
        timezone_section = ft.Container(
            content=ft.Row(
                [
                    ft.Text("Timezone offset (hours):", size=13),
                    self.timezone_offset_field,
                    ft.Text(
                        "(e.g., 3 for Moscow, -5 for EST)",
                        size=11,
                        color=ft.Colors.GREY_600,
                    ),
                ],
                spacing=10,
            ),
            padding=10,
            bgcolor=ft.Colors.GREY_50,
            border_radius=8,
        )

        # Batching section
        batching_section = ft.Container(
            content=ft.Column(
                [
                    self.enable_batching_checkbox,
                    ft.Row(
                        [
                            ft.Text("Max per batch:", size=12),
                            self.batch_max_field,
                            ft.Text("Time window:", size=12),
                            self.batch_time_window_field,
                            ft.Text("min", size=12),
                        ],
                        spacing=5,
                    ),
                    ft.Row(
                        [
                            ft.Text("Max message length:", size=12),
                            self.batch_max_length_field,
                            ft.Text("chars", size=12),
                        ],
                        spacing=5,
                    ),
                ],
                spacing=8,
            ),
            padding=10,
            bgcolor=ft.Colors.BLUE_50,
            border_radius=8,
        )

        # Form fields
        form = ft.Column(
            [
                ft.Text("Resend Settings:", size=16, weight=ft.FontWeight.BOLD),
                export_shortcuts_section,
                ft.Container(height=10),
                ft.Text("Or enter path manually:", size=14, weight=ft.FontWeight.BOLD),
                self.source_dir_field,
                ft.Container(height=10),
                ft.Text("Options:", size=14, weight=ft.FontWeight.BOLD),
                self.include_media_checkbox,
                self.include_text_checkbox,
                ft.Container(height=10),
                header_section,
                ft.Container(height=5),
                timezone_section,
                ft.Container(height=5),
                batching_section,
            ],
            spacing=15,
        )

        # Warning note
        warning_note = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Warning:",
                        weight=ft.FontWeight.BOLD,
                        size=12,
                        color=ft.Colors.RED_700,
                    ),
                    ft.Text(
                        "• Messages will be sent to the target chat as NEW messages",
                        size=12,
                    ),
                    ft.Text(
                        "• Original message context (replies, etc.) will be lost",
                        size=12,
                    ),
                    ft.Text(
                        "• Ensure you have permission to post in the target chat",
                        size=12,
                    ),
                ],
                spacing=5,
            ),
            bgcolor=ft.Colors.RED_50,
            border=ft.border.all(1, ft.Colors.RED_200),
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
                    "Start Resend",
                    icon=ft.Icons.SEND,
                    on_click=self._on_start_resend_clicked,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.PURPLE_700,
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
            warning_note,
            self.error_text,
            ft.Container(height=5),
            buttons,
        ]
        self.spacing = 0
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO

    async def _on_start_resend_clicked(self, e):
        """Handle start resend button click."""
        # Validate and update config
        try:
            self.config.source_directory = self.source_dir_field.value.strip()
            self.config.include_media = self.include_media_checkbox.value
            self.config.include_text = self.include_text_checkbox.value

            # Header fields
            self.config.show_sender_name = self.show_sender_name_checkbox.value
            self.config.show_sender_username = self.show_username_checkbox.value
            self.config.show_date = self.show_date_checkbox.value
            self.config.show_reply_link = self.show_reply_link_checkbox.value
            self.config.use_hidden_reply_links = self.use_hidden_links_checkbox.value

            # Timezone
            try:
                self.config.timezone_offset_hours = int(
                    self.timezone_offset_field.value or "0"
                )
            except ValueError:
                self._show_error("Timezone offset must be a number")
                return

            # Batching
            self.config.enable_batching = self.enable_batching_checkbox.value
            try:
                self.config.batch_max_messages = int(self.batch_max_field.value or "7")
                self.config.batch_time_window_minutes = int(
                    self.batch_time_window_field.value or "10"
                )
                self.config.batch_max_message_length = int(
                    self.batch_max_length_field.value or "150"
                )
            except ValueError:
                self._show_error("Batching parameters must be numbers")
                return

            # Validate
            if not self.config.source_directory:
                self._show_error("Source directory is required")
                return

            if not self.config.include_media and not self.config.include_text:
                self._show_error("You must select at least one option (media or text)")
                return

            # Call callback
            if self.on_start_resend_callback:
                await self.on_start_resend_callback(self.config)

        except Exception as ex:
            self._show_error(f"Error: {str(ex)}")
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
