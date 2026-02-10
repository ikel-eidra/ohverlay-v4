# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for ZenFish Overlay.
Produces a single-folder portable build - no admin install needed.
"""

import sys
import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config', 'config'),
    ],
    hiddenimports=[
        'PySide6.QtWidgets',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'numpy',
        'loguru',
        'requests',
        'engine.brain',
        'engine.school',
        'engine.aquarium',
        'engine.sanctuary',
        'engine.perlin',
        'engine.llm_brain',
        'ui.skin',
        'ui.tetra_skin',
        'ui.discus_skin',
        'ui.bubbles',
        'ui.tray',
        'modules.health',
        'modules.love_notes',
        'modules.schedule',
        'modules.news',
        'modules.telegram_bridge',
        'modules.webhook_server',
        'utils.logger',
        'config.settings',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'PIL',
        'cv2',
        'IPython',
        'jupyter',
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
    [],
    exclude_binaries=True,
    name='ZenFish',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,      # No console window - pure overlay
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ZenFish',
)
