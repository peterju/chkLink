@echo off
setlocal
cd /d "%~dp0"

set "SEVENZIP=%ProgramFiles%\7-Zip\7z.exe"

if not exist "out\chklink.exe" (
    echo [錯誤] 找不到 out\chklink.exe，請先執行 make.cmd。
    exit /b 1
)

if not exist "%SEVENZIP%" (
    echo [錯誤] 找不到 7-Zip：%SEVENZIP%
    exit /b 1
)

if not exist "LocalVersion.yaml" (
    echo [錯誤] 找不到 LocalVersion.yaml。
    exit /b 1
)

copy /y "out\chklink.exe" "chklink_upd.exe" >nul
if errorlevel 1 (
    echo [錯誤] 無法建立 chklink_upd.exe。
    exit /b 1
)

"%SEVENZIP%" a -t7z "update.7z" "chklink_upd.exe"
if errorlevel 1 (
    echo [錯誤] 無法建立 update.7z。
    exit /b 1
)

if not exist "deploy" mkdir "deploy"

move /y "update.7z" "deploy\" >nul
copy /y "LocalVersion.yaml" "deploy\RemoteVersion.yaml" >nul
del /q "chklink_upd.exe"

echo [完成] 更新部署檔已輸出至 deploy\
