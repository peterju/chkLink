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

"%PYTHON_EXE%" -c "import nuitka" >nul 2>nul
if errorlevel 1 (
    echo [錯誤] 目前使用的 Python 環境尚未安裝 Nuitka。
    exit /b 1
)

if not exist "chklink.py" (
    echo [錯誤] 找不到 chklink.py。
    exit /b 1
)

if not exist "chklink.ico" (
    echo [錯誤] 找不到 chklink.ico。
    exit /b 1
)

for /f "delims=" %%i in ('%PYTHON_EXE% -c "import chklink_config as c; print(c.APP_NAME)"') do set "APP_NAME=%%i"
for /f "delims=" %%i in ('%PYTHON_EXE% -c "import chklink_config as c; print(c.DEFAULT_APP_VERSION)"') do set "APP_VERSION=%%i"

if not defined APP_NAME (
    echo [錯誤] 無法取得 APP_NAME。
    exit /b 1
)

if not defined APP_VERSION (
    echo [錯誤] 無法取得 APP_VERSION。
    exit /b 1
)

if not exist "data" mkdir "data"
if not exist "installer" mkdir "installer"

"%PYTHON_EXE%" -c "import chklink_config as c; c.dump_yaml(c.DEFAULT_LOCAL_VERSION_FILE, {\"version\": c.DEFAULT_APP_VERSION}); c.ensure_update_cmd()"
if errorlevel 1 (
    echo [錯誤] 無法更新 data\LocalVersion.yaml 或 data\update.cmd。
    exit /b 1
)

if exist "out" rmdir /s /q "out"
if exist "build" rmdir /s /q "build"
if not exist ".build-cache" mkdir ".build-cache"

set PYTHONUTF8=1
set "NUITKA_CACHE_DIR=%~dp0.build-cache\nuitka"

"%PYTHON_EXE%" -m nuitka ^
    --standalone ^
    --assume-yes-for-downloads ^
    --jobs=%NUMBER_OF_PROCESSORS% ^
    --disable-ccache ^
    --enable-plugin=tk-inter ^
    --include-package-data=ttkbootstrap ^
    --include-data-files=icon\folder.png=icon\folder.png ^
    --product-name=%APP_NAME% ^
    --file-version=%APP_VERSION% ^
    --product-version=%APP_VERSION% ^
    --windows-icon-from-ico=chklink.ico ^
    --windows-console-mode=disable ^
    --output-dir=out ^
    --output-filename=chklink.exe ^
    chklink.py

if errorlevel 1 (
    echo [錯誤] Nuitka 編譯失敗。
    exit /b 1
)

if not exist "out\chklink.dist\chklink.exe" (
    echo [錯誤] 編譯程序已完成，但未產生 out\chklink.dist\chklink.exe。
    exit /b 1
)

copy /y "data\LocalVersion.yaml" "installer\RemoteVersion.yaml" >nul
if errorlevel 1 (
    echo [錯誤] 無法產生 installer\RemoteVersion.yaml。
    exit /b 1
)

echo [完成] 已產生 out\chklink.dist\chklink.exe
echo [完成] 已同步 data\LocalVersion.yaml
echo [完成] 已產生 installer\RemoteVersion.yaml