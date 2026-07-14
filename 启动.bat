@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 本草拾珍
echo ========================================
echo   本草拾珍 —— 正在启动后端并打开前端
echo ========================================
echo.
where python >nul 2>&1
if errorlevel 1 (
  echo [错误] 未找到 python，请先安装 Python 并加入 PATH。
  pause
  exit /b 1
)
python run.py
if errorlevel 1 pause
