# -*- coding: utf-8 -*-
"""banner.py — 进入时的「道」徽标与命令速查。

徽标不是手绘的：它是把系统字体里「道」的位图取出来转成的字符画，
并经过反向校验（字符画还原回位图 == 原字体位图，逐点一致）。
生成脚本见 docs/guide/cli.md 的说明；运行时不需要字体与 Pillow。
"""
from __future__ import annotations

import os
import sys

DAO_ART = [
    "  ▄▄        ▄▄       █▄▄    ",
    "   ▀█▄       ██▄    ▄█▀     ",
    "    ██        █▀   ▄▀    ▄▄ ",
    "        ▀▀▀▀▀▀▀▀██▀▀▀▀▀▀▀▀▀▀",
    "     ▄          █▀     ▄    ",
    "▀▀▀▀██▀    ██▀▀▀▀▀▀▀▀▀██▀   ",
    "    ██     ██▄▄▄▄▄▄▄▄▄██    ",
    "    ██     ██         ██    ",
    "    ██     ██▄▄▄▄▄▄▄▄▄██    ",
    "    ██     ██         ██    ",
    "    ██     ██▄▄▄▄▄▄▄▄▄██    ",
    " ▄▄▀▀▀▀▄   ██         ▀▀    ",
    "██      ▀▄▄▄                ",
    "          ▀▀▀▀████████████▀▀",
]

TAGLINE = "一台制造知识的机器：只产问题与概念，不产答案。"
HONESTY = "诚实边界：世界新问题 N3 = 0 —— 产出是候选问题与判定路由，不是「已确认的新知识」。"

# (命令, 说明) —— 保持短、可组合、能直接复制着跑
COMMANDS = [
    ("paper <文件/目录…>", "论文 → 问题（「作者已提出」/「机器提出」分开标注）"),
    ("ask \"<日常疑问>\"", "疑问 → 类型 + 判定路由 + 科学问题"),
    ("imagine <自造词>", "造词 → 概念（组词/拆词/还原造句/成段/解释）"),
    ("perceive <图片/目录…>", "图像（经验）→ 结构特征 → 带判定路由的问题"),
    ("all", "86 母题 → 问题树 L0–L5 → 领域融合（+ 新颖性门）"),
    ("report", "把一次跑批汇总成一页人话 REPORT.md"),
    ("doctor", "环境自查：缺什么、下一步做什么"),
    ("data fetch", "取 OEIS 参照系（约 32MB）"),
    ("mcp", "以 MCP server 运行，挂到 Claude Code / DSH / Cursor"),
]

_R, _D, _B = "\033[0m", "\033[2m", "\033[1m"
_VERM = "\033[38;2;176;58;46m"     # 朱砂：只用在徽标上（浅底深底都看得见）


def _use_color(stream) -> bool:
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("ASK_DAO_COLOR", "").lower() in ("1", "always", "true", "yes"):
        return True
    if os.environ.get("ASK_DAO_BANNER") == "0":
        return False
    try:
        return bool(stream.isatty())
    except Exception:                                            # noqa: BLE001
        return False


def version() -> str:
    try:
        from importlib.metadata import version as _v
        return _v("ask-dao-machine")
    except Exception:                                            # noqa: BLE001
        return "0.5.0"


def _dw(s: str) -> int:
    """终端显示宽度：CJK 与全角算 2 列（否则中英混排的表格会歪）。"""
    import unicodedata
    w = 0
    for ch in s:
        w += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return w


def render(color: bool | None = None, stream=None, width: int | None = None) -> str:
    """正文只用「终端默认前景 + 加粗/变暗」，不写死颜色——浅底深底都不会变成看不见的字。"""
    stream = stream or sys.stdout
    if color is None:
        color = _use_color(stream)

    def c(code: str, text: str) -> str:
        return f"{code}{text}{_R}" if color else text

    L = [""]
    for line in DAO_ART:
        L.append("   " + c(_VERM, line))
    L.append("")
    L.append("   " + c(_B, "问道 · ask-dao-machine") + c(_D, f"  v{version()}"))
    L.append("   " + c(_D, TAGLINE))
    L.append("")
    labels = [f"ask-dao-machine {cmd}" for cmd, _ in COMMANDS]
    pad = max(_dw(s) for s in labels) + 2
    for label, (_, desc) in zip(labels, COMMANDS):
        L.append("   " + c(_B, label) + " " * (pad - _dw(label)) + c(_D, desc))
    L.append("")
    L.append("   " + c(_D, HONESTY))
    L.append("   " + c(_D, "ask-dao-machine help   看全部用法；每条命令都支持 --help"))
    L.append("")
    return "\n".join(L)


def show(stream=None) -> None:
    stream = stream or sys.stdout
    print(render(stream=stream), file=stream)


def usage_line() -> str:
    return ("用法: ask-dao-machine <paper|ask|imagine|perceive|all|report|doctor|"
            "data|mcp> …  （直接敲 ask-dao-machine 看速查）")
