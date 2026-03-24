@echo off
chcp 950 >nul
setlocal
cd /d "%~dp0"

set "PYTHON_EXE=python"
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo [錯誤] 找不到 Python。
        exit /b 1
    )
)

for /f "delims=" %%i in ('%PYTHON_EXE% -c "import chklink_config as c; print(c.DEFAULT_APP_VERSION)"') do set "APP_VERSION=%%i"
if not defined APP_VERSION (
    echo [錯誤] 無法取得 APP_VERSION。
    exit /b 1
)

set "SOURCE_DIR=installer\%APP_VERSION%"
set "SOURCE_SETUP=%SOURCE_DIR%\chklink_setup.exe"
set "SOURCE_REMOTE=%SOURCE_DIR%\RemoteVersion.yaml"
set "RELEASE_DIR=release\%APP_VERSION%"
set "RELEASE_SETUP=chklink-%APP_VERSION%-win-x64-setup.exe"
set "RELEASE_REMOTE=chklink-%APP_VERSION%-RemoteVersion.yaml"
set "RELEASE_HASH=chklink-%APP_VERSION%-SHA256.txt"

if not exist "%SOURCE_SETUP%" (
    echo [錯誤] 找不到 %SOURCE_SETUP% ，請先執行 make_setup.cmd。
    exit /b 1
)

if not exist "%SOURCE_REMOTE%" (
    echo [錯誤] 找不到 %SOURCE_REMOTE% ，請先執行 make_exec.cmd。
    exit /b 1
)

if not exist "%RELEASE_DIR%" mkdir "%RELEASE_DIR%"

echo [資訊] 正在整理 GitHub Release 資產...
copy /y "%SOURCE_SETUP%" "%RELEASE_DIR%\%RELEASE_SETUP%" >nul
if errorlevel 1 (
    echo [錯誤] 複製 installer 失敗。
    exit /b 1
)

copy /y "%SOURCE_REMOTE%" "%RELEASE_DIR%\%RELEASE_REMOTE%" >nul
if errorlevel 1 (
    echo [錯誤] 複製 RemoteVersion.yaml 失敗。
    exit /b 1
)

"%PYTHON_EXE%" -c "import hashlib, pathlib; base = pathlib.Path(r'%RELEASE_DIR%'); files = [base / r'%RELEASE_SETUP%', base / r'%RELEASE_REMOTE%']; out = base / r'%RELEASE_HASH%'; lines = [hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name for p in files]; out.write_text('\n'.join(lines) + '\n', encoding='utf-8')"
if errorlevel 1 (
    echo [錯誤] 產生 GitHub Release SHA256.txt 失敗。
    exit /b 1
)

echo [完成] 已建立 %RELEASE_DIR%
echo [完成] - %RELEASE_SETUP%
echo [完成] - %RELEASE_REMOTE%
echo [完成] - %RELEASE_HASH%
exit /b 0
