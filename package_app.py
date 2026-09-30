"""
Cognitive AI — Standalone Windows Executable Build Script
Uses PyInstaller to create a production-grade, distributable desktop release.
"""

import os
import sys
import shutil
import subprocess

APP_NAME = "CognitiveAI"
ENTRY_POINT = "main_ui_clean.py"
ICON_PATH = os.path.abspath("assets/icon.ico")

def build():
    print(f"==================================================")
    print(f"Building {APP_NAME} Production Release")
    print(f"==================================================")

    # Verify PyInstaller is installed
    try:
        import PyInstaller
        print(f"[OK] PyInstaller detected: {PyInstaller.__version__}")
    except ImportError:
        print("[ERROR] PyInstaller not installed. Install with: pip install pyinstaller")
        sys.exit(1)

    # Prepare command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        f"--name={APP_NAME}",
        f"--icon={ICON_PATH}",
        "--add-data=assets;assets",
        "--add-data=user_settings.json;.",
        "--hidden-import=PyQt6",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=psutil",
        "--hidden-import=win32gui",
        "--hidden-import=win32process",
        "--hidden-import=requests",
        "--hidden-import=sqlite3",
        ENTRY_POINT
    ]

    print(f"\nRunning command:\n{' '.join(cmd)}\n")
    ret = subprocess.run(cmd)

    if ret.returncode == 0:
        dist_dir = os.path.abspath(os.path.join("dist", APP_NAME))
        
        # Ensure data folder template is present in dist
        target_data = os.path.join(dist_dir, "data")
        os.makedirs(target_data, exist_ok=True)
        
        print("\n" + "=" * 50)
        print(f"🎉 BUILD SUCCESSFUL!")
        print(f"Distribution output folder: {dist_dir}")
        print(f"Executable location: {os.path.join(dist_dir, f'{APP_NAME}.exe')}")
        print("=" * 50)
    else:
        print(f"\n[ERROR] PyInstaller failed with exit code {ret.returncode}")
        sys.exit(ret.returncode)

if __name__ == "__main__":
    build()
