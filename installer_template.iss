#define MyAppName "{{APP_NAME}}"
#define MyAppDisplayName "{{APP_DISPLAY_NAME}}"
#define MyAppVersion "{{APP_VERSION}}"
#define MyAppPublisher "{{APP_PUBLISHER}}"
#define MyAppExeName "chklink.exe"
#define MyAppCliExeName "chklink_cli.exe"
#define MyAppDistDir "{{DIST_DIR}}"
#define MyAppCliExePath "{{CLI_EXE_PATH}}"
#define MyAppUpdateCmd "{{UPDATE_CMD_PATH}}"
#define MyAppOutputDir "{{OUTPUT_DIR}}"
#define MySetupIconFile "{{ICON_PATH}}"

[Setup]
AppId={{A1E42E19-0B41-4B4D-BF51-6DDE2911A0E1}
AppName={#MyAppDisplayName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppDisplayName}
OutputDir={#MyAppOutputDir}
OutputBaseFilename=chklink_setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile={#MySetupIconFile}
DisableProgramGroupPage=yes

[Languages]
Name: "chinesetraditional"; MessagesFile: "compiler:Languages\ChineseTraditional.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#MyAppDistDir}\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
Source: "{#MyAppCliExePath}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppUpdateCmd}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\{#MyAppDisplayName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{group}\{#MyAppDisplayName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppDisplayName}}"; Flags: nowait postinstall skipifsilent
