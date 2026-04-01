# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for NetShare standalone .exe
# Developed by Futol Ethical Technology Ecosystems
# For: Sarah Attaqnia Contracting Company
#
# Build:   pyinstaller netshare.spec --noconfirm
# Output:  dist\NetShare\NetShare.exe
#
# Requirements:
#   pip install pyinstaller PySide6 loguru
#
# No admin rights, no console window, no network ports opened.

block_cipher = None

a = Analysis(
    ['netshare_main.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[
        # PySide6 core
        'PySide6.QtWidgets',
        'PySide6.QtGui',
        'PySide6.QtCore',
        'PySide6.QtNetwork',
        # NetShare modules
        'netshare_settings',
        'netshare_overlay',
        'netshare_card',
        'netshare_console',
        'netshare_tray',
        # Shared modules
        'modules.network_folder_watcher',
        'modules.network_notifier',
        # Utilities
        'utils.logger',
        'loguru',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # ---- All Ohverlay creature / fish skins (not needed) ----
        'ui',
        'engine',
        # ---- AI / comms modules (not needed) ----
        'modules.health',
        'modules.love_notes',
        'modules.news',
        'modules.schedule',
        'modules.telegram_bridge',
        'modules.webhook_server',
        'modules.blue_vision',
        'modules.blue_vision_bridge',
        'modules.updater',
        'modules.factory_client',
        # ---- Heavy third-party libraries (not used) ----
        'openai',
        'anthropic',
        'pdfplumber',
        'groq',
        'numpy',
        'PIL',
        'cv2',
        'scipy',
        'matplotlib',
        'pandas',
        'IPython',
        'notebook',
        'tk',
        'tkinter',
        'wx',
        'PyQt5',
        'PyQt6',
    ],
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
    name='NetShare',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # console=False  → no black cmd window; runs silently in system tray
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version_info={
        'FileVersion':     '1, 0, 0, 0',
        'ProductVersion':  '1, 0, 0, 0',
        'CompanyName':     'Futol Ethical Technology Ecosystems',
        'FileDescription': 'NetShare Network Folder Notification Overlay',
        'ProductName':     'NetShare',
        'LegalCopyright':  'Futol Ethical Technology Ecosystems',
        'OriginalFilename':'NetShare.exe',
    } if False else None,   # set to True once you have a version_info.txt
    # icon='netshare_icon.ico',  # uncomment + add .ico file for a custom icon
)
