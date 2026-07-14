@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 本草拾珍 · 打开
where python >nul 2>&1
if errorlevel 1 (
  echo [错误] 未找到 python，请先安装 Python 并加入 PATH。
  pause
  exit /b 1
)
python run.py --daemon --open
if errorlevel 1 (
  echo.
  echo [提示] 后端未能启动，请检查 backend 依赖是否已安装：
  echo   pip install -r backend\requirements.txt
  pause
  exit /b 1
)
