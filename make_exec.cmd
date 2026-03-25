@echo off
chcp 950 >nul
setlocal
cd /d "%~dp0"

echo [資訊] make_exec.cmd 的作用：編譯 GUI / CLI，並產生對應版本的遠端版本檔。
echo [資訊] 這是第 1 步，完成後可依需要執行 make_sign_app.cmd 或 make_setup.cmd。
echo.

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

if not exist "chklink_cli.py" (
    echo [錯誤] 找不到 chklink_cli.py。
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

if not exist "installer" mkdir "installer"
if not exist "installer\%APP_VERSION%" mkdir "installer\%APP_VERSION%"

"%PYTHON_EXE%" -c "import chklink_config as c; c.ensure_update_cmd(); c.dump_yaml('installer/{}/RemoteVersion.yaml'.format(c.DEFAULT_APP_VERSION), {'version': c.DEFAULT_APP_VERSION})"
if errorlevel 1 (
    echo [錯誤] 無法建立 installer\%APP_VERSION%\RemoteVersion.yaml 或 update.cmd。
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
    echo [錯誤] GUI Nuitka 編譯失敗。
    exit /b 1
)

if not exist "out\chklink.dist\chklink.exe" (
    echo [錯誤] 編譯程序已完成，但找不到 out\chklink.dist\chklink.exe。
    exit /b 1
)

"%PYTHON_EXE%" -m nuitka ^
    --onefile ^
    --assume-yes-for-downloads ^
    --jobs=%NUMBER_OF_PROCESSORS% ^
    --disable-ccache ^
    "--product-name=%APP_NAME% CLI" ^
    --file-version=%APP_VERSION% ^
    --product-version=%APP_VERSION% ^
    --windows-icon-from-ico=chklink.ico ^
    --windows-console-mode=force ^
    --output-dir=out ^
    --output-filename=chklink_cli.exe ^
    chklink_cli.py

if errorlevel 1 (
    echo [錯誤] CLI Nuitka 編譯失敗。
    exit /b 1
)

if not exist "out\chklink_cli.exe" (
    echo [錯誤] 編譯程序已完成，但找不到 out\chklink_cli.exe。
    exit /b 1
)

echo [完成] 已產生 out\chklink.dist\chklink.exe
echo [完成] 已產生 out\chklink_cli.exe
echo [完成] 已產生 installer\%APP_VERSION%\RemoteVersion.yaml
echo [完成] 下一步可執行 make_sign_app.cmd 或直接執行 make_setup.cmd
exit /b 0