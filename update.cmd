@echo off
echo �i��s�ª������ɴ����@�~...
if exist chklink.exe taskkill /f /im chklink.exe 2>nul
timeout 1
if exist chklink_upd.exe move /Y chklink.exe chklink.exe.old
if exist chklink_upd.exe move /Y chklink_upd.exe chklink.exe
if not exist chklink_upd.exe echo ��s���\�I
if exist chklink_upd.exe echo ��s���ѡI
start chklink.exe
timeout 6
