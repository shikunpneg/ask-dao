# -*- coding: utf-8 -*-
"""把 src/ask_dao_machine/ 的模块按功能重命名，并更新全仓库引用。

为什么用脚本而不是手工：36 个文件 + 大量引用点，手工一轮轮改容易漏；
脚本是确定性的，且可以先 --dry-run 看全貌再落盘。

只改「文件名 + 引用」，不改任何逻辑、不改子命令名、不改用户可见文案。
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent      # 脚本在 tools/ 下，上跳一级才是仓库根
SRC = ROOT / "src" / "ask_dao_machine"

# 旧名(不含 .py) -> 新名(不含 .py)
RENAME = {
    "_console": "ui_console",
    "banner": "ui_banner",
    "ux": "ui_ux",
    "cli": "interface_cli",
    "mcp": "interface_mcp",
    "flow": "pipeline_router",
    "paper": "input_paper",
    "perceive": "input_image",
    "report": "output_report",
    "viz": "output_viz",
    "doctor": "diagnose_env",
    "model": "data_problem_model",
    "registry": "data_motif_registry",
    "grammar": "data_combo_grammar",
    "domains_biomed": "domain_pack_biomed",
    "preproblems": "stage_preproblems",
    "pipeline": "stage_pipeline",
    "novelty_judge": "judge_novelty",
    "verifier": "judge_verifier",
    "judges_math": "judge_math",
    "judge_blueprints": "judge_blueprint",
    "motif_composer": "motif_compose",
    "motif_growth": "motif_grow",
    "aesthetics_engine": "engine_aesthetics",
    "break_engine": "engine_break",
    "combo_engine": "engine_combo",
    "counterex_engine": "engine_counterexample",
    "direction_engine": "engine_direction",
    "fusion_engine": "engine_fusion",
    "lang_info_engine": "engine_language_info",
    "math_engine": "engine_math",
    "records_engine": "engine_records",
    "sparse_engine": "engine_sparse",
    "territory_engine": "engine_territory",
}

SCAN_SUFFIX = {".py", ".yml", ".yaml", ".toml", ".md", ".html", ".txt", ".cfg", ".json"}
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".dsh-uploads", "out", "data",
             ".dsh-vision-toolkit", ".venv", "build", "dist", "handoff",
             "ask_dao_machine.egg-info"}          # egg-info 是构建产物，会被重新生成
# 这个脚本自己不能被扫到：它含有映射表与说明文字，改了就自毁
SKIP_FILES = {"rename_modules.py"}


def rewrite_text(text: str) -> tuple[str, int]:
    """按「旧名 -> 新名」改写引用。只碰 import 形式与文件路径形式，不碰裸词。"""
    n = 0
    for old, new in RENAME.items():
        before = text
        # from .old import      /  from .old.sub import
        text = re.sub(rf"(from\s+\.{re.escape(old)})(\b)", rf"from .{new}\2", text)
        # from . import old
        text = re.sub(rf"(from\s+\.\s+import\s+){re.escape(old)}\b", rf"\1{new}", text)
        # from ask_dao_machine.old import   /   ask_dao_machine.old.x
        text = re.sub(rf"(ask_dao_machine\.){re.escape(old)}\b", rf"\1{new}", text)
        # 路径字面量：src/ask_dao_machine/old.py、ask_dao_machine\old.py
        text = re.sub(rf"(ask_dao_machine[/\\]){re.escape(old)}\.py", rf"\1{new}.py", text)
        # 产物里的自述路径：ask-dao-machine/paper.py
        text = re.sub(rf"(ask-dao-machine/){re.escape(old)}\.py", rf"\1{new}.py", text)
        if text != before:
            n += 1
    return text, n


def scan_files() -> list[Path]:
    out: list[Path] = []
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in SCAN_SUFFIX:
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.name in SKIP_FILES:
            continue
        if p.stat().st_size > 2_000_000:
            continue
        out.append(p)
    return sorted(out)


def changed_lines(old: str, new: str) -> list[tuple[int, str, str]]:
    """逐行对比，返回 (行号, 改前, 改后)——dry-run 时给人工核对。"""
    out = []
    for i, (a, b) in enumerate(zip(old.splitlines(), new.splitlines()), 1):
        if a != b:
            out.append((i, a.strip()[:110], b.strip()[:110]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="真的改（默认只 dry-run）")
    ap.add_argument("--show", type=int, default=40, help="dry-run 最多打印多少行改动")
    a = ap.parse_args()

    # ── 1) 文件重命名 ──
    moves = []
    for old, new in RENAME.items():
        src, dst = SRC / f"{old}.py", SRC / f"{new}.py"
        if src.exists():
            moves.append((src, dst))
        elif not dst.exists():
            print(f"  [跳过] {old}.py 不存在", file=sys.stderr)

    print(f"=== 待重命名 {len(moves)} 个模块 ===")
    for s, d in moves:
        print(f"  {s.name:24} -> {d.name}")

    # ── 2) 扫描引用 ──
    print(f"\n=== 引用改写 ===")
    hits: list[tuple[Path, int, str, str]] = []
    for p in scan_files():
        try:
            t = p.read_text(encoding="utf-8")
        except Exception:
            continue
        t2, n = rewrite_text(t)
        if n:
            hits.append((p, n, t, t2))
    for s, _d in moves:                       # 被移动的文件自身也要改
        try:
            t = s.read_text(encoding="utf-8")
        except Exception:
            continue
        _t2, n = rewrite_text(t)
        if n:
            hits.append((s, n, t, _t2))

    shown = 0
    for p, n, t, t2 in hits:
        print(f"\n  {p.relative_to(ROOT)}  （{n} 个模块名）")
        for ln, before, after in changed_lines(t, t2):
            if shown >= a.show and not a.apply:
                print(f"    … 还有更多，用 --show 调大")
                break
            print(f"    L{ln}")
            print(f"      - {before}")
            print(f"      + {after}")
            shown += 1

    if not a.apply:
        print(f"\n[dry-run] 会改 {len(moves)} 个文件名 + {len(hits)} 个文件的引用。"
              f"\n加 --apply 真的执行。")
        return 0

    # ── 3) 落盘：先改内容，再 git mv ──
    for p, _n, _t, _t2 in hits:
        try:
            t = p.read_text(encoding="utf-8")
            p.write_text(rewrite_text(t)[0], encoding="utf-8")
        except Exception as e:                                    # noqa: BLE001
            print(f"  [警告] 改写失败 {p}: {e}", file=sys.stderr)

    for s, d in moves:
        r = subprocess.run(["git", "mv", str(s), str(d)], cwd=ROOT,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            s.rename(d)                       # 不在 git 里就普通移动
    print(f"\n[apply] 已重命名 {len(moves)} 个模块，改写 {len(hits)} 个文件的引用。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
