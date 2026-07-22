# -*- coding: utf-8 -*-
"""本草拾珍启动器：清端口 → 起后端 → 等就绪 → 开浏览器（同窗口，最稳）。"""
from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
URL = "http://127.0.0.1:8000/"
HEALTH = URL + "api/stats"


def kill_port_8000() -> None:
    import re

    try:
        out = subprocess.run(
            ["netstat", "-ano"], capture_output=True, text=True, timeout=8
        ).stdout
    except Exception:
        return
    for line in out.splitlines():
        if ":8000" not in line or "LISTENING" not in line:
            continue
        m = re.search(r"LISTENING\s+(\d+)\s*$", line)
        if not m:
            continue
        subprocess.run(["taskkill", "/PID", m.group(1), "/F"], capture_output=True)


def open_when_ready() -> None:
    for _ in range(60):
        try:
            with urllib.request.urlopen(HEALTH, timeout=1.2) as r:
                data = json.loads(r.read().decode("utf-8"))
            n = data.get("total_herbs", "?")
            print("\n数据库已连接，药材数：", n)
            print("正在打开浏览器：", URL)
            webbrowser.open(URL)
            print("请使用地址：", URL, "（不要双击 index.html）")
            return
        except Exception:
            time.sleep(0.4)
    print("\n[警告] 服务已启动但健康检查超时，请手动打开", URL)


def main() -> int:
    if not (BACKEND / "app" / "main.py").is_file():
        print("[错误] 找不到 backend/app/main.py")
        return 1

    print("清理旧进程…")
    kill_port_8000()
    time.sleep(0.4)

    # 切到 backend，保证相对路径与数据库路径正确
    import os

    os.chdir(str(BACKEND))
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))

    threading.Thread(target=open_when_ready, daemon=True).start()

    print("启动后端（关闭本窗口 = 停止服务）…")
    print("=" * 48)
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
