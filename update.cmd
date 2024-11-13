@echo off
echo 進行新舊版執行檔替換作業...
if exist chklink.exe taskkill /f /im chklink.exe 2>nul
timeout 1
if exist chklink_upd.exe move /Y chklink.exe chklink.exe.old
if exist chklink_upd.exe move /Y chklink_upd.exe chklink.exe
if not exist chklink_upd.exe echo 更新成功！
if exist chklink_upd.exe echo 更新失敗！
start chklink.exe
timeout 6
