# -*- coding: utf-8 -*-
"""补漏：`from . import (a, b, c)` 这种多名字括号形式，rename_modules.py 的正则没覆盖。

只改括号内列出的模块名（按同一张对照表），不碰其它任何内容。
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RENAME = {
    "_console": "ui_console", "banner": "ui_banner", "ux": "ui_ux",
    "cli": "interface_cli", "mcp": "interface_mcp", "flow": "pipeline_router",
    "paper": "input_paper", "perceive": "input_image", "report": "output_report",
    "viz": "output_viz", "doctor": "diagnose_env", "model": "data_problem_model",
    "registry": "data_motif_registry", "grammar": "data_combo_grammar",
    "domains_biomed": "domain_pack_biomed", "preproblems": "stage_preproblems",
    "pipeline": "stage_pipeline", "novelty_judge": "judge_novelty",
    "verifier": "judge_verifier", "judges_math": "judge_math",
    "judge_blueprints": "judge_blueprint", "motif_composer": "motif_compose",
    "motif_growth": "motif_grow", "aesthetics_engine": "engine_aesthetics",
    "break_engine": "engine_break", "combo_engine": "engine_combo",
    "counterex_engine": "engine_counterexample", "direction_engine": "engine_direction",
    "fusion_engine": "engine_fusion", "lang_info_engine": "engine_language_info",
    "math_engine": "engine_math", "records_engine": "engine_records",
    "sparse_engine": "engine_sparse", "territory_engine": "engine_territory",
}
NEW = set(RENAME.values())

# 匹配 from . import ( ... )  或  from . import a, b, c
PAT = re.compile(r"(from\s+\.\s+import\s+)(\([^)]*\)|[A-Za-z_][\w,\s]*)")


def fix_body(body: str) -> tuple[str, int]:
    n = 0

    def one(m):
        nonlocal n
        name = m.group(0).strip()
        if name in NEW:
            return name
        if name in RENAME:
            n += 1
            return RENAME[name]
        return name

    # 逐个标识符替换（保留逗号、空白、括号、换行）
    body2 = re.sub(r"[A-Za-z_]\w*", one, body)
    return body2, n


def main():
    changed = 0
    for p in sorted(ROOT.rglob("*.py")):
        if any(s in p.parts for s in (".git", "__pycache__", "out", "data", "handoff")):
            continue
        try:
            t = p.read_text(encoding="utf-8")
        except Exception:
            continue
        total = 0

        def repl(m):
            nonlocal total
            head, body = m.group(1), m.group(2)
            if head.rstrip().endswith("import") and "," not in body and "(" not in body:
                # 单名字的情况 rename_modules 已经处理过；这里再兜一次
                pass
            body2, n = fix_body(body)
            total += n
            return head + body2

        t2 = PAT.sub(repl, t)
        if t2 != t and total:
            p.write_text(t2, encoding="utf-8")
            changed += 1
            print(f"  修补 {p.relative_to(ROOT)}  （{total} 个名字）")
    print(f"\n补漏完成：{changed} 个文件")


if __name__ == "__main__":
    main()
