; ============================================================
; OHVERLAY v4.0 - Inno Setup Installer Script
; By Futol Ethical Technology Ecosystems
; Creates a proper Windows installer (.exe setup wizard)
;
; Prerequisites:
;   1. First run build_windows.bat to create dist\Ohverlay\
;   2. Install Inno Setup from https://jrsoftware.org/isinfo.php
;   3. Open this file in Inno Setup Compiler and click Build
;   OR run: build_installer.bat (does steps 2-3 automatically)
; ============================================================

#define MyAppName "Ohverlay"
#define MyAppVersion "4.0.0"
#define MyAppPublisher "Futol Ethical Technology Ecosystems"
#define MyAppURL "https://github.com/michaelfutol/ohverlay"
#define MyAppExeName "Ohverlay.exe"

[Setup]
AppId={{B8E3F2A1-5C7D-4E9F-A1B2-3C4D5E6F7A8B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
; No admin required - installs to user's AppData by default
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=commandline
UsedUserAreasWarning=no
OutputDir=installer_output
OutputBaseFilename=Ohverlay-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; Uncomment and set path when you have an icon:
; SetupIconFile=assets\ohverlay.ico
; UninstallDisplayIcon={app}\{#MyAppExeName}
DisableProgramGroupPage=yes
LicenseFile=LICENSE
InfoBeforeFile=INSTALL.md
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupentry"; Description: "Start Ohverlay when Windows starts"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
; Include the entire PyInstaller output folder
Source: "dist\Ohverlay\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Optional startup entry
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: startupentry

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userprofile}\.ohverlay"
Type: filesandordirs; Name: "{userprofile}\.zenfish"
Type: filesandordirs; Name: "{localappdata}\Ohverlay"
Type: filesandordirs; Name: "{userappdata}\Ohverlay"
