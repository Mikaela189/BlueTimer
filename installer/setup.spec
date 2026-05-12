# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ["setup.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("../dist/BlueTimer.exe", "."),
        ("../dist/Launcher.exe", "."),
        ("dist/BlueTimer_Uninstall.exe", "."),
    ],
    hiddenimports=["win32com.client"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="BlueTimer_Setup_v0.1.0",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    uac_admin=True,
)
