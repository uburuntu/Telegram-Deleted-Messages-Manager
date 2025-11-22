"""
Chat selection screen.
"""

from typing import Awaitable, Callable, List

import flet as ft

from ...models.chat import ChatInfo
from ...services.telegram_service import TelegramService
from ...utils.validators import validate_chat_id, validate_search_query
from ..components.chat_list_item import ChatListItem


class ChatSelectScreen(ft.Column):
    """Screen for selecting a chat."""

    def __init__(
        self,
        telegram_service: TelegramService,
        on_chat_selected: Callable[[ChatInfo], Awaitable[None]],
        on_back: Callable[[], Awaitable[None]] = None,
        title: str = "Select a Chat",
        description: str = "Choose a chat to export deleted messages from",
        mode: str = "export",  # "export" or "resend"
    ):
        """
        Initialize chat select screen.

        Args:
            telegram_service: TelegramService instance
            on_chat_selected: Callback when chat is selected
            on_back: Callback to go back
            title: Screen title
            description: Screen description
            mode: Selection mode ("export" or "resend") for permission filtering
        """
        super().__init__()
        self.telegram_service = telegram_service
        self.on_chat_selected_callback = on_chat_selected
        self.on_back_callback = on_back
        self.screen_title = title
        self.screen_description = description
        self.mode = mode

        # State
        self.chats: List[ChatInfo] = []
        self.loading = False
        self.initial_load_done = False

        # UI Controls
        self.search_field = ft.TextField(
            label="Search by chat name",
            hint_text="Type to search...",
            prefix_icon=ft.Icons.SEARCH,
            on_submit=self._on_search_submitted,
            expand=True,
        )

        self.chat_id_field = ft.TextField(
            label="Or enter Chat ID",
            hint_text="e.g., -1001234567890",
            keyboard_type=ft.KeyboardType.TEXT,
            prefix_icon=ft.Icons.TAG,
            expand=True,
        )

        self.chat_list_container = ft.Column(
            [],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        self.error_text = ft.Text(
            "",
            color=ft.Colors.RED_400,
            visible=False,
            size=13,
        )

        self.loading_indicator = ft.ProgressRing(
            visible=False,
            width=20,
            height=20,
        )

        self.info_text = ft.Text(
            "",
            color=ft.Colors.BLUE_600,
            visible=False,
            size=13,
            italic=True,
        )

        # Build UI
        self._build_ui()

        # Auto-load recent chats after UI is built
        if self.page:
            self.page.run_task(self._initial_load)

    def did_mount(self):
        """Called when the control is added to the page."""
        if not self.initial_load_done:
            self.page.run_task(self._initial_load)

    async def _initial_load(self):
        """Load recent chats automatically on initialization."""
        if self.initial_load_done:
            return

        self.initial_load_done = True
        await self._load_recent_chats_internal()

    def _build_ui(self):
        """Build the UI layout."""
        # Header
        header = ft.Column(
            [
                ft.Text(
                    self.screen_title,
                    size=26,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    self.screen_description,
                    size=13,
                    color=ft.Colors.GREY_700,
                ),
                ft.Divider(height=15),
            ],
            spacing=8,
        )

        # Info note about permissions
        permission_note = self._build_permission_note()

        # Search and ID section combined
        search_id_section = ft.Column(
            [
                ft.Text("Find a specific chat:", size=15, weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        self.search_field,
                        ft.IconButton(
                            icon=ft.Icons.SEARCH,
                            tooltip="Search",
                            on_click=self._on_search_clicked,
                            style=ft.ButtonStyle(
                                color=ft.Colors.WHITE,
                                bgcolor=ft.Colors.BLUE_700,
                            ),
                        ),
                    ],
                    spacing=10,
                ),
                ft.Row(
                    [
                        self.chat_id_field,
                        ft.IconButton(
                            icon=ft.Icons.ARROW_FORWARD,
                            tooltip="Load by ID",
                            on_click=self._on_load_chat_by_id_clicked,
                            style=ft.ButtonStyle(
                                color=ft.Colors.WHITE,
                                bgcolor=ft.Colors.GREEN_700,
                            ),
                        ),
                    ],
                    spacing=10,
                ),
            ],
            spacing=12,
        )

        # Recent chats section
        recent_chats_header = ft.Row(
            [
                ft.Text("Your recent chats:", size=15, weight=ft.FontWeight.BOLD),
                self.loading_indicator,
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Refresh",
                    on_click=self._on_load_recent_clicked,
                    icon_size=20,
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=10,
        )

        # Back button at the bottom
        back_button = ft.Container(
            content=ft.TextButton(
                "Back",
                icon=ft.Icons.ARROW_BACK,
                on_click=self._on_back_clicked,
            )
            if self.on_back_callback
            else None,
            alignment=ft.alignment.center_left,
            padding=ft.padding.only(top=15),
        )

        # Main layout
        self.controls = [
            header,
            permission_note,
            ft.Container(height=8),
            search_id_section,
            ft.Container(height=12),
            ft.Divider(),
            recent_chats_header,
            self.info_text,
            self.error_text,
            self.chat_list_container,
            back_button if self.on_back_callback else ft.Container(),
        ]
        self.spacing = 0
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO

    def _build_permission_note(self) -> ft.Container:
        """Build permission note based on mode."""
        if self.mode == "export":
            note_text = "Note: Exporting requires admin rights in channels/supergroups. Export will fail if you don't have the necessary permissions."
            icon = ft.Icons.INFO_OUTLINE
            color = ft.Colors.BLUE_400
        else:  # resend
            note_text = "Note: Resending requires permission to send messages in the target chat. Operation will fail if you don't have the necessary permissions."
            icon = ft.Icons.INFO_OUTLINE
            color = ft.Colors.BLUE_400

        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, size=20, color=color),
                    ft.Text(
                        note_text,
                        size=12,
                        color=ft.Colors.GREY_700,
                        italic=True,
                    ),
                ],
                spacing=10,
            ),
            bgcolor=ft.Colors.BLUE_50,
            border_radius=6,
            padding=10,
        )

    async def _on_search_clicked(self, e):
        """Handle search button click."""
        await self._perform_search()

    async def _on_search_submitted(self, e):
        """Handle search field submit."""
        await self._perform_search()

    async def _perform_search(self):
        """Perform chat search."""
        query = self.search_field.value

        # Validate query
        is_valid, error = validate_search_query(query)
        if not is_valid:
            self._show_error(error)
            self.search_field.error_text = error
            self.update()
            return

        self.search_field.error_text = None
        self._show_loading(True)
        self._show_error("")
        self._show_info("")

        try:
            # Search chats
            chats = await self.telegram_service.search_chats(query, limit=30)

            self.chats = chats
            self._update_chat_list()

            if len(chats) == 0:
                self._show_info(f"No chats found matching '{query}'")
            else:
                self._show_info(f"Found {len(chats)} chat(s) matching '{query}'")

        except Exception as ex:
            self._show_error(f"Error searching chats: {str(ex)}")
        finally:
            self._show_loading(False)
            self.update()

    async def _on_load_chat_by_id_clicked(self, e):
        """Handle load chat by ID button click."""
        chat_id_str = self.chat_id_field.value

        # Validate chat ID
        is_valid, error, chat_id = validate_chat_id(chat_id_str)
        if not is_valid:
            self._show_error(error)
            self.chat_id_field.error_text = error
            self.update()
            return

        self.chat_id_field.error_text = None
        self._show_loading(True)
        self._show_error("")
        self._show_info("")

        try:
            # Get chat by ID
            chat = await self.telegram_service.get_chat_by_id(chat_id)
            if chat:
                await self._on_chat_clicked(chat)
            else:
                self._show_error(f"Chat with ID {chat_id} not found")

        except Exception as ex:
            self._show_error(f"Error loading chat: {str(ex)}")
        finally:
            self._show_loading(False)
            self.update()

    async def _on_load_recent_clicked(self, e):
        """Handle refresh button click."""
        await self._load_recent_chats_internal()

    async def _load_recent_chats_internal(self):
        """Internal method to load recent chats."""
        self._show_loading(True)
        self._show_error("")
        self._show_info("Loading your recent chats...")

        try:
            # Load recent chats
            chats = await self.telegram_service.get_recent_chats(limit=50)

            self.chats = chats
            self._update_chat_list()

            if len(chats) == 0:
                self._show_info("No recent chats found")
            else:
                self._show_info(f"Loaded {len(chats)} recent chat(s)")

        except Exception as ex:
            self._show_error(f"Error loading recent chats: {str(ex)}")
        finally:
            self._show_loading(False)
            self.update()

    async def _on_chat_clicked(self, chat: ChatInfo):
        """Handle chat item click."""
        if self.on_chat_selected_callback:
            await self.on_chat_selected_callback(chat)

    def _update_chat_list(self):
        """Update the chat list display."""
        self.chat_list_container.controls.clear()

        for chat in self.chats:
            item = ChatListItem(chat, self._on_chat_clicked)
            self.chat_list_container.controls.append(item)

    def _show_loading(self, loading: bool):
        """Show/hide loading indicator."""
        self.loading = loading
        self.loading_indicator.visible = loading

    def _show_error(self, message: str):
        """Show error message."""
        self.error_text.value = message
        self.error_text.visible = bool(message)

    def _show_info(self, message: str):
        """Show info message."""
        self.info_text.value = message
        self.info_text.visible = bool(message)

    async def _on_back_clicked(self, e):
        """Handle back button click."""
        if self.on_back_callback:
            await self.on_back_callback()
