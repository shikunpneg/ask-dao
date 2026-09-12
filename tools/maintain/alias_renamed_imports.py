# -*- coding: utf-8 -*-
"""补漏 2：`from . import new_X` 要写成 `from . import new_X as old_X`。

为什么不用"把调用点也全改掉"：调用点遍布各文件（`aesthetics_engine.run` 这种），
逐一改风险大、review 难。在**导入处加别名**是等价且最小的改动——
文件名按功能改了，代码一处不用动。

只处理 `from . import ...` 这一种形式（单名 / 逗号 / 括号列表都覆盖）。
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
REV = {v: k for k, v in RENAME.items()}          # 新名 -> 旧名（别名）

PAT = re.compile(r"(from\s+\.\s+import\s+)(\([^)]*\)|[A-Za-z_][\w\s,]*)", re.S)


def fix_names(body: str) -> tuple[str, int]:
    n = 0

    def one(m):
        nonlocal n
        name = m.group(0)
        old = REV.get(name)
        if not old:
            return name
        n += 1
        return f"{name} as {old}"

    return re.sub(r"[A-Za-z_]\w*", one, body), n


def main():
    changed = 0
    for p in sorted(ROOT.rglob("*.py")):
        if any(s in p.parts for s in (".git", "__pycache__", "out", "data", "handoff",
                                      "ask_dao_machine.egg-info")):
            continue
        if p.name in ("fix_multiname_imports.py", "rename_modules.py"):
            continue
        try:
            t = p.read_text(encoding="utf-8")
        except Exception:
            continue
        total = 0

        def repl(m):
            nonlocal total
            head, body = m.group(1), m.group(2)
            if " as " in body:                    # 已经有别名，跳过
                return m.group(0)
            body2, n = fix_names(body)
            total += n
            return head + body2

        t2 = PAT.sub(repl, t)
        if t2 != t and total:
            p.write_text(t2, encoding="utf-8")
            changed += 1
            print(f"  加别名 {p.relative_to(ROOT)}  （{total} 处）")
    print(f"\n补漏 2 完成：{changed} 个文件")


if __name__ == "__main__":
    main()
