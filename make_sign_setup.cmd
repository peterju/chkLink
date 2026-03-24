@echo off
chcp 950 >nul
setlocal
cd /d "%~dp0"

for /f "delims=" %%i in ('python -c "import chklink_config as c; print(c.DEFAULT_APP_VERSION)"') do set "APP_VERSION=%%i"
if not defined APP_VERSION set "APP_VERSION=(未知版本)"

echo [資訊] make_sign_setup.cmd 的作用：對 installer 進行加簽。
echo [資訊] 這是第 4 步，請先確認 make_setup.cmd 已完成。
echo [資訊] 準備簽章：
echo [資訊]   installer\%APP_VERSION%\chklink_setup.exe
echo [資訊] 開始執行 sign_files.ps1 -Target setup ...
powershell -ExecutionPolicy Bypass -File ".\sign_files.ps1" -Target setup
chcp 950 >nul
if errorlevel 1 (
    echo [錯誤] installer 加簽失敗。
    exit /b 1
)

echo [完成] installer 已完成加簽。
exit /b 0