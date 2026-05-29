@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo Web Config Panel: http://localhost:8888
start http://localhost:8888
%LOCALAPPDATA%\Programs\Python\Python312\python.exe webui.py
pause
