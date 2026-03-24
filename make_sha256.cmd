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

set "OUTPUT_DIR=installer\%APP_VERSION%"
set "SETUP_FILE=%OUTPUT_DIR%\chklink_setup.exe"
set "REMOTE_FILE=%OUTPUT_DIR%\RemoteVersion.yaml"
set "HASH_FILE=%OUTPUT_DIR%\SHA256.txt"

if not exist "%SETUP_FILE%" (
    echo [錯誤] 找不到 %SETUP_FILE% ，請先執行 make_setup.cmd。
    exit /b 1
)

if not exist "%REMOTE_FILE%" (
    echo [錯誤] 找不到 %REMOTE_FILE% ，請先執行 make_exec.cmd。
    exit /b 1
)

echo [資訊] 正在產生 %HASH_FILE% ...
"%PYTHON_EXE%" -c "import hashlib, pathlib; files = [pathlib.Path(r'%SETUP_FILE%'), pathlib.Path(r'%REMOTE_FILE%')]; output = pathlib.Path(r'%HASH_FILE%'); lines = []; [lines.append(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.name) for path in files]; output.write_text('\n'.join(lines) + '\n', encoding='utf-8')"
if errorlevel 1 (
    echo [錯誤] 產生 SHA256.txt 失敗。
    exit /b 1
)

echo [完成] 已產生 %HASH_FILE%
exit /b 0