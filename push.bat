@echo off
cd /d "%~dp0"
echo === 提交更新 ===
set /p msg="提交说明: "
git add -A
git commit -m "%msg%"
echo === 推送 ===
git push
echo === 完成 ===
pause
