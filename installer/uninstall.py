from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import sys
import time
import winreg
from pathlib import Path


APP_NAME = "BlueTimer"


def message(title: str, body: str, icon: int = 0x40) -> None:
    ctypes.windll.user32.MessageBoxW(None, body, title, icon)


def remove_file(path: Path) -> None:
    try:
        if path.exists():
            path.unlink()
    except Exception:
        pass


def unregister_autostart() -> None:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as key:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
    except Exception:
        pass


def uninstall() -> None:
    result = ctypes.windll.user32.MessageBoxW(None, "确定要卸载 BlueTimer 吗？", "卸载 BlueTimer", 0x24)
    if result != 6:
        return

    subprocess.run(["taskkill", "/IM", "BlueTimer.exe", "/F"], capture_output=True, creationflags=0x08000000)
    time.sleep(0.5)
    unregister_autostart()

    install_dir = Path(sys.executable).resolve().parent
    start_menu = Path(os.environ.get("ProgramData", "C:/ProgramData")) / "Microsoft/Windows/Start Menu/Programs" / APP_NAME
    desktop = Path(os.environ.get("Public", "C:/Users/Public")) / "Desktop"

    remove_file(desktop / "BlueTimer.lnk")
    if start_menu.exists():
        shutil.rmtree(start_menu, ignore_errors=True)

    try:
        winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\BlueTimer")
    except Exception:
        pass

    cleanup_script = Path(os.environ.get("TEMP", str(Path.home()))) / "BlueTimer_cleanup.cmd"
    cleanup_script.write_text(
        f"""@echo off
timeout /t 2 /nobreak >nul
rmdir /s /q "{install_dir}"
del "%~f0"
""",
        encoding="gbk",
    )
    subprocess.Popen(["cmd", "/c", str(cleanup_script)], creationflags=0x08000000)
    message("BlueTimer 已卸载", "BlueTimer 已卸载。用户配置和日志会保留在 AppData 中。")


if __name__ == "__main__":
    try:
        uninstall()
    except Exception as exc:
        message("BlueTimer 卸载失败", str(exc), 0x10)
        raise
