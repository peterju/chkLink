@echo off
chcp 950 >nul
setlocal
cd /d "%~dp0"

:menu
cls
echo ========================================
echo chkLink 建置選單
echo ========================================
echo 1. 編譯 GUI / CLI 並產生 RemoteVersion
echo 2. 對 GUI / CLI 加簽
echo 3. 建立 installer
echo 4. 對 installer 加簽
echo 5. 產生 SHA256.txt
echo 6. 整理 GitHub Release 資產
echo 0. 離開
echo ========================================
set /p CHOICE=請輸入要執行的步驟： 

if "%CHOICE%"=="1" call make_exec.cmd
if "%CHOICE%"=="2" call make_sign_app.cmd
if "%CHOICE%"=="3" call make_setup.cmd
if "%CHOICE%"=="4" call make_sign_setup.cmd
if "%CHOICE%"=="5" call make_sha256.cmd
if "%CHOICE%"=="6" call make_github_release.cmd
if "%CHOICE%"=="0" goto end
if not "%CHOICE%"=="1" if not "%CHOICE%"=="2" if not "%CHOICE%"=="3" if not "%CHOICE%"=="4" if not "%CHOICE%"=="5" if not "%CHOICE%"=="6" if not "%CHOICE%"=="0" (
    echo [錯誤] 無效的選項。
)

echo.
pause
goto menu

:end
exit /b 0
