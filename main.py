"""
Main entry point for the Telegram Deleted Messages Manager application.
"""

import flet as ft

from src.ui.app import main

if __name__ == "__main__":
    ft.app(target=main)
