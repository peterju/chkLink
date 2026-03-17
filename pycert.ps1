$ErrorActionPreference = 'Stop'

$signToolPath = '..\SignTool\x64\signtool.exe'
# 請使用自然人憑證上的「簽章憑證」thumbprint，不要誤用加密憑證。
# 若換卡、補發憑證，或在不同電腦上操作，請先重新確認目前可用的簽章憑證 thumbprint。
# 這裡的 $thumbprint 指的是簽章憑證的 SHA-1 雜湊值，也就是 certutil -scinfo 顯示的「Cert 雜湊(sha1)」。
# 若不知道如何查詢，請參考 README 的「如何判斷應該用哪張自然人憑證」章節。
$thumbprint = '63dc665f1795f66146cf1096d956fd797060af24'
# 檔案摘要演算法請以實測可成功的值為準；本環境目前使用 SHA1, 若不行則試試 SHA256。
$fileDigestAlgorithm = 'SHA1'
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
& $signToolPath sign /sha1 $thumbprint /fd $fileDigestAlgorithm /t $timestampUrl /v $targetFile

if ($LASTEXITCODE -ne 0) {
    Write-Host '[錯誤] SignTool 執行失敗，請確認憑證、thumbprint 與 signtool.exe 路徑設定。' -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host '[完成] chklink.exe 已完成簽章。' -ForegroundColor Green
