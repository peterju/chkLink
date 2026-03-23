@echo off
chcp 950 >nul
setlocal
cd /d "%~dp0"

echo [資訊] 目前 make1.cmd 會先視需要執行 pycert.ps1，再轉呼叫 build_installer.ps1 產生安裝程式。
choice /C YN /N /T 10 /D N /M "是否先執行 pycert.ps1 進行簽章？(10 秒後預設為 N) "
if errorlevel 2 goto build_setup
if errorlevel 1 goto sign_first

:sign_first
echo [資訊] 開始執行 pycert.ps1...
powershell -ExecutionPolicy Bypass -File ".\pycert.ps1"
chcp 950 >nul
if errorlevel 1 (
    echo [錯誤] pycert.ps1 執行失敗。
    exit /b 1
)

:build_setup
echo [資訊] 開始執行 build_installer.ps1...
powershell -ExecutionPolicy Bypass -File ".\build_installer.ps1"
chcp 950 >nul
if errorlevel 1 (
    echo [錯誤] build_installer.ps1 執行失敗。
    exit /b 1
)

echo [完成] 安裝檔已產生完成。
echo [完成] 請至 installer\chklink_setup.exe 取得安裝程式。
echo [完成] 請至 installer\RemoteVersion.yaml 取得版本檔。
exit /b 0