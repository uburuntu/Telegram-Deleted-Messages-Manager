"""
2FA password authentication screen.
"""

from typing import Awaitable, Callable

import flet as ft


class PasswordAuthScreen(ft.Column):
    """Screen for entering 2FA password."""

    def __init__(
        self,
        on_password_submitted: Callable[[str], Awaitable[None]],
        on_back: Callable[[], Awaitable[None]],
    ):
        """
        Initialize password auth screen.

        Args:
            on_password_submitted: Callback when password is submitted
            on_back: Callback to go back
        """
        super().__init__()
        self.on_password_submitted_callback = on_password_submitted
        self.on_back_callback = on_back

        # UI Controls
        self.password_field = ft.TextField(
            label="Two-Factor Authentication Password",
            hint_text="Enter your 2FA password",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
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
                    "Two-Factor Authentication",
                    size=26,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "Your account has 2FA enabled",
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
                            ft.Icon(ft.Icons.SECURITY, color=ft.Colors.ORANGE_400),
                            ft.Text(
                                "Additional Security:",
                                weight=ft.FontWeight.BOLD,
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Text(
                        "• This is the cloud password you set up in Telegram",
                        size=13,
                    ),
                    ft.Text(
                        "• It's different from your verification code",
                        size=13,
                    ),
                    ft.Text(
                        "• This password protects your account",
                        size=13,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=ft.Colors.ORANGE_50,
            border=ft.border.all(1, ft.Colors.ORANGE_200),
            border_radius=8,
            padding=15,
        )

        # Form
        form = ft.Column(
            [
                ft.Text("Password:", size=16, weight=ft.FontWeight.BOLD),
                self.password_field,
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
                    "Sign In",
                    icon=ft.Icons.LOGIN,
                    on_click=self._on_sign_in_clicked,
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

    async def _on_sign_in_clicked(self, e):
        """Handle sign in button click."""
        password = self.password_field.value

        # Basic validation
        if not password:
            self._show_error("Please enter your 2FA password")
            return

        # Clear error and show loading
        self._show_error("")
        self.loading.visible = True
        self.update()

        # Call callback
        if self.on_password_submitted_callback:
            try:
                await self.on_password_submitted_callback(password)
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
