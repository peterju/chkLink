@echo off
cd /d "%~dp0"
if not defined VIRTUAL_ENV (
	call .venv\Scripts\activate
)
python chklink.py
