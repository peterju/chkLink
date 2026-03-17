#define MyAppName "chkLink"
#define MyAppVersion "1.4"
#define MyAppPublisher "chkLink"
#define MyAppExeName "chklink.exe"
#define MyAppDistDir "D:\\pyTest\\chkLink\\out\\chklink.dist"
#define MyAppConfigDefault "D:\\pyTest\\chkLink\\config.yaml-default"
#define MyAppLocalVersion "D:\\pyTest\\chkLink\\LocalVersion.yaml"
#define MyAppUpdateCmd "D:\\pyTest\\chkLink\\update.cmd"

[Setup]
AppId={{A1E42E19-0B41-4B4D-BF51-6DDE2911A0E1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=D:\\pyTest\\chkLink\\installer
OutputBaseFilename=chklink_setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=D:\\pyTest\\chkLink\\chklink.ico
DisableProgramGroupPage=yes

[Languages]
Name: "chinesetraditional"; MessagesFile: "compiler:Languages\ChineseTraditional.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional tasks:"

[Files]
Source: "{#MyAppDistDir}\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
Source: "{#MyAppConfigDefault}"; DestDir: "{app}"; DestName: "config.yaml"; Flags: ignoreversion
Source: "{#MyAppLocalVersion}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppUpdateCmd}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent