# -*- coding: utf-8 -*-
"""按「谁真的运行它」重判 tools/，并生成 tools/README.md 索引。

上次审计的缺陷：把「文档里提到文件名」当成引用 —— 而 docs/EXECUTION_LOG.md 是
历史日志，提到某个脚本不代表它现在有用。真正的判据是**运行关系**：
  1) CI / workflow 调用
  2) src/ask_dao_machine 调用（_repo_tools() 会 import tools/ 里的模块）
  3) run_resident 调用（它按文件名 subprocess）
  4) 其它 tools 脚本 import 或 subprocess 它
  5) 文档正文（非历史日志）给用户演示的命令里出现
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"E:\ask-dao\ask-dao-machine")
TOOLS = ROOT / "tools"

files = sorted(TOOLS.glob("*.py"))
names = [p.stem for p in files]

# ── 取每个文件的一句话说明（首个 docstring 的首行）────────────────
def blurb(p: Path) -> str:
    try:
        t = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    t = t.lstrip("\ufeff")                       # 有的文件带 BOM
    m = re.match(r'\s*(?:#[^\n]*\n\s*)*("""|\'\'\')(.*?)\1', t, re.S)
    if not m:
        m2 = re.match(r"\s*#[^\n]*\n\s*#\s*(.+)", t)
        return (m2.group(1).strip()[:70] if m2 else "")
    body = m.group(2).strip()
    line = body.splitlines()[0].strip() if body else ""
    line = re.sub(r"^[\w/\.]+\.py\s*—\s*", "", line)      # 去掉 "xxx.py — " 前缀
    return line[:70]


def sources() -> dict[str, list[str]]:
    """谁是「运行者」（不是「提到者」）。"""
    live: dict[str, set[str]] = defaultdict(set)

    def scan(pat: re.Pattern, tag: str, paths):
        for p in paths:
            if not p.is_file():
                continue
            try:
                t = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for n in names:
                if pat.search(t.replace(n + ".py", "\x00")):
                    live[n].add(tag)

    # 1) CI / workflow / action
    ci = list((ROOT / ".github").rglob("*.yml")) + list((ROOT / ".github").rglob("*.yaml"))
    for p in ci:
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for n in names:
            if re.search(rf"\b{n}\b", t):
                live[n].add("CI")
    # 2) src/（含 _repo_tools 的 import 与 subprocess）
    srcs = list((ROOT / "src").rglob("*.py"))
    for p in srcs:
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for n in names:
            if re.search(rf"\b{n}\b", t):
                live[n].add("src")
    # 3) run_resident（按文件名 subprocess）
    rr = TOOLS / "run_resident.py"
    if rr.exists():
        t = rr.read_text(encoding="utf-8", errors="ignore")
        for n in names:
            if re.search(rf"\b{n}\b", t):
                live[n].add("长跑总控")
    # 4) 其它 tools 之间
    for p in files:
        t = p.read_text(encoding="utf-8", errors="ignore")
        for n in names:
            if n == p.stem:
                continue
            if re.search(rf"\b{n}\b", t):
                live[n].add("tools")
    # 5) 文档正文（排除历史日志类）
    HIST = {"execution_log.md", "experiment_record.md", "novelty_ledger.md",
            "novelty_ledger_corrections.md", "k2_ledger.md", "master_plan.md"}
    for p in list((ROOT / "docs").rglob("*.md")) + [ROOT / "README.md"]:
        if p.name.lower() in HIST:
            continue
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for n in names:
            if re.search(rf"\b{n}\b", t):
                live[n].add("文档")
    return live


live = sources()
# 按"运行者"强弱排序
ORDER = {"CI": 0, "src": 1, "长跑总控": 2, "文档": 3, "tools": 4}
groups: dict[str, list[str]] = defaultdict(list)
for n in names:
    who = sorted(live.get(n, set()), key=lambda x: ORDER.get(x, 9))
    groups["、".join(who) if who else "(没有运行者)"].append(n)

print(f"tools/ 共 {len(names)} 个 .py\n")
print("=" * 90)
print("A. 有运行者的（按运行者分组）")
print("=" * 90)
for who in sorted(groups, key=lambda k: (ORDER.get(k.split("、")[0], 9), k)):
    if who == "(没有运行者)":
        continue
    print(f"\n▌ {who}　（{len(groups[who])} 个）")
    for n in sorted(groups[who]):
        p = TOOLS / f"{n}.py"
        print(f"   {n:30} {blurb(p)}")

dead = groups.get("(没有运行者)", [])
print()
print("=" * 90)
print(f"B. 没有任何运行者的 {len(dead)} 个")
print("=" * 90)
for n in sorted(dead):
    p = TOOLS / f"{n}.py"
    print(f"   {n:30} {blurb(p)}")

# ── 生成 tools/README.md ─────────────────────────────────────────
out = ["# tools/ —— 每个脚本是干什么的",
       "",
       "> 本文件自动生成（`python tools/tools_index.py`）。改脚本后请重新生成。",
       "",
       f"共 {len(names)} 个脚本。按「**谁在运行它**」分组——"
       "只有被运行的才算活代码；只在历史日志里被提到的，不算。",
       ""]
for who in sorted(groups, key=lambda k: (ORDER.get(k.split("、")[0], 9), k)):
    if who == "(没有运行者)":
        continue
    out.append(f"## {who}　（{len(groups[who])} 个）")
    out.append("")
    out.append("| 脚本 | 作用 |")
    out.append("|---|---|")
    for n in sorted(groups[who]):
        out.append(f"| `{n}.py` | {blurb(TOOLS / f'{n}.py') or '—'} |")
    out.append("")
if dead:
    out.append(f"## 没有运行者　（{len(dead)} 个）")
    out.append("")
    out.append("> 这些脚本当前**没有任何东西调用它**。可能是一次性探针、"
               "已完成使命的历史脚本，或需要保留的证据链。**先别删**——"
               "但要对它们做任何事之前，先确认不是证据链的一环。")
    out.append("")
    out.append("| 脚本 | 作用 |")
    out.append("|---|---|")
    for n in sorted(dead):
        out.append(f"| `{n}.py` | {blurb(TOOLS / f'{n}.py') or '—'} |")
    out.append("")
(TOOLS / "README.md").write_text("\n".join(out), encoding="utf-8")
print()
print(f"已生成 tools/README.md（{len(out)} 行）")
