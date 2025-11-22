"""
Progress screen for showing operation progress.
"""

from typing import Awaitable, Callable, Optional

import flet as ft

from ...models.message import ExportProgress


class ProgressScreen(ft.Column):
    """Screen for displaying operation progress."""

    def __init__(
        self,
        title: str,
        on_complete: Optional[Callable[[], Awaitable[None]]] = None,
        on_stop: Optional[Callable[[], Awaitable[None]]] = None,
        on_back: Optional[Callable[[], Awaitable[None]]] = None,
    ):
        """
        Initialize progress screen.

        Args:
            title: Screen title
            on_complete: Callback when operation is complete
            on_stop: Callback to stop the operation
            on_back: Callback to go back
        """
        super().__init__()
        self.screen_title = title
        self.on_complete_callback = on_complete
        self.on_stop_callback = on_stop
        self.on_back_callback = on_back

        # UI Controls
        self.progress_bar = ft.ProgressBar(
            width=350,
            value=0,
            bar_height=18,
            color=ft.Colors.BLUE_400,
            bgcolor=ft.Colors.BLUE_100,
        )

        self.status_text = ft.Text(
            "Initializing...",
            size=15,
            weight=ft.FontWeight.BOLD,
        )

        self.progress_percentage = ft.Text(
            "0%",
            size=22,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_700,
        )

        self.stats_container = ft.Column(
            [],
            spacing=10,
        )

        self.stop_button = ft.ElevatedButton(
            "Stop",
            icon=ft.Icons.STOP,
            on_click=self._on_stop_clicked,
            visible=True,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.RED_700,
            ),
        )

        self.back_button = ft.TextButton(
            "Back",
            icon=ft.Icons.ARROW_BACK,
            on_click=self._on_back_clicked,
            visible=False,
        )

        self.complete_button = ft.ElevatedButton(
            "Continue",
            icon=ft.Icons.ARROW_FORWARD,
            on_click=self._on_complete_clicked,
            visible=False,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.GREEN_700,
            ),
        )

        self.error_container = ft.Container(
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
                    self.screen_title,
                    size=26,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Divider(height=15),
            ],
            spacing=8,
        )

        # Progress section
        progress_section = ft.Column(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            self.status_text,
                            ft.Container(height=10),
                            self.progress_bar,
                            ft.Container(height=10),
                            self.progress_percentage,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    alignment=ft.alignment.center,
                ),
            ],
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Stats section
        stats_section = ft.Container(
            content=self.stats_container,
            bgcolor=ft.Colors.GREY_100,
            border_radius=8,
            padding=20,
        )

        # Error section
        self.error_container.content = ft.Column(
            [
                ft.Icon(ft.Icons.ERROR_OUTLINE, size=48, color=ft.Colors.RED_400),
                ft.Text(
                    "An error occurred",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.RED_700,
                ),
                ft.Text(
                    "",
                    size=14,
                    color=ft.Colors.RED_600,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )
        self.error_container.bgcolor = ft.Colors.RED_50
        self.error_container.border = ft.border.all(1, ft.Colors.RED_200)
        self.error_container.border_radius = 8
        self.error_container.padding = 20

        # Buttons section
        buttons_section = ft.Container(
            content=ft.Row(
                [
                    self.back_button,
                    ft.Container(expand=True),
                    self.stop_button,
                    self.complete_button,
                ],
                spacing=10,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
        )

        # Main layout
        self.controls = [
            header,
            ft.Container(height=15),
            progress_section,
            ft.Container(height=15),
            stats_section,
            ft.Container(height=10),
            self.error_container,
            ft.Container(height=10),
            buttons_section,
        ]
        self.spacing = 0
        self.expand = True
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    def update_progress(self, progress: ExportProgress):
        """
        Update progress display.

        Args:
            progress: ExportProgress object
        """
        # Update progress bar
        if progress.total_messages > 0:
            self.progress_bar.value = progress.progress_percentage / 100
        else:
            self.progress_bar.value = None  # Indeterminate

        # Update percentage
        self.progress_percentage.value = f"{progress.progress_percentage:.1f}%"

        # Update status
        if progress.is_complete:
            self.stop_button.visible = False
            self.back_button.visible = True
            if progress.error_message:
                self.status_text.value = "Failed"
                self.status_text.color = ft.Colors.RED_700
                self._show_error(progress.error_message)
            else:
                self.status_text.value = "Complete!"
                self.status_text.color = ft.Colors.GREEN_700
                self.complete_button.visible = True
        else:
            self.status_text.value = (
                f"Processing message {progress.current_message_id or '...'}"
            )
            self.status_text.color = ft.Colors.BLUE_700
            self.stop_button.visible = True
            self.back_button.visible = False
            self.complete_button.visible = False

        # Update stats
        self._update_stats(progress)

        self.update()

    def _update_stats(self, progress: ExportProgress):
        """Update statistics display."""
        self.stats_container.controls.clear()

        stats = [
            ("Total Messages", progress.total_messages),
            ("Processed", progress.processed_messages),
            ("Text Messages", progress.exported_text_messages),
            ("Media Messages", progress.exported_media_messages),
            ("Failed", progress.failed_messages),
            ("Success Rate", f"{progress.success_rate:.1f}%"),
            ("Elapsed Time", progress.formatted_elapsed_time),
            ("Estimated Time Remaining", progress.formatted_eta),
        ]

        for label, value in stats:
            stat_row = ft.Row(
                [
                    ft.Text(
                        f"{label}:",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        expand=True,
                    ),
                    ft.Text(
                        str(value),
                        size=14,
                    ),
                ],
                spacing=10,
            )
            self.stats_container.controls.append(stat_row)

    def _show_error(self, error_message: str):
        """Show error message."""
        self.error_container.visible = True
        error_text = self.error_container.content.controls[2]
        error_text.value = error_message

    async def _on_stop_clicked(self, e):
        """Handle stop button click."""
        if self.on_stop_callback:
            await self.on_stop_callback()

    async def _on_back_clicked(self, e):
        """Handle back button click."""
        if self.on_back_callback:
            await self.on_back_callback()

    async def _on_complete_clicked(self, e):
        """Handle complete button click."""
        if self.on_complete_callback:
            await self.on_complete_callback()
