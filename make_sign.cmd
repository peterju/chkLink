@echo off
chcp 950 >nul
setlocal
cd /d "%~dp0"

for /f "delims=" %%i in ('python -c "import chklink_config as c; print(c.DEFAULT_APP_VERSION)"') do set "APP_VERSION=%%i"
if not defined APP_VERSION set "APP_VERSION=(未知版本)"

echo [資訊] make_sign.cmd 的作用：對 GUI / CLI / installer 進行正式簽章。
echo [資訊] 這是第 3 階段，請先確認 make.cmd 與 make_setup.cmd 都已完成。
echo [資訊] 準備簽章三個檔案：
echo [資訊]   1. out\chklink.dist\chklink.exe
echo [資訊]   2. out\chklink_cli.exe
echo [資訊]   3. installer\%APP_VERSION%\chklink_setup.exe
echo [資訊] 開始執行 pycert.ps1...
powershell -ExecutionPolicy Bypass -File ".\pycert.ps1"
chcp 950 >nul
if errorlevel 1 (
    echo [錯誤] pycert.ps1 執行失敗。
    exit /b 1
)

echo [完成] 三個檔案已完成簽章。
exit /b 0