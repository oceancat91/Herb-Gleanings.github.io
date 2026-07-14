# -*- coding: utf-8 -*-
"""运行配置：优先读取 backend/.env（不入库），其次系统环境变量。"""
from __future__ import annotations

import os
from pathlib import Path

_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


def _load_env_file() -> None:
    if not _ENV_PATH.is_file():
        return
    for raw in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


_load_env_file()

DEEPSEEK_API_KEY: str = os.environ.get("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_MODEL: str = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro").strip()
DEEPSEEK_BASE_URL: str = os.environ.get(
    "DEEPSEEK_BASE_URL", "https://api.deepseek.com"
).strip().rstrip("/")
