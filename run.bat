@echo off
chcp 65001 > nul
cd /d "%~dp0"
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" main.py
pause
