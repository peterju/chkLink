@echo off
REM --output-filename=
REM Set-ExecutionPolicy Unrestricted
python -m nuitka --onefile --disable-console --enable-plugin=tk-inter --windows-icon-from-ico=chklink.ico --output-dir=out chklink.py
