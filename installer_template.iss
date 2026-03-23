#define MyAppName "chkLink"
#define MyAppDisplayName "網頁失效連結掃描工具"
#define MyAppVersion "1.4"
#define MyAppPublisher "chkLink"
#define MyAppExeName "chklink.exe"
#define MyAppDistDir "D:\\pyTest\\chkLink\\out\\chklink.dist"
#define MyAppLocalVersion "D:\\pyTest\\chkLink\\data\\LocalVersion.yaml"
#define MyAppUpdateCmd "D:\\pyTest\\chkLink\\data\\update.cmd"

[Setup]
AppId={{A1E42E19-0B41-4B4D-BF51-6DDE2911A0E1}
AppName={#MyAppDisplayName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppDisplayName}
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
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#MyAppDistDir}\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
Source: "{#MyAppLocalVersion}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppUpdateCmd}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autodesktop}\{#MyAppDisplayName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{group}\{#MyAppDisplayName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppDisplayName}}"; Flags: nowait postinstall skipifsilent