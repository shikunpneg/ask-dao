# -*- coding: utf-8 -*-
"""mcp.py — 把问道做成 MCP server（零依赖，stdio，newline-delimited JSON-RPC 2.0）。

为什么是 MCP：
  Claude Code、Codex、Cursor、Continue 与 DSH 都用同一套 stdio 约定
  （command / args / env），工具名统一落在 mcp__<server>__<tool>。
  所以一份 server 可以同时挂到这些宿主上，不需要各写一个插件。

暴露的工具（都能离线跑，除 perceive 需要 numpy）：
  ask_dao_limits   —— 这台机器的诚实边界（调用方模型必须先读它，避免过度声称）
  ask_dao_problem  —— 日常疑问 → 类型 + 判定路由 + 科学问题
  ask_dao_imagine  —— 造词 → 概念链（组词/拆词/还原/成段/解释）
  ask_dao_paper    —— 论文或语料 → 问题清单（通用三机制 + bio医学领域包 + E-value 计算）
  ask_dao_perceive —— 图像 → 结构特征 → 带判定路由的问题

用法（任何宿主里都差一行配置）：
  python -m ask_dao_machine mcp
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROTOCOL = "2024-11-05"
SERVER = {"name": "ask-dao-machine", "version": "0.5.0"}

LIMITS = """问道 · ask-dao-machine —— 诚实边界（请连同结果一起转述给用户）
1. 世界新问题（N3）至今 = 0 条。产出的是**候选问题**与**证据边界推进**，不是"已确认的新知识"。
2. "检索未见" ≠ "新"。参照系只有 OEIS + 检索；真正的文献门需要人/联网。
3. 论文支线里，"作者已提出"的未解点**不算机器新问题**，必须分开标注。
4. 生物医学领域包产出的方法学追问**不主张世界新**：它是把文中一处方法学缺口写成可判形式，
   其中一部分作者可能已在局限/讨论里提过（标记 author_touched）。
5. E-value 是用 HR/OR 近似 RR 的算术换算，要求结局不常见；数值可复核，但它是门槛不是发现。
6. 每条问题的价值在于**能否被判定**（route 字段给的就是判定方式），不在于措辞漂亮。"""

TOOLS = [
    {
        "name": "ask_dao_limits",
        "description": "问道机器的诚实边界：世界新问题为 0、哪些产出不算新知识。调用其它工具前建议先读。",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "ask_dao_problem",
        "description": ("把一个日常疑问/困惑变成可判的科学问题：给出类型判定、判定路由与形式化后的陈述。"
                        "适合用户问『这个疑问算什么科学问题』时调用。"),
        "inputSchema": {
            "type": "object",
            "properties": {"question": {"type": "string", "description": "用户的日常疑问原文"}},
            "required": ["question"], "additionalProperties": False,
        },
    },
    {
        "name": "ask_dao_imagine",
        "description": ("想象路：输入一个自造词（如『记忆调性』），输出概念链——"
                        "组词、按深度拆词、还原造句、成段、解释。判据是『被理解』而不是真伪。"),
        "inputSchema": {
            "type": "object",
            "properties": {"word": {"type": "string", "description": "要理解的概念词"},
                           "depth": {"type": "integer", "minimum": 1, "maximum": 5, "default": 3}},
            "required": ["word"], "additionalProperties": False,
        },
    },
    {
        "name": "ask_dao_paper",
        "description": ("输入论文/语料（本地文件路径，或直接给正文 text），输出问题清单："
                        "①作者自陈未解（不算新）②文本张力 ③结构追问 ④领域包（biomed=生物医学方法学追问，"
                        "含从 HR/CI 机器算出的 E-value 残余混杂门槛）。"),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "论文文件或目录（.md/.txt/.pdf/.docx/.epub）"},
                "text": {"type": "string", "description": "也可以直接给正文文本（与 path 二选一）"},
                "domain": {"type": "string", "enum": ["auto", "biomed", "none"], "default": "auto"},
                "max_per_type": {"type": "integer", "minimum": 1, "maximum": 20, "default": 6},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "ask_dao_perceive",
        "description": "经验入口：输入一张图（或目录），输出结构特征与带判定路由的视觉问题。需要 numpy。",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "图片文件或目录"}},
            "required": ["path"], "additionalProperties": False,
        },
    },
]


# ── 仓库定位（tools/ 下的引擎不在 wheel 里，源码运行时可用）────────────
def _repo_root() -> Path | None:
    env = os.environ.get("ASK_DAO_ROOT")
    if env and (Path(env) / "tools").is_dir():
        return Path(env)
    for base in (Path.cwd(), Path(__file__).resolve().parents[2]):
        for p in [base, *base.parents]:
            if (p / "tools" / "run_paths.py").exists():
                return p
    return None


def _tools_import(name: str):
    root = _repo_root()
    if root is None:
        raise RuntimeError("找不到仓库根（含 tools/run_paths.py）；请设置 ASK_DAO_ROOT")
    tp = str(root / "tools")
    if tp not in sys.path:
        sys.path.insert(0, tp)
    return __import__(name)


def _quiet(fn, *a, **k):
    """把底层 print 重定向到 stderr，保证 stdout 只有协议帧。"""
    import contextlib
    with contextlib.redirect_stdout(sys.stderr):
        return fn(*a, **k)


# ── 各工具实现 ────────────────────────────────────────────────────────
def _capture(fn, *a, **k) -> str:
    """运行只靠 print 输出的老工具，把文本抓回来（stdout 只留协议帧）。"""
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn(*a, **k)
    return buf.getvalue().strip()


def t_problem(args: dict) -> str:
    q = (args.get("question") or "").strip()
    if not q:
        return "需要 question 参数。"
    qr = _tools_import("question_refiner")
    r = _quiet(qr.refine, {"daily_question": q, "domain": "通用"})
    L = [f"日常疑问：{q}",
         f"类型：{r.get('kind')}　判定路由：{r.get('judge_route')}",
         f"科学问题：{r.get('scientific_question')}",
         "", "（这台机器的诚实边界：世界新问题至今 = 0；产出的是候选问题与判定路由。）"]
    return "\n".join(str(x) for x in L if x is not None)


def t_imagine(args: dict) -> str:
    word = (args.get("word") or "").strip()
    if not word:
        return "需要 word 参数。"
    rp = _tools_import("run_paths")
    depth = int(args.get("depth") or 3)
    txt = _capture(rp.run_imagine, type("A", (), {"word": word, "pairs": None, "depth": depth})())
    if not txt:
        return f"「{word}」未建成树；可换更熟的词，或改用 --pairs 组合两个词。"
    return txt[:2000]


def t_paper(args: dict) -> str:
    from . import paper as P
    domain = args.get("domain") or "auto"
    mpt = int(args.get("max_per_type") or 6)
    text = args.get("text")
    if text:
        probs = P.mine(text, "<inline text>", max_per_type=mpt, domain=domain)
    else:
        path = (args.get("path") or "").strip()
        if not path:
            return "需要 path 或 text 之一。"
        payload = _quiet(P.run, [path], out_dir=os.path.join(os.getcwd(), "out", "mcp_paper"),
                         max_per_type=mpt, quiet=True, domain=domain)
        probs = payload.get("problems", [])
    if not probs:
        return "没有产出问题：检查路径/格式，或正文太短（信号太稀薄）。"
    n_author = sum(1 for p in probs if p.get("is_author_stated"))
    n_bm = sum(1 for p in probs if p.get("domain") == "生物医学")
    n_calc = sum(1 for p in probs if p.get("computed"))
    # 机器算出 > 领域包方法学追问 > 其他（把最有价值的排前面）
    probs = sorted(probs, key=lambda p: (not p.get("computed"),
                                         p.get("domain") != "生物医学"))
    L = [f"共 {len(probs)} 条问题：作者已提出 {n_author} 条（不算新）· 机器提出 {len(probs)-n_author} 条"
         + (f"（生物医学方法学追问 {n_bm} 条，其中机器算出数值 {n_calc} 条）" if n_bm else ""), ""]
    for p in probs[:12]:
        tag = "作者已提出" if p.get("is_author_stated") else "机器提出"
        L.append(f"[{p['type']} {p['id']}] ({tag}) {p['statement'][:220]}")
        L.append(f"    判定路由：{p['route']}")
        if p.get("computed"):
            c = p["computed"]
            L.append(f"    机器算出：{c['effect_type']}={c['point']} (95% CI {c['ci'][0]}–{c['ci'][1]}) "
                     f"→ 残余混杂门槛 E={c['evalue_point']}（CI 界 {c['evalue_ci_bound']}）")
    if len(probs) > 12:
        L.append(f"…还有 {len(probs)-12} 条（已写入 out/mcp_paper/，含 problems_paper.json 与 REPORT.md）")
    L += ["", LIMITS.splitlines()[0], LIMITS.splitlines()[3]]
    return "\n".join(L)


def t_perceive(args: dict) -> str:
    path = (args.get("path") or "").strip()
    if not path:
        return "需要 path 参数。"
    from . import perceive as PC
    payload = _quiet(PC.run, [path], out_dir=os.path.join(os.getcwd(), "out", "mcp_perceive"),
                     quiet=True)
    probs = payload.get("problems", [])
    if not probs:
        return "没有产出问题。"
    L = [f"视觉经验 → {len(probs)} 条可判问题", ""]
    for p in probs[:8]:
        L.append(f"[{p['type']} {p['id']}] {p['statement'][:200]}")
        L.append(f"    证据：{p.get('evidence','')[:160]}　路由：{p['route']}")
    return "\n".join(L)


HANDLERS = {
    "ask_dao_limits": lambda a: LIMITS,
    "ask_dao_problem": t_problem,
    "ask_dao_imagine": t_imagine,
    "ask_dao_paper": t_paper,
    "ask_dao_perceive": t_perceive,
}


def _reply(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _handle(msg: dict) -> dict | None:
    mid = msg.get("id")
    method = msg.get("method")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": PROTOCOL,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": SERVER,
        }}
    if method in ("notifications/initialized", "notifications/cancelled", "initialized"):
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        fn = HANDLERS.get(name)
        if fn is None:
            return {"jsonrpc": "2.0", "id": mid,
                    "error": {"code": -32602, "message": f"unknown tool: {name}"}}
        try:
            text = fn(args)
            return {"jsonrpc": "2.0", "id": mid,
                    "result": {"content": [{"type": "text", "text": text}], "isError": False}}
        except Exception as e:                                   # noqa: BLE001
            return {"jsonrpc": "2.0", "id": mid,
                    "result": {"content": [{"type": "text",
                                            "text": f"{type(e).__name__}: {e}"}],
                               "isError": True}}
    if mid is None:
        return None
    return {"jsonrpc": "2.0", "id": mid,
            "error": {"code": -32601, "message": f"method not found: {method}"}}


def serve() -> int:
    print(f"[ask-dao-machine mcp] stdio server ready (protocol {PROTOCOL}); "
          f"tools={len(TOOLS)}", file=sys.stderr)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = _handle(msg)
        if resp is not None:
            _reply(resp)
    return 0


def main(argv=None) -> int:
    from . import _console
    _console.setup()
    return serve()


if __name__ == "__main__":
    raise SystemExit(main())
