"""
Verification code authentication screen.
"""

from typing import Awaitable, Callable

import flet as ft


class CodeAuthScreen(ft.Column):
    """Screen for entering verification code."""

    def __init__(
        self,
        phone: str,
        on_code_submitted: Callable[[str], Awaitable[None]],
        on_back: Callable[[], Awaitable[None]],
    ):
        """
        Initialize code auth screen.

        Args:
            phone: Phone number that received the code
            on_code_submitted: Callback when code is submitted
            on_back: Callback to go back
        """
        super().__init__()
        self.phone = phone
        self.on_code_submitted_callback = on_code_submitted
        self.on_back_callback = on_back

        # UI Controls
        self.code_field = ft.TextField(
            label="Verification Code",
            hint_text="Enter the code you received",
            prefix_icon=ft.Icons.SECURITY,
            keyboard_type=ft.KeyboardType.NUMBER,
            max_length=6,
            autofocus=True,
            expand=True,
        )

        self.error_text = ft.Text(
            "",
            color=ft.Colors.RED_400,
            visible=False,
        )

        self.loading = ft.ProgressRing(visible=False)

        # Build UI
        self._build_ui()

    def _build_ui(self):
        """Build the UI layout."""
        # Header
        header = ft.Column(
            [
                ft.Text(
                    "Enter Verification Code",
                    size=26,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    f"Code sent to {self.phone}",
                    size=13,
                    color=ft.Colors.GREY_700,
                ),
                ft.Divider(height=15),
            ],
            spacing=8,
        )

        # Info card
        info_card = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.BLUE_400),
                            ft.Text(
                                "Check your messages:",
                                weight=ft.FontWeight.BOLD,
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Text(
                        "• Look for a message from Telegram in your app",
                        size=13,
                    ),
                    ft.Text(
                        "• Or check your SMS messages",
                        size=13,
                    ),
                    ft.Text(
                        "• The code is usually 5-6 digits",
                        size=13,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=ft.Colors.BLUE_50,
            border=ft.border.all(1, ft.Colors.BLUE_200),
            border_radius=8,
            padding=15,
        )

        # Form
        form = ft.Column(
            [
                ft.Text("Verification Code:", size=16, weight=ft.FontWeight.BOLD),
                self.code_field,
            ],
            spacing=15,
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
                self.loading,
                ft.ElevatedButton(
                    "Verify",
                    icon=ft.Icons.CHECK,
                    on_click=self._on_verify_clicked,
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
            info_card,
            ft.Container(height=15),
            form,
            self.error_text,
            ft.Container(height=5),
            buttons,
        ]
        self.spacing = 0
        self.expand = True
        self.scroll = ft.ScrollMode.AUTO

    async def _on_verify_clicked(self, e):
        """Handle verify button click."""
        code = self.code_field.value

        # Basic validation
        if not code or not code.strip():
            self._show_error("Please enter the verification code")
            return

        code = code.strip()

        if not code.isdigit():
            self._show_error("Code must contain only digits")
            return

        # Clear error and show loading
        self._show_error("")
        self.loading.visible = True
        self.update()

        # Call callback
        if self.on_code_submitted_callback:
            try:
                await self.on_code_submitted_callback(code)
            except Exception as ex:
                self._show_error(f"Error: {str(ex)}")
                self.loading.visible = False
                self.update()

    async def _on_back_clicked(self, e):
        """Handle back button click."""
        if self.on_back_callback:
            await self.on_back_callback()

    def _show_error(self, message: str):
        """Show error message."""
        self.error_text.value = message
        self.error_text.visible = bool(message)
        self.update()
