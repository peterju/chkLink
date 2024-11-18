@echo off
REM --output-filename=
REM Set-ExecutionPolicy Unrestricted

REM 刪除 out 目錄內的所有檔案與目錄
if exist out (
    rmdir /s /q out
)

nuitka --standalone --onefile --enable-plugin=tk-inter --windows-icon-from-ico=chklink.ico --output-dir=out - -windows-console-mode=disable chklink.py
