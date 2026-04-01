# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for NetShare standalone .exe
# Build with:  pyinstaller netshare.spec --noconfirm
#
# Produces:  dist/NetShare/NetShare.exe
# No admin rights required. Runs silently in the system tray on Windows.

import os

block_cipher = None

a = Analysis(
    ['netshare_main.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PySide6.QtWidgets',
        'PySide6.QtGui',
        'PySide6.QtCore',
        'modules.network_folder_watcher',
        'modules.network_notifier',
        'ui.bubbles',
        'utils.logger',
        'netshare_settings',
        'netshare_overlay',
        'netshare_tray',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude all Ohverlay creature/fish UI (not needed for standalone)
        'ui.jellyfish_skin',
        'ui.jellyfish_cyan_skin',
        'ui.jellyfish_iridescent_skin',
        'ui.betta_skin',
        'ui.geometric_skin',
        'ui.energy_orb_skin',
        'ui.holographic_skin',
        'ui.airplane_skin',
        'ui.train_skin',
        'ui.submarine_skin',
        'ui.balloon_skin',
        'ui.tray',
        # Exclude heavy AI/comms modules
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
        'engine',
        'openai',
        'anthropic',
        'pdfplumber',
        'groq',
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
    # windowed=True hides the console window — runs silently in tray
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='netshare_icon.ico',  # uncomment and add icon file if desired
)
