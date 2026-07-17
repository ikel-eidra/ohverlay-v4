# Build and Release Workflows

## Verified Build Artifacts

Ohverlay provides two main types of builds through PyInstaller:
1. **Portable ZIP:** A standalone folder compressed into a `.zip` archive that can be extracted and run without installation.
2. **Standard Installer:** An Inno Setup compiler configuration (`installer.iss`) that creates a `.exe` installer.

## Build Requirements

- Python 3.11.9+
- `pip install -r requirements.txt` (including `pyinstaller`)
- [Inno Setup 6+](https://jrsoftware.org/isinfo.php) (Required for the `.exe` installer only)

## Execution Instructions

To generate the builds, run the automated script from the root directory:

```powershell
python build.py
```

Or you can use the batch script wrappers directly:
```powershell
# For the executable installer:
.\build_installer.bat

# For the portable zip:
.\build_portable_zip.bat
```

## Release Policy

- **Releases are generated from the `main` branch only.**
- **Version Numbering:** Ohverlay follows Semantic Versioning (SemVer). The version number belongs in Git tags (e.g., `v4.1.0`), GitHub Releases, changelogs, and installer metadata. It does not belong in the permanent repository name.
- **Verification:** Do not tag or publish a release until the complete release gate (tests pass, compile checks pass, artifacts are generated and verified) has passed.

### Future Infrastructure
- An automated GitHub Actions pipeline for CI/CD is planned.
- Checksums (SHA-256) will be generated and attached to all future GitHub Release assets for verification.
