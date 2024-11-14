@echo off
rem signtool sign /sha1 089a46b557607ae3bf629b07906b8931088107f3 /fd SHA1 /t http://timestamp.sectigo.com /v out\chklink.exe
REM --output-filename=
REM Set-ExecutionPolicy Unrestricted
copy /y out\chklink.exe chklink_upd.exe
"C:\Program Files\7-Zip\7z.exe" a resources.7z icon\*.* webdriver\*.* LocalVersion.yaml
"C:\Program Files\7-Zip\7z.exe" a update.7z chklink_upd.exe
if not exist deploy mkdir deploy
move /y resources.7z deploy
move /y update.7z deploy
copy /y LocalVersion.yaml deploy\RemoteVersion.yaml
del /q chklink_upd.exe
