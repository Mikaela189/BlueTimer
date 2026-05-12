from __future__ import annotations

import ctypes
import os
import shutil
import sys
import winreg
from pathlib import Path


APP_NAME = "BlueTimer"
APP_VERSION = "0.1.0"
PUBLISHER = "BlueTimer"


def resource_path(name: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / name


def message(title: str, body: str, icon: int = 0x40) -> None:
    ctypes.windll.user32.MessageBoxW(None, body, title, icon)


def create_shortcut(path: Path, target: Path, working_dir: Path, description: str = "") -> None:
    import win32com.client

    path.parent.mkdir(parents=True, exist_ok=True)
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(str(path))
    shortcut.TargetPath = str(target)
    shortcut.WorkingDirectory = str(working_dir)
    shortcut.Description = description
    shortcut.IconLocation = str(target)
    shortcut.Save()


def install() -> None:
    install_dir = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / APP_NAME
    start_menu = Path(os.environ.get("ProgramData", "C:/ProgramData")) / "Microsoft/Windows/Start Menu/Programs" / APP_NAME
    desktop = Path(os.environ.get("Public", "C:/Users/Public")) / "Desktop"

    install_dir.mkdir(parents=True, exist_ok=True)
    for filename in ("BlueTimer.exe", "Launcher.exe", "BlueTimer_Uninstall.exe"):
        shutil.copy2(resource_path(filename), install_dir / filename)

    create_shortcut(start_menu / "BlueTimer.lnk", install_dir / "BlueTimer.exe", install_dir, "启动 BlueTimer")
    create_shortcut(start_menu / "卸载 BlueTimer.lnk", install_dir / "BlueTimer_Uninstall.exe", install_dir, "卸载 BlueTimer")
    create_shortcut(desktop / "BlueTimer.lnk", install_dir / "BlueTimer.exe", install_dir, "启动 BlueTimer")

    uninstall_key = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\BlueTimer"
    with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, uninstall_key, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, PUBLISHER)
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
        winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(install_dir / "BlueTimer.exe"))
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, str(install_dir / "BlueTimer_Uninstall.exe"))
        winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)

    message("BlueTimer 安装完成", "BlueTimer 已安装完成，桌面和开始菜单中已创建快捷方式。")
    ctypes.windll.shell32.ShellExecuteW(None, "open", str(install_dir / "BlueTimer.exe"), "", str(install_dir), 1)


if __name__ == "__main__":
    try:
        install()
    except Exception as exc:
        message("BlueTimer 安装失败", str(exc), 0x10)
        raise
