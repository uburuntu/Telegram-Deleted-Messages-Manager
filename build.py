"""
Build script for creating standalone executable.
"""

import os
import subprocess
import sys
from pathlib import Path


def build_executable():
    """Build standalone executable using PyInstaller."""
    print("Building standalone executable...")

    # Get project root
    project_root = Path(__file__).parent

    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--name=TelegramDeletedMessagesManager",
        "--onefile",
        "--windowed",
        "--clean",
        f"--add-data=src{os.pathsep}src",
        "--hidden-import=flet",
        "--hidden-import=telethon",
        "--hidden-import=pydantic",
        "--collect-all=flet",
        "--collect-all=flet_core",
        "--collect-all=flet_runtime",
        "main.py",
    ]

    # Run PyInstaller
    try:
        subprocess.run(cmd, check=True, cwd=project_root)
        print("\n[OK] Build successful!")
        print(
            f"Executable location: {project_root / 'dist' / 'TelegramDeletedMessagesManager'}"
        )
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Build failed: {e}")
        sys.exit(1)


def build_with_flet():
    """Build using Flet's native build command."""
    print("Building with Flet...")

    try:
        subprocess.run(["flet", "build", "macos"], check=True)
        print("\n[OK] Flet build successful!")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Flet build failed: {e}")
        print("Note: Flet build command may not be available in all environments.")
        print("Falling back to PyInstaller...")
        build_executable()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--flet":
        build_with_flet()
    else:
        build_executable()
