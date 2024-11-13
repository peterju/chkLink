@echo off
cd /d "%~dp0"
if not defined VIRTUAL_ENV (
	call env\Scripts\activate
)
code .
