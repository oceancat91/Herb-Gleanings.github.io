# -*- coding: utf-8 -*-
"""本草拾珍 · 一键启动：拉起后端并打开前端页面。"""
from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
PID_FILE = ROOT / ".backend.pid"
HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}/"
HEALTH = f"http://{HOST}:{PORT}/api/stats"

# Windows: 后台启动、不弹控制台
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
DETACHED_PROCESS = 0x00000008


def port_open() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((HOST, PORT)) == 0


def api_ready() -> bool:
    try:
        with urllib.request.urlopen(HEALTH, timeout=1.5) as r:
            return 200 <= r.status < 300
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def wait_ready(timeout: float = 25.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if api_ready():
            return True
        time.sleep(0.4)
    return False


def _read_pid() -> int | None:
    try:
        if PID_FILE.is_file():
            return int(PID_FILE.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        pass
    return None


def _write_pid(pid: int) -> None:
    try:
        PID_FILE.write_text(str(pid), encoding="utf-8")
    except OSError:
        pass


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            import ctypes

            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid
            )
            if not handle:
                return False
            code = ctypes.c_ulong()
            ok = ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
            ctypes.windll.kernel32.CloseHandle(handle)
            return bool(ok) and code.value == STILL_ACTIVE
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def start_backend_daemon() -> bool:
    """后台启动 uvicorn（已运行则跳过）。"""
    if api_ready():
        return True

    pid = _read_pid()
    if pid and _pid_alive(pid):
        return wait_ready(20.0)

    if port_open() and not api_ready():
        print(f"端口 {PORT} 已被占用，但 /api/stats 不可用，请检查后重试。")
        return False

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        HOST,
        "--port",
        str(PORT),
    ]
    creationflags = 0
    if os.name == "nt":
        creationflags = DETACHED_PROCESS | CREATE_NO_WINDOW

    proc = subprocess.Popen(
        cmd,
        cwd=str(BACKEND),
        creationflags=creationflags,
        close_fds=os.name != "nt",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _write_pid(proc.pid)
    return wait_ready(30.0)


def start_backend_foreground() -> subprocess.Popen | None:
    """前台启动 uvicorn（关闭窗口即停止）。"""
    if api_ready():
        print(f"后端已在运行：{URL}")
        return None
    if port_open():
        print(f"端口 {PORT} 已被占用，但 /api/stats 不可用，请检查后重试。")
        return None
    print("正在启动后端…")
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            HOST,
            "--port",
            str(PORT),
        ],
        cwd=str(BACKEND),
    )
    if not wait_ready():
        print("后端启动超时，请查看上方报错。")
        if proc.poll() is None:
            proc.terminate()
        return None
    print(f"后端已就绪：{URL}")
    _write_pid(proc.pid)
    return proc


def open_browser() -> None:
    webbrowser.open(URL)


def main() -> int:
    parser = argparse.ArgumentParser(description="本草拾珍 · 启动后端并打开前端")
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="后台启动后端（不占用当前窗口，适合打开前端.bat）",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="启动完成后打开浏览器",
    )
    args = parser.parse_args()

    if not (BACKEND / "app" / "main.py").is_file():
        print("未找到 backend/app/main.py")
        return 1

    if args.daemon:
        ok = start_backend_daemon()
        if not ok:
            return 1
        if args.open:
            open_browser()
        return 0

    proc = start_backend_foreground()
    if proc is None and not api_ready():
        return 1

    if args.open or proc is None:
        print("正在打开前端…")
        open_browser()

    if proc is None:
        return 0

    print("关闭本窗口将停止后端（Ctrl+C 亦可）。")
    try:
        return proc.wait()
    except KeyboardInterrupt:
        print("\n正在停止后端…")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
