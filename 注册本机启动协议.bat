@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 注册 herba:// 本机启动协议

echo.
echo 将注册自定义协议 herba:// 
echo 之后从 GitHub Pages 打开主页时，可请求本机自动启动后端。
echo 仅写入当前用户注册表，可随时卸载。
echo.

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
set "LAUNCHER=%ROOT%\run_herba_protocol.bat"

reg add "HKCU\Software\Classes\herba" /ve /d "URL:Herba Atlas Protocol" /f >nul
reg add "HKCU\Software\Classes\herba" /v "URL Protocol" /d "" /f >nul
reg add "HKCU\Software\Classes\herba\DefaultIcon" /ve /d "%%SystemRoot%%\System32\SHELL32.dll,13" /f >nul
reg add "HKCU\Software\Classes\herba\shell\open\command" /ve /d "\"%LAUNCHER%\" \"%%1\"" /f >nul

if errorlevel 1 (
  echo [失败] 注册表写入失败。
  pause
  exit /b 1
)

echo [完成] 已注册 herba:// →
echo   %LAUNCHER%
echo.
echo 使用方式：
echo   1. 打开 https://oceancat91.github.io/Herb-Gleanings.github.io/
echo   2. 浏览器若询问是否打开「本草拾珍」协议，请允许
echo   3. 本机后端启动后，页面会自动跳转到完整版
echo.
echo 卸载请运行：卸载本机启动协议.bat
echo.
pause
