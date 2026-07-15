@echo off
chcp 65001 >nul
title 卸载 herba:// 协议
reg delete "HKCU\Software\Classes\herba" /f >nul 2>&1
echo 已尝试删除 herba:// 协议注册。
pause
