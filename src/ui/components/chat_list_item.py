"""
Chat list item component.
"""

import flet as ft

from ...models.chat import ChatInfo


class ChatListItem(ft.Container):
    """Component for displaying a chat item in a list."""

    def __init__(self, chat: ChatInfo, on_click):
        """
        Initialize chat list item.

        Args:
            chat: ChatInfo object
            on_click: Callback when item is clicked
        """
        super().__init__()
        self.chat = chat
        self.on_click_callback = on_click

        # Build UI
        self._build_ui()

    def _build_ui(self):
        """Build the UI layout."""
        # Chat icon based on type
        icon_map = {
            "channel": ft.Icons.CAMPAIGN,
            "group": ft.Icons.GROUP,
            "supergroup": ft.Icons.GROUPS,
            "user": ft.Icons.PERSON,
            "chat": ft.Icons.CHAT,
        }
        icon = icon_map.get(self.chat.chat_type, ft.Icons.CHAT)

        # Build content
        content = ft.Row(
            [
                ft.Icon(icon, size=40, color=ft.Colors.BLUE_400),
                ft.Column(
                    [
                        ft.Text(
                            self.chat.title,
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Row(
                            [
                                ft.Text(
                                    self.chat.chat_type_display,
                                    size=12,
                                    color=ft.Colors.GREY_600,
                                ),
                                ft.Text(
                                    f"@{self.chat.username}"
                                    if self.chat.username
                                    else "",
                                    size=12,
                                    color=ft.Colors.GREY_500,
                                ),
                                ft.Text(
                                    f"ID: {self.chat.chat_id}",
                                    size=12,
                                    color=ft.Colors.GREY_500,
                                ),
                            ],
                            spacing=10,
                        ),
                    ],
                    spacing=5,
                    expand=True,
                ),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=ft.Colors.GREY_400),
            ],
            spacing=15,
            alignment=ft.MainAxisAlignment.START,
        )

        self.content = content
        self.padding = 15
        self.border = ft.border.all(1, ft.Colors.GREY_300)
        self.border_radius = 8
        self.ink = True
        self.on_click = self._handle_click

        # Hover effect
        self.bgcolor = ft.Colors.WHITE
        self.on_hover = self._on_hover

    async def _handle_click(self, e):
        """Handle click event."""
        if self.on_click_callback:
            await self.on_click_callback(self.chat)

    def _on_hover(self, e):
        """Handle hover effect."""
        self.bgcolor = ft.Colors.BLUE_50 if e.data == "true" else ft.Colors.WHITE
        self.update()
