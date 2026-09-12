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

files = sorted(p for p in TOOLS.rglob("*.py")
               if "__pycache__" not in p.parts)
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
    line = re.sub(r"^(?:[\w/\.\-]+[/\\])?[\w\.\-]+\.py\s*[—\-]+\s*", "", line)
    line = re.sub(r"^(?:tools[/\\])?(?:core|engines|build|maintain|research|archive|site)[/\\]?[\w\.\-]*\.py\s*[—\-]+\s*", "", line)
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


# 手动入口白名单：靠 `python tools/<sub>/xxx.py` 手跑，没有任何「引用」能检测到。
# 这是上一版审计的盲点 —— 它们被误判进「没有运行者」，其实是被手跑的。
MANUAL = {
    "make_site", "make_site_assets", "build_paths_viz", "build_site_problems",
    "build_tree_viz", "make_problem_tree", "tree_svg", "arch_diagram",
    "make_deck", "make_pptx", "deck_spec", "deck_figs", "design_ink",
    "make_logo", "art_logo", "banner_art", "make_ledger",
    "install_integrations", "tools_index", "run_resident",
    "reorganize_tools", "fix_tools_layout_refs", "fix_tools_layout_refs2",
}

live = sources()

# 文件已按功能分到子目录，所以"按名字拼路径"是错的 ——
# 之前 blurb(PATH_OF.get(n, TOOLS / f"{n}.py")) 因此全部读不到，说明列退化成「—」。
PATH_OF: dict[str, Path] = {p.stem: p for p in files}

for _n in MANUAL:
    live.setdefault(_n, set()).add("手动入口")
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
        p = PATH_OF.get(n, TOOLS / f"{n}.py")
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
DESC = {
    "core": "**产品依赖** —— 被 src/ask_dao_machine 调用，不能乱动",
    "engines": "**长跑链路** —— 被 run_resident.py 按文件名调用",
    "build": "**生成产物** —— 站点 / PPT / 架构图 / logo（手动入口）",
    "maintain": "**工程维护** —— 重构 / 修复 / 补抓语料 / 索引（手动入口）",
    "research": "**研究实验** —— 提问题 / 扫描 / 验证 / 度量（历史与在用的都在这里）",
    "archive": "**归档** —— 没有运行者的历史脚本（先别删，可能是证据链）",
    "site": "站点模板与数据（非 .py）",
}

_overview = ["# tools/ —— 每个脚本是干什么的",
       "",
       "> 本文件自动生成（`python tools/tools_index.py`）。改脚本后请重新生成。",
       "",
       "## 目录结构总览",
       "",
       "```",
       "tools/",
       "├── run_resident.py      常驻长跑总控（三链路轮转的入口）",
       "├── tools_index.py       本索引的生成器",
       "├── core/                产品依赖（被 src/ 调用）",
       "├── engines/             长跑链路引擎（被 run_resident 调用）",
       "├── build/               生成产物：站点 / PPT / 架构图 / logo",
       "├── maintain/            工程维护：重构 / 修复 / 补抓 / 索引",
       "├── research/            研究实验",
       "├── archive/             归档的历史脚本",
       "└── site/                站点模板与数据",
       "```",
       "",
       "| 目录 | 是什么 |",
       "|---|---|",
       ]
for _k in ("core", "engines", "build", "maintain", "research", "archive", "site"):
    _n = len([x for x in TOOLS.glob(f"{_k}/*.py")])
    out.append(f"| `{_k}/` | {DESC[_k]}{f'（{_n} 个脚本）' if _n else ''} |")
out += ["",
        "**怎么用**：想知道某个脚本干什么，直接在里面搜文件名；"
        "`research/` 里多数是当时的研究脚本，跑不跑得通取决于当时的产物还在不在。",
        ""]
out = _overview + [
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
        out.append(f"| `{n}.py` | {blurb(PATH_OF.get(n, TOOLS / f'{n}.py')) or '—'} |")
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
        out.append(f"| `{n}.py` | {blurb(PATH_OF.get(n, TOOLS / f'{n}.py')) or '—'} |")
    out.append("")

STRUCT_OVERVIEW = """## 目录结构总览

```
tools/
├── run_resident.py      常驻长跑总控（三链路轮转的入口）
├── tools_index.py       本索引的生成器
├── core/                产品依赖（被 src/ask_dao_machine 调用）
├── engines/             长跑链路引擎（被 run_resident.py 调用）
├── build/               生成产物：站点 / PPT / 架构图 / logo（手动入口）
├── maintain/            工程维护：重构 / 修复 / 补抓语料 / 索引（手动入口）
├── research/            研究实验：提问题 / 扫描 / 验证 / 度量
├── archive/             归档：没有运行者的历史脚本（先别删，可能是证据链）
└── site/                站点模板与数据（非 .py）
```

**怎么找**：知道脚本名就搜文件名；不知道就按上表看它属于哪一类再翻。
`research/` 里多数是当时的研究脚本，能不能跑取决于当时的产物还在不在。
**怎么加**：新脚本请放进对应子目录 —— `core/`（产品要用）、`engines/`（长跑要用）、
`build/`（生成产物）、`maintain/`（工程维护）、`research/`（一次性研究）。
放完重跑 `python tools/tools_index.py`。

"""

(TOOLS / "README.md").write_text(
    STRUCT_OVERVIEW + "\n".join(out), encoding="utf-8")
print()
print(f"已生成 tools/README.md（{len(out)} 行）")
