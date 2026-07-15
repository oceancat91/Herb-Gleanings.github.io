@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 本草拾珍 · 协议启动
where python >nul 2>&1
if errorlevel 1 (
  echo [错误] 未找到 python
  pause
  exit /b 1
)
python run.py --daemon
exit /b %errorlevel%
