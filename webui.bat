@echo off
cd /d "%~dp0"
echo ================================
echo   IntroForge v3.2
echo ================================
title IntroForge Server

REM 杀掉占用8888端口的旧进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8888.*LISTENING" 2^>nul') do (
    echo Killing old process on port 8888: %%a
    taskkill /f /pid %%a 2>nul
)
timeout /t 1 >nul

echo Starting server at http://localhost:8888
start http://localhost:8888

:loop
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" -u webui.py
echo [%date% %time%] Server stopped, restarting in 3s...
timeout /t 3 >nul
goto loop
