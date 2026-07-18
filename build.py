#!/usr/bin/env python3
"""
Ohverlay 0.1.0-dev Build Script
By FutolTech

Usage:
    python build.py              # Build portable app
    python build.py --installer  # Build installer (Windows only, needs Inno Setup)
    python build.py --zip        # Build portable ZIP

Requirements:
    pip install -r requirements.txt
"""

import subprocess
import sys
import os
import shutil
import platform
from pathlib import Path


def run(cmd, **kwargs):
    """Run a command and print output."""
    print(f'  > {cmd}')
    result = subprocess.run(cmd, shell=True, **kwargs)
    if result.returncode != 0:
        print(f'  [ERROR] Command failed with exit code {result.returncode}')
    return result.returncode


def check_python():
    """Verify Python is available."""
    print('[1/4] Checking Python...')
    ver = sys.version_info
    print(f'  Python {ver.major}.{ver.minor}.{ver.micro}')
    if ver.major < 3 or (ver.major == 3 and ver.minor < 10):
        print('  [WARNING] Python 3.10+ recommended')
    return True


def install_deps():
    """Verify build dependencies."""
    print('[2/4] Verifying dependencies...')
    try:
        import PyInstaller
    except ImportError:
        print('  [ERROR] PyInstaller not found. Please install build requirements:')
        print('  pip install -r requirements.txt')
        sys.exit(1)


def build_app():
    """Build the portable application."""
    print('[3/4] Building Ohverlay with PyInstaller...')
    print('  (This may take 2-5 minutes)')

    # Clean previous build
    for d in ['build', 'dist']:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)

    ret = run(f'{sys.executable} -m PyInstaller ohverlay.spec --noconfirm --clean')
    if ret != 0:
        print('\n  [ERROR] Build failed! Check errors above.')
        return False

    print('\n[4/4] Build complete!')
    print(f'\n  Location: dist/Ohverlay/')

    system = platform.system()
    if system == 'Windows':
        print('  Run:      dist\\Ohverlay\\Ohverlay.exe')
    else:
        print('  Run:      dist/Ohverlay/Ohverlay')

    return True


def build_zip():
    """Create a portable ZIP."""
    dist_dir = Path('dist/Ohverlay')
    if not dist_dir.exists():
        print('Building app first...')
        if not build_app():
            return False

    print('Creating portable ZIP...')
    output_dir = Path('installer_output')
    output_dir.mkdir(exist_ok=True)

    shutil.make_archive(
        str(output_dir / 'Ohverlay-Portable'),
        'zip',
        'dist',
        'Ohverlay'
    )
    print(f'\n  ZIP created: installer_output/Ohverlay-Portable.zip')
    return True


def build_installer():
    """Build Windows installer using Inno Setup."""
    if platform.system() != 'Windows':
        print('[ERROR] Installer build only available on Windows.')
        print('  Use the portable ZIP instead: python build.py --zip')
        return False

    dist_dir = Path('dist/Ohverlay')
    if not dist_dir.exists():
        print('Building app first...')
        if not build_app():
            return False

    # Find Inno Setup
    iscc_paths = [
        os.path.expandvars(r'%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe'),
        os.path.expandvars(r'%ProgramFiles%\Inno Setup 6\ISCC.exe'),
        os.path.expandvars(r'%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe'),
    ]

    iscc = None
    for p in iscc_paths:
        if os.path.exists(p):
            iscc = p
            break

    if not iscc:
        print('[ERROR] Inno Setup not found.')
        print('  Download free from: https://jrsoftware.org/isdl.php')
        return False

    print(f'  Found Inno Setup: {iscc}')
    ret = run(f'"{iscc}" installer.iss')
    if ret == 0:
        print('\n  Installer created: installer_output/Ohverlay-Setup.exe')
    return ret == 0


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print()
    print('  =============================================')
    print('   OHVERLAY 0.1.0-dev — Build System')
    print('   FutolTech')
    print('  =============================================')
    print()

    args = sys.argv[1:]

    check_python()
    install_deps()

    if '--installer' in args:
        build_installer()
    elif '--zip' in args:
        build_zip()
    else:
        if build_app():
            print('\n  Next steps:')
            print('    python build.py --zip        Create portable ZIP')
            if platform.system() == 'Windows':
                print('    python build.py --installer  Create Windows installer')


if __name__ == '__main__':
    main()
