# -*- coding: utf-8 -*-
"""_console.py — 让 CLI 在非 UTF-8 控制台（Windows cp1252/cp936、CI runner）上也能正常输出中文。

Windows 上 Python 的 stdout 默认跟随控制台代码页（常见 cp1252/cp936），打印中文会直接
抛 UnicodeEncodeError 让命令崩掉——这在 GitHub Actions 的 windows-latest 上必然发生。
这里统一把 stdout/stderr 切成 UTF-8（errors="replace" 兜底），是幂等且无副作用的。
"""
from __future__ import annotations

import sys


def setup() -> None:
    """把标准输出/错误切到 UTF-8；失败就算了（例如被 pytest 捕获时）。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except Exception:                                       # noqa: BLE001
            pass
