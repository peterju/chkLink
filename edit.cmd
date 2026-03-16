@echo off
setlocal
cd /d "%~dp0"
if not defined VIRTUAL_ENV (
    if exist .venv\Scripts\activate.bat (
        call .venv\Scripts\activate.bat 
    )
)
echo 開啟目前專案資料夾...
code .