"""
Main Flet application.
"""

from typing import Optional

import flet as ft

from ..models.chat import ChatInfo
from ..models.config import ExportConfig, ResendConfig, TelegramConfig
from ..models.message import ExportProgress
from ..services.export_service import ExportService
from ..services.resend_service import ResendService
from ..services.storage_service import StorageService
from ..services.telegram_service import TelegramService
from .screens.chat_select_screen import ChatSelectScreen
from .screens.code_auth_screen import CodeAuthScreen
from .screens.config_screen import ConfigScreen
from .screens.export_config_screen import ExportConfigScreen
from .screens.password_auth_screen import PasswordAuthScreen
from .screens.phone_auth_screen import PhoneAuthScreen
from .screens.progress_screen import ProgressScreen
from .screens.resend_config_screen import ResendConfigScreen
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TelegramApp:
    """Main application class."""

    def __init__(self, page: ft.Page):
        """
        Initialize the application.

        Args:
            page: Flet page object
        """
        self.page = page
        self.page.title = "Telegram Deleted Messages Manager"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 20

        # Set responsive window sizing that better fits content
        self.page.window.width = 600
        self.page.window.height = 550
        self.page.window.min_width = 600
        self.page.window.min_height = 500
        self.page.window.resizable = True

        # Services
        self.storage_service = StorageService()
        self.telegram_service: Optional[TelegramService] = None
        self.export_service: Optional[ExportService] = None
        self.resend_service: Optional[ResendService] = None

        # Configuration
        self.app_config = self.storage_service.load_config()

        # State
        self.current_screen: Optional[ft.Control] = None
        self.selected_chat: Optional[ChatInfo] = None
        self.selected_resend_chat: Optional[ChatInfo] = None
        self.auth_phone: Optional[str] = None  # Store phone during auth flow

        # Initialize
        self._initialize()

    def _initialize(self):
        """Initialize the application."""
        # Show appropriate first screen
        if not self.app_config.telegram.is_valid():
            self._show_config_screen()
        else:
            # Try to connect and show main menu
            self.page.run_task(self._connect_and_show_menu)

    async def _connect_and_show_menu(self):
        """Connect to Telegram and show main menu."""
        try:
            # Initialize services
            self.telegram_service = TelegramService(self.app_config.telegram)
            is_authorized = await self.telegram_service.connect()

            if is_authorized:
                # Already logged in - initialize services and show menu
                self.export_service = ExportService(self.telegram_service)
                self.resend_service = ResendService(self.telegram_service)
                self._show_main_menu()
            else:
                # Need to authenticate - show phone screen
                self._show_phone_auth_screen()

        except Exception as e:
            # Show error and go back to config
            self._show_error_dialog(
                "Connection Failed",
                f"Failed to connect to Telegram: {str(e)}\n\nPlease check your API credentials.",
            )
            self._show_config_screen()

    def _show_phone_auth_screen(self):
        """Show phone authentication screen."""
        self._clear_content()
        screen = PhoneAuthScreen(
            on_phone_submitted=self._on_phone_submitted,
            on_back=self._on_phone_auth_back,
        )
        self._set_content(screen)

    async def _on_phone_submitted(self, phone: str):
        """Handle phone number submitted."""
        self.auth_phone = phone
        try:
            # Send verification code
            result = await self.telegram_service.authenticate(phone=phone)

            if result["status"] == "code_sent":
                # Show code entry screen
                self._show_code_auth_screen(phone)
            else:
                self._show_error_dialog(
                    "Error",
                    f"Failed to send code: {result.get('message', 'Unknown error')}",
                )
        except Exception as e:
            self._show_error_dialog("Error", f"Failed to send code: {str(e)}")

    async def _on_phone_auth_back(self):
        """Handle back from phone auth."""
        self._show_config_screen()

    def _show_code_auth_screen(self, phone: str):
        """Show code verification screen."""
        self._clear_content()
        screen = CodeAuthScreen(
            phone=phone,
            on_code_submitted=self._on_code_submitted,
            on_back=self._on_code_auth_back,
        )
        self._set_content(screen)

    async def _on_code_submitted(self, code: str):
        """Handle verification code submitted."""
        try:
            # Sign in with code
            result = await self.telegram_service.authenticate(
                phone=self.auth_phone, code=code
            )

            if result["status"] == "success":
                # Successfully authenticated - initialize services
                self.export_service = ExportService(self.telegram_service)
                self.resend_service = ResendService(self.telegram_service)
                self._show_main_menu()
            elif result["status"] == "password_required":
                # 2FA is enabled - show password screen
                self._show_password_auth_screen()
            else:
                self._show_error_dialog(
                    "Error",
                    f"Failed to verify code: {result.get('message', 'Unknown error')}",
                )
        except Exception as e:
            self._show_error_dialog("Error", f"Failed to verify code: {str(e)}")

    async def _on_code_auth_back(self):
        """Handle back from code auth."""
        self._show_phone_auth_screen()

    def _show_password_auth_screen(self):
        """Show 2FA password screen."""
        self._clear_content()
        screen = PasswordAuthScreen(
            on_password_submitted=self._on_password_submitted,
            on_back=self._on_password_auth_back,
        )
        self._set_content(screen)

    async def _on_password_submitted(self, password: str):
        """Handle 2FA password submitted."""
        try:
            # Sign in with password
            result = await self.telegram_service.authenticate(password=password)

            if result["status"] == "success":
                # Successfully authenticated - initialize services
                self.export_service = ExportService(self.telegram_service)
                self.resend_service = ResendService(self.telegram_service)
                self._show_main_menu()
            else:
                self._show_error_dialog(
                    "Error",
                    f"Failed to verify password: {result.get('message', 'Incorrect password')}",
                )
        except Exception as e:
            self._show_error_dialog("Error", f"Failed to verify password: {str(e)}")

    async def _on_password_auth_back(self):
        """Handle back from password auth."""
        self._show_code_auth_screen(self.auth_phone)

    def _show_config_screen(self):
        """Show API configuration screen."""
        self._clear_content()
        screen = ConfigScreen(
            config=self.app_config.telegram,
            on_save=self._on_config_saved,
        )
        self._set_content(screen)

    async def _on_config_saved(self, config: TelegramConfig):
        """Handle configuration saved."""
        self.app_config.telegram = config
        self.storage_service.save_config(self.app_config)

        # Connect and proceed
        await self._connect_and_show_menu()

    def _show_main_menu(self):
        """Show main menu screen."""
        self._clear_content()

        # Build menu with improved spacing and layout
        menu = ft.Column(
            [
                ft.Text(
                    "Telegram Deleted Messages Manager",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "What would you like to do?",
                    size=15,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Divider(height=20),
                ft.ElevatedButton(
                    "Export Deleted Messages",
                    icon=ft.Icons.DOWNLOAD,
                    on_click=lambda _: self._show_export_chat_select(),
                    width=280,
                    height=55,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.BLUE_700,
                    ),
                ),
                ft.ElevatedButton(
                    "Re-send Exported Messages",
                    icon=ft.Icons.SEND,
                    on_click=lambda _: self._show_resend_chat_select(),
                    width=280,
                    height=55,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.PURPLE_700,
                    ),
                ),
                ft.Divider(height=10),
                ft.TextButton(
                    "Change API Configuration",
                    icon=ft.Icons.SETTINGS,
                    on_click=lambda _: self._show_config_screen(),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
        )

        container = ft.Container(
            content=menu,
            expand=True,
            alignment=ft.alignment.center,
        )

        self._set_content(container)

    def _show_export_chat_select(self):
        """Show chat selection for export."""
        self._clear_content()
        screen = ChatSelectScreen(
            telegram_service=self.telegram_service,
            on_chat_selected=self._on_export_chat_selected,
            title="Select Chat to Export From",
            description="Choose the chat to export deleted messages from",
            mode="export",
        )
        self._set_content(screen)

    async def _on_export_chat_selected(self, chat: ChatInfo):
        """Handle chat selected for export."""
        self.selected_chat = chat
        self._show_export_config_screen()

    def _show_export_config_screen(self):
        """Show export configuration screen."""
        self._clear_content()
        screen = ExportConfigScreen(
            chat=self.selected_chat,
            config=self.app_config.export,
            on_start_export=self._on_start_export,
            on_back=self._on_export_config_back,
        )
        self._set_content(screen)

    async def _on_start_export(self, config: ExportConfig):
        """Start export process."""
        self.app_config.export = config
        self.storage_service.save_config(self.app_config)

        # Show progress screen
        progress_screen = ProgressScreen(
            title="Exporting Messages",
            on_complete=self._on_export_complete,
        )
        self._clear_content()
        self._set_content(progress_screen)

        # Start export
        try:
            await self.export_service.export_deleted_messages(
                config=config,
                progress_callback=lambda p: self._update_progress(progress_screen, p),
            )
        except Exception as e:
            progress = ExportProgress()
            progress.error_message = str(e)
            progress.is_complete = True
            progress_screen.update_progress(progress)

    async def _on_export_config_back(self):
        """Handle back from export config."""
        self._show_export_chat_select()

    async def _on_export_complete(self):
        """Handle export complete."""
        self._show_main_menu()

    def _show_resend_chat_select(self):
        """Show chat selection for resend."""
        self._clear_content()
        screen = ChatSelectScreen(
            telegram_service=self.telegram_service,
            on_chat_selected=self._on_resend_chat_selected,
            title="Select Target Chat",
            description="Choose the chat to re-send messages to",
            mode="resend",
        )
        self._set_content(screen)

    async def _on_resend_chat_selected(self, chat: ChatInfo):
        """Handle chat selected for resend."""
        self.selected_resend_chat = chat
        self._show_resend_config_screen()

    def _show_resend_config_screen(self):
        """Show resend configuration screen."""
        self._clear_content()
        screen = ResendConfigScreen(
            target_chat=self.selected_resend_chat,
            config=self.app_config.resend,
            storage_service=self.storage_service,
            on_start_resend=self._on_start_resend,
            on_back=self._on_resend_config_back,
        )
        self._set_content(screen)

    async def _on_start_resend(self, config: ResendConfig):
        """Start resend process."""
        self.app_config.resend = config
        self.storage_service.save_config(self.app_config)

        # Show progress screen
        progress_screen = ProgressScreen(
            title="Re-sending Messages",
            on_complete=self._on_resend_complete,
            on_stop=self._on_resend_stop,
        )
        self._clear_content()
        self._set_content(progress_screen)

        # Start resend
        try:
            await self.resend_service.resend_messages(
                config=config,
                progress_callback=lambda p: self._update_progress(progress_screen, p),
            )
        except Exception as e:
            progress = ExportProgress()
            progress.error_message = str(e)
            progress.is_complete = True
            progress_screen.update_progress(progress)

    async def _on_resend_config_back(self):
        """Handle back from resend config."""
        self._show_resend_chat_select()

    async def _on_resend_complete(self):
        """Handle resend complete."""
        self._show_main_menu()

    async def _on_resend_stop(self):
        """Handle stop button click during resend."""
        logger.info("User clicked stop during resend")
        if self.resend_service:
            self.resend_service.cancel()

    def _update_progress(self, screen: ProgressScreen, progress: ExportProgress):
        """Update progress screen."""
        screen.update_progress(progress)

    def _clear_content(self):
        """Clear page content."""
        self.page.controls.clear()
        self.current_screen = None

    def _set_content(self, control: ft.Control):
        """Set page content."""
        self.current_screen = control
        self.page.add(control)
        self.page.update()

    def _show_error_dialog(self, title: str, message: str):
        """Show error dialog."""
        dialog = ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Text(message),
            actions=[
                ft.TextButton("OK", on_click=lambda _: self.page.close(dialog)),
            ],
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()


def main(page: ft.Page):
    """Main entry point for Flet app."""
    _app = TelegramApp(page)  # Keep instance alive
