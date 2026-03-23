$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$configPath = Join-Path $projectRoot 'chklink_config.py'
$issPath = Join-Path $projectRoot 'installer_template.iss'
$distDir = Join-Path $projectRoot 'out\chklink.dist'
$dataDir = Join-Path $projectRoot 'data'
$localVersionPath = Join-Path $projectRoot 'data\LocalVersion.yaml'
$updateCmdPath = Join-Path $projectRoot 'data\update.cmd'
$iconPath = Join-Path $projectRoot 'chklink.ico'
$installerDir = Join-Path $projectRoot 'installer'
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    $pythonExe = 'python'
}

if (-not (Test-Path -LiteralPath $configPath)) {
    Write-Host '[ERROR] chklink_config.py not found.' -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath $distDir)) {
    Write-Host '[ERROR] out\chklink.dist not found. Run make.cmd first.' -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath $localVersionPath)) {
    Write-Host '[ERROR] data\LocalVersion.yaml not found. Run make.cmd first.' -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath $updateCmdPath)) {
    Write-Host '[INFO] data\update.cmd not found. Creating it now...'
    & $pythonExe -c "import chklink_config as c; c.ensure_update_cmd()"
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $updateCmdPath)) {
        Write-Host '[ERROR] data\update.cmd not found.' -ForegroundColor Red
        exit 1
    }
}

if (-not (Test-Path -LiteralPath $iconPath)) {
    Write-Host '[ERROR] chklink.ico not found.' -ForegroundColor Red
    exit 1
}

$appInfoJson = & $pythonExe -c "import json, chklink_config as c; print(json.dumps({'app_name': c.APP_NAME, 'app_display_name': c.APP_DISPLAY_NAME, 'app_version': c.DEFAULT_APP_VERSION}))"
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($appInfoJson)) {
    Write-Host '[ERROR] Unable to read application metadata from chklink_config.py.' -ForegroundColor Red
    exit 1
}

$appInfo = $appInfoJson | ConvertFrom-Json
$appName = [string]$appInfo.app_name
$appDisplayName = [string]$appInfo.app_display_name
$appVersion = [string]$appInfo.app_version

if ([string]::IsNullOrWhiteSpace($appName)) {
    Write-Host '[ERROR] APP_NAME is empty.' -ForegroundColor Red
    exit 1
}

if ([string]::IsNullOrWhiteSpace($appDisplayName)) {
    Write-Host '[ERROR] APP_DISPLAY_NAME is empty.' -ForegroundColor Red
    exit 1
}

if ([string]::IsNullOrWhiteSpace($appVersion)) {
    Write-Host '[ERROR] DEFAULT_APP_VERSION is empty.' -ForegroundColor Red
    exit 1
}

$innoCandidates = @(
    'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',
    'C:\Program Files\Inno Setup 6\ISCC.exe'
)
$isccExe = $innoCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if ([string]::IsNullOrWhiteSpace($isccExe)) {
    Write-Host '[ERROR] ISCC.exe not found. Install Inno Setup 6 first.' -ForegroundColor Red
    exit 1
}

$languageFile = Join-Path (Split-Path -Parent $isccExe) 'Languages\ChineseTraditional.isl'
if (-not (Test-Path -LiteralPath $languageFile)) {
    Write-Host '[ERROR] ChineseTraditional.isl not found. Put it under Inno Setup 6\Languages first.' -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath $installerDir)) {
    New-Item -ItemType Directory -Path $installerDir | Out-Null
}

$issContent = @"
#define MyAppName "$appName"
#define MyAppDisplayName "$appDisplayName"
#define MyAppVersion "$appVersion"
#define MyAppPublisher "$appName"
#define MyAppExeName "chklink.exe"
#define MyAppDistDir "$($distDir -replace '\\','\\')"
#define MyAppLocalVersion "$($localVersionPath -replace '\\','\\')"
#define MyAppUpdateCmd "$($updateCmdPath -replace '\\','\\')"

[Setup]
AppId={{A1E42E19-0B41-4B4D-BF51-6DDE2911A0E1}
AppName={#MyAppDisplayName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppDisplayName}
OutputDir=$($installerDir -replace '\\','\\')
OutputBaseFilename=chklink_setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=$($iconPath -replace '\\','\\')
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
"@

$utf8Bom = New-Object System.Text.UTF8Encoding($true)
[System.IO.File]::WriteAllText($issPath, $issContent.Replace("`n", "`r`n"), $utf8Bom)

Write-Host 'Compiling setup with Inno Setup...'
& $isccExe $issPath

if ($LASTEXITCODE -ne 0) {
    Write-Host '[ERROR] Inno Setup compilation failed.' -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host '[DONE] setup.exe has been created under installer\.' -ForegroundColor Green
