# -*- mode: python ; coding: utf-8 -*-
"""
OHVERLAY v4.0 - PyInstaller Spec File
Builds a portable Windows executable (no installation needed)
By Futol Ethical Technology Ecosystems
"""

import sys
import os

block_cipher = None

# Collect all Python source files for the application
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include config directory
        ('config', 'config'),
        # Include LUMEX package
        ('LUMEX_PACKAGE', 'LUMEX_PACKAGE'),
        # Include HTML overlays
        ('chatbox-overlay.html', '.'),
        ('sticky-note-overlay.html', '.'),
        ('fairy-dandelion.html', '.'),
        ('manta-ray-overlay.html', '.'),
        ('aurora.html', '.'),
        ('exam-reviewer-overlay.html', '.'),
        ('ghost-woman-overlay.html', '.'),
        # Include version info
        ('windows_file_version_info.txt', '.'),
    ],
    hiddenimports=[
        # Core UI skins
        'ui.skin',
        'ui.skin_realistic',
        'ui.jellyfish_skin',
        'ui.jellyfish_cyan_skin',
        'ui.jellyfish_iridescent_skin',
        'ui.tetra_skin',
        'ui.discus_skin',
        'ui.geometric_skin',
        'ui.energy_orb_skin',
        'ui.holographic_skin',
        'ui.airplane_skin',
        'ui.train_skin',
        'ui.submarine_skin',
        'ui.balloon_skin',
        'ui.bubbles',
        'ui.tray',
        # Engine modules
        'engine.brain',
        'engine.brain_enhanced',
        'engine.llm_brain',
        'engine.aquarium',
        'engine.sanctuary',
        'engine.school',
        'engine.perlin',
        # Feature modules
        'modules.health',
        'modules.love_notes',
        'modules.schedule',
        'modules.news',
        'modules.telegram_bridge',
        'modules.webhook_server',
        'modules.updater',
        'modules.blue_memory',
        'modules.blue_realtime',
        'modules.blue_vision',
        'modules.blue_vision_bridge',
        # Config
        'config.settings',
        # Utils
        'utils.logger',
        # PySide6 plugins
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtNetwork',
        # Third-party
        'numpy',
        'loguru',
        'pynput',
        'pynput.keyboard',
        'pynput.keyboard._win32',
        'pynput.mouse',
        'pynput.mouse._win32',
        'anthropic',
        'openai',
        'requests',
        'pydantic',
        'PIL',
        'psutil',
        'flask',
        'dotenv',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude dev/test dependencies to reduce size
        'pytest',
        'pytest_qt',
        'hypothesis',
        'black',
        'flake8',
        'mypy',
        'pylint',
        'isort',
        'sphinx',
        'jupyter',
        'IPython',
        'notebook',
        'matplotlib',
        'tkinter',
        '_tkinter',
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
    name='Ohverlay',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window - pure GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='windows_file_version_info.txt',
    icon=None,  # Add icon path here if you have one: icon='assets/ohverlay.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Ohverlay',
)
