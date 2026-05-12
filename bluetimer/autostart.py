from __future__ import annotations

import sys
from pathlib import Path

APP_NAME = "BlueTimer"
REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def launcher_path() -> str:
    exe_dir = Path(sys.executable).resolve().parent
    candidate = exe_dir / "Launcher.exe"
    if candidate.exists():
        return str(candidate)
    return str(exe_dir / "Launcher.exe")


def set_autostart(enabled: bool) -> tuple[bool, str]:
    if sys.platform != "win32":
        return False, "开机自启仅支持 Windows"
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, launcher_path())
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
        return True, "已更新开机自启"
    except Exception as exc:
        return False, str(exc)
