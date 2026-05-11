# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Минимум скрытых импортов
hiddenimports = [
    'numpy',
    'scipy',
]

a = Analysis(
    ['dualsense-bridge.py'],
    pathex=[],
    binaries=[],
    datas=[('presets.py', '.')],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter.test'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DualSenseBridge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)
