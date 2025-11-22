"""
Phone number authentication screen.
"""

from typing import Awaitable, Callable

import flet as ft


class PhoneAuthScreen(ft.Column):
    """Screen for entering phone number for Telegram authentication."""

    def __init__(
        self,
        on_phone_submitted: Callable[[str], Awaitable[None]],
        on_back: Callable[[], Awaitable[None]],
    ):
        """
        Initialize phone auth screen.

        Args:
            on_phone_submitted: Callback when phone is submitted
            on_back: Callback to go back
        """
        super().__init__()
        self.on_phone_submitted_callback = on_phone_submitted
        self.on_back_callback = on_back

        # UI Controls
        self.phone_field = ft.TextField(
            label="Phone Number",
            hint_text="Enter with country code, e.g., +1234567890",
            prefix_icon=ft.Icons.PHONE,
            keyboard_type=ft.KeyboardType.PHONE,
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
                    "Sign In to Telegram",
                    size=26,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "Enter your phone number to receive a verification code",
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
                                "Important:",
                                weight=ft.FontWeight.BOLD,
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Text(
                        "• Include your country code (e.g., +1 for USA)",
                        size=13,
                    ),
                    ft.Text(
                        "• You'll receive a code via Telegram or SMS",
                        size=13,
                    ),
                    ft.Text(
                        "• Make sure you have access to this number",
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
                ft.Text("Your Phone Number:", size=16, weight=ft.FontWeight.BOLD),
                self.phone_field,
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
                    "Send Code",
                    icon=ft.Icons.SEND,
                    on_click=self._on_send_code_clicked,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.BLUE_700,
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

    async def _on_send_code_clicked(self, e):
        """Handle send code button click."""
        phone = self.phone_field.value

        # Basic validation
        if not phone or not phone.strip():
            self._show_error("Please enter your phone number")
            return

        phone = phone.strip()

        if not phone.startswith("+"):
            self._show_error("Phone number must start with + and country code")
            return

        # Clear error and show loading
        self._show_error("")
        self.loading.visible = True
        self.update()

        # Call callback
        if self.on_phone_submitted_callback:
            try:
                await self.on_phone_submitted_callback(phone)
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
