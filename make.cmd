@echo off
REM --output-filename=
REM Set-ExecutionPolicy Unrestricted

REM �R�� out �ؿ������Ҧ��ɮ׻P�ؿ�
if exist out (
    rmdir /s /q out
)

nuitka --standalone --onefile --enable-plugin=tk-inter --windows-icon-from-ico=chklink.ico --output-dir=out - -windows-console-mode=disable chklink.py
