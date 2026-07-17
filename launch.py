# -*- coding: utf-8 -*-
"""本草拾珍 · 启动器 —— 杀旧进程 → 启动 uvicorn → 等就绪 → 打开浏览器。"""
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

BACKEND = Path(__file__).resolve().parent / "backend"
URL = "http://127.0.0.1:8000/"
HEALTH = f"{URL}api/stats"
TIMEOUT = 30


def kill_port_8000():
    """杀掉所有占用 8000 端口的进程。"""
    import re
    try:
        out = subprocess.run(
            ["netstat", "-ano"], capture_output=True, text=True, timeout=5
        ).stdout
    except Exception:
        return
    for line in out.split("\n"):
        if ":8000" not in line or "LISTENING" not in line:
            continue
        m = re.search(r"LISTENING\s+(\d+)", line)
        if m:
            subprocess.run(["taskkill", "/pid", m.group(1), "/f"], capture_output=True)


def main() -> int:
    # ---------- 0. 清扫旧进程 ----------
    print("检查端口…")
    kill_port_8000()
    time.sleep(0.3)

    # ---------- 1. 后台启动 uvicorn ----------
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(BACKEND),
        stdout=subprocess.DEVNULL,
        stderr=None,
        creationflags=(getattr(subprocess, "CREATE_NO_WINDOW", 0)
                       if sys.platform == "win32" else 0),
    )

    # ---------- 2. 等就绪 ----------
    print("等待后端就绪…", end="", flush=True)
    deadline = time.time() + TIMEOUT
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(HEALTH, timeout=1) as r:
                if 200 <= r.status < 300:
                    break
        except Exception:
            pass
        time.sleep(0.5)
        print(".", end="", flush=True)
    else:
        print("\n[失败] 后端 %d 秒未就绪，请检查报错" % TIMEOUT)
        kill_port_8000()
        return 1
    print(" OK")

    # ---------- 3. 打开浏览器 ----------
    print("正在打开浏览器 " + URL)
    webbrowser.open(URL)

    # ---------- 4. 等用户手动停止 ----------
    input("\n本草拾珍已启动  " + URL + "\n按 Enter 停止服务…\n")

    kill_port_8000()
    print("服务已停止。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
