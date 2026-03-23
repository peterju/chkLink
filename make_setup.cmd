@echo off
chcp 950 >nul
setlocal
cd /d "%~dp0"

for /f "delims=" %%i in ('python -c "import chklink_config as c; print(c.DEFAULT_APP_VERSION)"') do set "APP_VERSION=%%i"
if not defined APP_VERSION set "APP_VERSION=(未知版本)"

echo [資訊] make_setup.cmd 的作用：根據目前版本產生 installer。
echo [資訊] 這是第 2 階段，不會預設執行簽章。
echo [資訊] 若需要正式簽章，請在完成後另外執行 make_sign.cmd。
echo [資訊] 開始執行 build_installer.ps1...
powershell -ExecutionPolicy Bypass -File ".\build_installer.ps1"
chcp 950 >nul
if errorlevel 1 (
    echo [錯誤] build_installer.ps1 執行失敗。
    exit /b 1
)

echo [完成] 安裝檔已產生完成。
echo [完成] 請至 installer\%APP_VERSION%\chklink_setup.exe 取得安裝程式。
echo [完成] 請至 installer\%APP_VERSION%\RemoteVersion.yaml 取得版本檔。
echo [完成] 若需要簽章，請再執行 make_sign.cmd。
exit /b 0