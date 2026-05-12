from __future__ import annotations

import ctypes
import os
import sys
import winreg


APP_NAME = "BlueTimer"
REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def main_exe() -> str:
    return os.path.join(os.path.dirname(sys.executable), "BlueTimer.exe")


def register_autostart() -> None:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, sys.executable)


def unregister_autostart() -> None:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE) as key:
        try:
            winreg.DeleteValue(key, APP_NAME)
        except FileNotFoundError:
            pass


def launch_main() -> None:
    ctypes.windll.shell32.ShellExecuteW(None, "runas", main_exe(), "", None, 1)


if __name__ == "__main__":
    launch_main()
