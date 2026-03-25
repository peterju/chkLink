@echo off
chcp 950 >nul
setlocal
set "SETUP_PATH=%~1"
if "%SETUP_PATH%"=="" (
    echo [錯誤] 缺少安裝程式路徑。
    exit /b 1
)
if not exist "%SETUP_PATH%" (
    echo [錯誤] 找不到安裝程式：%SETUP_PATH%
    exit /b 1
)
echo [資訊] 準備啟動新版安裝程式...
taskkill /f /im chklink.exe 2>nul
timeout /t 1 /nobreak >nul
start "" "%SETUP_PATH%"
exit /b 0
