$ErrorActionPreference = 'Stop'

$signToolPath = '..\SignTool\x64\signtool.exe'
$thumbprint = '63dc665f1795f66146cf1096d956fd797060af24'
$timestampUrl = 'http://timestamp.sectigo.com'
$targetFile = 'out\chklink.exe'

if (-not (Test-Path -LiteralPath $signToolPath)) {
    Write-Host '[錯誤] 找不到 signtool.exe，請先安裝 Windows SDK，或修改 pycert.ps1 內的 $signToolPath。' -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath $targetFile)) {
    Write-Host '[錯誤] 找不到 out\chklink.exe，請先執行 make.cmd 產生執行檔。' -ForegroundColor Red
    exit 1
}

Write-Host '開始對 out\chklink.exe 進行簽章...'
& $signToolPath sign /sha1 $thumbprint /fd SHA1 /t $timestampUrl /v $targetFile

if ($LASTEXITCODE -ne 0) {
    Write-Host '[錯誤] SignTool 執行失敗，請確認憑證、thumbprint 與 signtool.exe 路徑設定。' -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host '[完成] chklink.exe 已完成簽章。' -ForegroundColor Green
