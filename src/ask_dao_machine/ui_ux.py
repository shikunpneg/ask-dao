# -*- coding: utf-8 -*-
"""ux.py — 全 CLI 共用的三件事，避免每条命令各写一套。

以前的问题（产品审计发现）：
  1. `--out` 默认值各命令不同：paper→out/papers、ask→out/ask、run→out/runs、
     perceive→out/perceive，而 report 默认 ./out —— 跑完想接报告，目录对不上。
  2. 跑完只给一行 `→ 路径`，不告诉用户下一步能干什么。
  3. 没有机器可读输出：想接管道/脚本，得自己去翻 out/ 找目录名。

这里提供：
  out_root(arg)        统一的输出根目录（默认 <repo>/out，可用 ASK_DAO_OUT 覆盖）
  run_dir(root, kind)  <root>/<kind>，保证存在
  next_steps(...)      跑完打印"下一步能做什么"（带真实可复制的命令）
  emit_json(obj)       把结果以 JSON 打到 stdout（--json 时用；其它日志走 stderr）
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

DEFAULT_ROOT = "out"


def out_root(arg: str | None = None) -> Path:
    """所有命令统一的输出根目录。

    优先级：命令行 --out > 环境变量 ASK_DAO_OUT > <cwd>/out
    """
    if arg:
        return Path(arg)
    env = os.environ.get("ASK_DAO_OUT")
    if env:
        return Path(env)
    return Path.cwd() / DEFAULT_ROOT


def run_dir(root: Path | str, kind: str) -> Path:
    """<root>/<kind>，需要时创建。kind 建议用功能名：paper / ask / image / words / runs。"""
    d = Path(root) / kind
    d.mkdir(parents=True, exist_ok=True)
    return d


def emit_json(obj: dict | list) -> None:
    """--json：结果只走 stdout，人看的日志由调用方走 stderr，两者不混。"""
    json.dump(obj, sys.stdout, ensure_ascii=False, indent=1)
    sys.stdout.write("\n")
    sys.stdout.flush()


def next_steps(*, out: Path | str | None = None, kind: str = "", extra: list[str] | None = None,
               as_json: bool = False, stream=None) -> None:
    """跑完告诉用户"下一步能做什么"——命令是可复制的，不是泛泛而谈。"""
    if as_json:
        return
    stream = stream or sys.stderr
    L = ["", "下一步可以："]
    if out:
        L.append(f"  ask-dao-machine report --out {out}          # 一页人话汇总")
    if kind == "paper":
        L.append(f"  ask-dao-machine paper <另一个文件>          # 会存到自己的标题目录，不覆盖这次")
        L.append("  ask-dao-machine run <论文> --stop ai4s     # 想一路跑到底就换 run")
    if kind == "ask":
        L.append("  ask-dao-machine ask \"<疑问>\" --stop ai4s    # 继续往下推到 AI4S 站")
    if kind == "words":
        L.append("  ask-dao-machine run --words <词> --bridge  # 加桥：把这个概念接到现实经验")
    L.append("  ask-dao-machine run --list                 # 看跑过哪些、产物在哪")
    for e in (extra or []):
        L.append("  " + e)
    print("\n".join(L), file=stream, flush=True)


# ── run --list：把跑过的产物列出来（以前完全看不到） ────────────────
def list_runs(root: Path | str | None = None, *, as_json: bool = False) -> list[dict]:
    """扫描 <root> 下的产物目录，按修改时间倒序返回。"""
    root = Path(out_root(str(root) if root else None))
    rows: list[dict] = []
    if not root.exists():
        if as_json:
            emit_json([])
        else:
            print(f"还没有任何产物（{root} 不存在）。先跑一次：ask-dao-machine run <论文>")
        return rows
    for d in sorted(root.rglob("*"), key=lambda p: p.stat().st_mtime if p.exists() else 0,
                    reverse=True):
        if not d.is_dir():
            continue
        files = [f.name for f in d.iterdir() if f.is_file()] if d.exists() else []
        hits = [f for f in files if f.startswith("problems_") or f == "flow.json"]
        if not hits:
            continue
        rows.append({
            "dir": str(d),
            "rel": str(d.relative_to(root)),
            "kind": d.parent.name if d.parent != root else d.name,
            "files": sorted(hits),
            "mtime": d.stat().st_mtime,
        })
        if len(rows) >= 60:
            break
    if as_json:
        emit_json(rows)
        return rows
    if not rows:
        print(f"{root} 下还没有产物。先跑一次：ask-dao-machine run <论文>")
        return rows
    import time as _t
    print(f"跑过的产物（{root}）：")
    for r in rows:
        ts = _t.strftime("%m-%d %H:%M", _t.localtime(r["mtime"]))
        print(f"  {ts}  {r['rel']}")
        print(f"          {' · '.join(r['files'])}")
    print()
    print("接报告：  ask-dao-machine report --out <上面任一路径>")
    return rows
