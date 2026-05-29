@echo off
cd /d "%~dp0"
echo IntroForge v3.0
echo http://localhost:8888
start http://localhost:8888
:loop
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" -u webui.py
echo Server stopped, restarting...
timeout /t 2 >nul
goto loop
