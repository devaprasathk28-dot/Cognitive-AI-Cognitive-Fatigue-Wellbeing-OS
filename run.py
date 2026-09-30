#!/usr/bin/env python3
"""
Cognitive AI — Master Product Launcher
======================================
Intelligent launcher for the Cognitive Fatigue & Wellbeing OS.
Automatically manages the background tracking engine, local SQLite database,
and chooses the premier UI interface (Electron + TypeScript Desktop or Native PyQt6).
"""

import os
import sys
import time
import shutil
import signal
import subprocess
import argparse

WORKSPACE_ROOT = os.path.dirname(os.path.abspath(__file__))
ELECTRON_APP_DIR = os.path.join(WORKSPACE_ROOT, "electron-app")
BRIDGE_SERVER_PY = os.path.join(WORKSPACE_ROOT, "bridge_server.py")
QT_MAIN_PY = os.path.join(WORKSPACE_ROOT, "main_ui_clean.py")

CHILD_PROCESSES = []


def cleanup(signum=None, frame=None):
    """Gracefully terminates all child processes."""
    print("\n[Cognitive AI] Shutting down services cleanly...")
    for proc in CHILD_PROCESSES:
        try:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    print("[Cognitive AI] All background services stopped.")
    sys.exit(0)


def check_node_electron_ready() -> bool:
    """Checks if Node.js and Electron are installed and ready."""
    node_bin = shutil.which("node")
    npm_bin = shutil.which("npm")
    if not node_bin or not npm_bin:
        return False

    dist_main = os.path.join(ELECTRON_APP_DIR, "dist-electron", "main", "main.js")
    node_modules = os.path.join(ELECTRON_APP_DIR, "node_modules")
    return os.path.exists(dist_main) and os.path.exists(node_modules)


def launch_electron_mode():
    """Starts the Python Bridge Server and launches the high-fidelity Electron desktop app."""
    print("=" * 65)
    print("⚡ COGNITIVE AI — HIGH-FIDELITY ELECTRON DESKTOP OS")
    print("   Platform: Windows | Architecture: Electron 33 + TypeScript + Python")
    print("   Engine: Local REST API on http://127.0.0.1:8765")
    print("=" * 65)

    # 1. Start Python bridge server
    print("[1/2] Starting Cognitive AI Telemetry Bridge Server...")
    bridge_proc = subprocess.Popen(
        [sys.executable, BRIDGE_SERVER_PY],
        cwd=WORKSPACE_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
    )
    CHILD_PROCESSES.append(bridge_proc)
    time.sleep(1.5)

    # 2. Launch Electron
    print("[2/2] Launching Glassmorphic Electron Desktop Client...")
    npx_bin = shutil.which("npx") or "npx"
    electron_proc = subprocess.Popen(
        f"{npx_bin} electron dist-electron/main/main.js",
        cwd=ELECTRON_APP_DIR,
        shell=True,
    )
    CHILD_PROCESSES.append(electron_proc)

    # Wait for electron to close
    try:
        electron_proc.wait()
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()


def launch_qt_mode():
    """Launches the native PyQt6 desktop application."""
    print("=" * 65)
    print("⚡ COGNITIVE AI — NATIVE PyQt6 DESKTOP APPLICATION")
    print("   Platform: Windows | Framework: PyQt6 Modern Dark")
    print("=" * 65)
    os.chdir(WORKSPACE_ROOT)
    cmd = [sys.executable, QT_MAIN_PY]
    proc = subprocess.Popen(cmd)
    CHILD_PROCESSES.append(proc)
    try:
        proc.wait()
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()


def main():
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    parser = argparse.ArgumentParser(description="Cognitive AI Master Launcher")
    parser.add_argument("--electron", action="store_true", help="Force launch Electron Desktop UI")
    parser.add_argument("--qt", action="store_true", help="Force launch Native PyQt6 UI")
    parser.add_argument("--bridge-only", action="store_true", help="Run only the Python API Bridge")

    args = parser.parse_args()

    if args.bridge_only:
        print("[Cognitive AI] Running bridge server standalone...")
        subprocess.run([sys.executable, BRIDGE_SERVER_PY], cwd=WORKSPACE_ROOT)
        return

    if args.qt:
        launch_qt_mode()
        return

    if args.electron:
        launch_electron_mode()
        return

    # Auto-detection: prefer Electron if built and available, otherwise fallback to PyQt6
    if check_node_electron_ready():
        launch_electron_mode()
    else:
        print("[Notice] Electron runtime not built or Node not found. Falling back to native PyQt6...")
        launch_qt_mode()


if __name__ == "__main__":
    main()
