$ErrorActionPreference = 'Stop'

$signToolPath = '..\SignTool\x64\signtool.exe'
# Use the signing certificate thumbprint from the citizen digital certificate.
# Do not use the encryption certificate thumbprint by mistake.
# The thumbprint here is the SHA-1 certificate hash shown by `certutil -scinfo`.
# See README for the lookup steps.
$thumbprint = '63dc665f1795f66146cf1096d956fd797060af24'
# Keep the digest algorithm aligned with the value that actually works in this environment.
$fileDigestAlgorithm = 'SHA1'
$timestampUrl = 'http://timestamp.sectigo.com'
$targetCandidates = @(
    'out\chklink.dist\chklink.exe',
    'out\chklink.exe'
)
$targetFile = $targetCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if (-not (Test-Path -LiteralPath $signToolPath)) {
    Write-Host '[ERROR] signtool.exe was not found. Install Windows SDK or update $signToolPath in pycert.ps1.' -ForegroundColor Red
    exit 1
}

if ([string]::IsNullOrWhiteSpace($targetFile)) {
    Write-Host '[ERROR] No chklink.exe was found to sign. Run make.cmd or make0.cmd first.' -ForegroundColor Red
    exit 1
}

Write-Host "Signing $targetFile ..."
& $signToolPath sign /sha1 $thumbprint /fd $fileDigestAlgorithm /t $timestampUrl /v $targetFile

if ($LASTEXITCODE -ne 0) {
    Write-Host '[ERROR] SignTool failed. Check the certificate, thumbprint, and signtool.exe path.' -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "[DONE] Signed $targetFile ." -ForegroundColor Green
