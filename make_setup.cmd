@echo off
chcp 950 >nul
setlocal
cd /d "%~dp0"

for /f "delims=" %%i in ('python -c "import chklink_config as c; print(c.DEFAULT_APP_VERSION)"') do set "APP_VERSION=%%i"
if not defined APP_VERSION set "APP_VERSION=(未知版本)"

echo [資訊] make_setup.cmd 的作用：將目前編譯產物封裝為 installer。
echo [資訊] 這是第 3 步，請先確認 make_exec.cmd 已完成；若需要，請先執行 make_sign_app.cmd。
echo [資訊] 開始執行 build_installer.ps1...
powershell -ExecutionPolicy Bypass -File ".\build_installer.ps1"
chcp 950 >nul
if errorlevel 1 (
    echo [錯誤] build_installer.ps1 執行失敗。
    exit /b 1
)

echo [完成] 已產生 installer\%APP_VERSION%\chklink_setup.exe
echo [完成] 已產生 installer\%APP_VERSION%\RemoteVersion.yaml
echo [完成] 若需要對 installer 加簽，請再執行 make_sign_setup.cmd。
exit /b 0