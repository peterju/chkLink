$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$configPath = Join-Path $projectRoot 'chklink_config.py'
$issTemplatePath = Join-Path $projectRoot 'installer_template.iss'
$distDir = Join-Path $projectRoot 'out\chklink.dist'
$cliExePath = Join-Path $projectRoot 'out\chklink_cli.exe'
$dataDir = Join-Path $projectRoot 'data'
$localVersionPath = Join-Path $projectRoot 'data\LocalVersion.yaml'
$updateCmdPath = Join-Path $projectRoot 'data\update.cmd'
$iconPath = Join-Path $projectRoot 'chklink.ico'
$installerRootDir = Join-Path $projectRoot 'installer'
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    $pythonExe = 'python'
}

if (-not (Test-Path -LiteralPath $configPath)) {
    Write-Host '[ERROR] chklink_config.py not found.' -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath $issTemplatePath)) {
    Write-Host '[ERROR] installer_template.iss not found.' -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath $distDir)) {
    Write-Host '[ERROR] out\chklink.dist not found. Run make.cmd first.' -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath $cliExePath)) {
    Write-Host '[ERROR] out\chklink_cli.exe not found. Run make.cmd first.' -ForegroundColor Red
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

$installerDir = Join-Path $installerRootDir $appVersion
if (-not (Test-Path -LiteralPath $installerDir)) {
    New-Item -ItemType Directory -Path $installerDir -Force | Out-Null
}
$generatedIssPath = Join-Path $installerRootDir 'build.iss'
$issTemplateContent = [System.IO.File]::ReadAllText($issTemplatePath)
$issContent = $issTemplateContent
$replacements = @{
    '{{APP_NAME}}' = $appName
    '{{APP_DISPLAY_NAME}}' = $appDisplayName
    '{{APP_VERSION}}' = $appVersion
    '{{APP_PUBLISHER}}' = $appName
    '{{DIST_DIR}}' = ($distDir -replace '\\','\\')
    '{{CLI_EXE_PATH}}' = ($cliExePath -replace '\\','\\')
    '{{LOCAL_VERSION_PATH}}' = ($localVersionPath -replace '\\','\\')
    '{{UPDATE_CMD_PATH}}' = ($updateCmdPath -replace '\\','\\')
    '{{OUTPUT_DIR}}' = ($installerDir -replace '\\','\\')
    '{{ICON_PATH}}' = ($iconPath -replace '\\','\\')
}
foreach ($entry in $replacements.GetEnumerator()) {
    $issContent = $issContent.Replace($entry.Key, $entry.Value)
}

$utf8Bom = New-Object System.Text.UTF8Encoding($true)
[System.IO.File]::WriteAllText($generatedIssPath, $issContent.Replace("`n", "`r`n"), $utf8Bom)

Write-Host 'Compiling setup with Inno Setup...'
& $isccExe $generatedIssPath

if ($LASTEXITCODE -ne 0) {
    Write-Host '[ERROR] Inno Setup compilation failed.' -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "[DONE] setup.exe has been created under installer\$appVersion\." -ForegroundColor Green
