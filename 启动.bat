@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 本草拾珍

where python >nul 2>&1 || (
  echo [错误] 未找到 python，请先安装并加入 PATH
  pause & exit /b 1
)

python -c "import fastapi" >nul 2>&1 || (
  echo [提示] 正在安装依赖，仅首次需要…
  pip install -r backend\requirements.txt -q
)

python launch.py
pause
