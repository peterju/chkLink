@echo off
chcp 950 >nul
setlocal
cd /d "%~dp0"

echo [資訊] make_sign_app.cmd 的作用：對 GUI 與 CLI 執行檔進行加簽。
echo [資訊] 這是第 2 步，請先確認 make_exec.cmd 已完成。
echo [資訊] 準備簽章：
echo [資訊]   1. out\chklink.dist\chklink.exe
echo [資訊]   2. out\chklink_cli.exe
echo [資訊] 開始執行 sign_files.ps1 -Target app ...
powershell -ExecutionPolicy Bypass -File ".\sign_files.ps1" -Target app
chcp 950 >nul
if errorlevel 1 (
    echo [錯誤] GUI / CLI 加簽失敗。
    exit /b 1
)

echo [完成] GUI / CLI 已完成加簽。
exit /b 0