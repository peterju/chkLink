param(
    [ValidateSet('app', 'setup', 'all')]
    [string]$Target = 'all'
)

$ErrorActionPreference = 'Stop'

$signToolPath = '..\SignTool\x64\signtool.exe'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$configPath = Join-Path $projectRoot 'chklink_config.py'
# Use the signing certificate thumbprint from the citizen digital certificate.
# Do not use the encryption certificate thumbprint by mistake.
# The thumbprint here is the SHA-1 certificate hash shown by `certutil -scinfo`.
# See README for the lookup steps.
$thumbprint = '63dc665f1795f66146cf1096d956fd797060af24'
# Keep the digest algorithm aligned with the value that actually works in this environment.
$fileDigestAlgorithm = 'SHA1'
$timestampUrl = 'http://timestamp.sectigo.com'

if (-not (Test-Path -LiteralPath $configPath)) {
    Write-Host '[ERROR] chklink_config.py not found.' -ForegroundColor Red
    exit 1
}

$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    $pythonExe = 'python'
}

$appVersion = & $pythonExe -c "import chklink_config as c; print(c.DEFAULT_APP_VERSION)"
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($appVersion)) {
    Write-Host '[ERROR] Unable to read DEFAULT_APP_VERSION from chklink_config.py.' -ForegroundColor Red
    exit 1
}

switch ($Target) {
    'app' {
        $targetFiles = @(
            (Join-Path $projectRoot 'out\chklink.dist\chklink.exe'),
            (Join-Path $projectRoot 'out\chklink_cli.exe')
        )
    }
    'setup' {
        $targetFiles = @(
            (Join-Path $projectRoot ("installer\{0}\chklink_setup.exe" -f $appVersion))
        )
    }
    default {
        $targetFiles = @(
            (Join-Path $projectRoot 'out\chklink.dist\chklink.exe'),
            (Join-Path $projectRoot 'out\chklink_cli.exe'),
            (Join-Path $projectRoot ("installer\{0}\chklink_setup.exe" -f $appVersion))
        )
    }
}

if (-not (Test-Path -LiteralPath $signToolPath)) {
    Write-Host '[ERROR] signtool.exe was not found. Install Windows SDK or update $signToolPath in sign_files.ps1.' -ForegroundColor Red
    exit 1
}

foreach ($targetFile in $targetFiles) {
    if (-not (Test-Path -LiteralPath $targetFile)) {
        Write-Host "[ERROR] Target file not found: $targetFile" -ForegroundColor Red
        exit 1
    }
}

foreach ($targetFile in $targetFiles) {
    Write-Host "Signing $targetFile ..."
    & $signToolPath sign /sha1 $thumbprint /fd $fileDigestAlgorithm /t $timestampUrl /v $targetFile

    if ($LASTEXITCODE -ne 0) {
        Write-Host '[ERROR] SignTool failed. Check the certificate, thumbprint, and signtool.exe path.' -ForegroundColor Red
        exit $LASTEXITCODE
    }

    Write-Host "[DONE] Signed $targetFile ." -ForegroundColor Green
}
