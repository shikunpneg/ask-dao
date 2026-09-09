# -*- coding: utf-8 -*-
"""viz.py — 从 ProblemSet + Registry 构建可视化 (data.js), 并复制模板 index.html。
可视化使命: 让每个问题可以被解释 —— 母题组合链/模板/参数/判定记录/诚实标签 + 树生长路径。"""
import json
from collections import Counter
from pathlib import Path
from typing import Dict, List

from .model import ProblemSet
from .registry import Registry


def _reg_block(reg: Registry) -> dict:
    return {"total": reg.total, "math_core": len(reg.math_core),
            "domains": reg.domain_counts(), "domain_detail": reg.domains}


def build_data(sets: Dict[str, ProblemSet], reg: Registry) -> dict:
    usage = Counter()
    roots, problems = [], []
    for ps in sets.values():
        roots.extend({"id": r.id, "label": r.label, "domain": r.domain,
                      "motifs": r.motifs, "seed": r.seed} for r in ps.roots)
        for p in ps.problems:
            d = p.to_dict()
            d["motifs"] = p.motifs
            d["status"] = p.status
            d["tag"] = p.honesty
            problems.append(d)
            for m in p.motifs:
                usage[m] += 1
    motifs_math = [{"name": m["name"], "type": m["type"], "note": m["note"],
                    "used": usage.get(m["name"], 0)} for m in reg.math_core]
    aesthetics = [d for d in problems if d["domain"] == "美学"]
    math_problems = [d for d in problems if d["domain"] == "数学"]
    for a in aesthetics:
        a["motifs"] = " × ".join(a["motifs"])
    return {"registry": _reg_block(reg), "motifs_math": motifs_math,
            "roots": roots, "problems": math_problems, "aesthetics": aesthetics}


def make_viz(out_dir: Path, sets: Dict[str, ProblemSet], reg: Registry,
             template: Path) -> Path:
    out_dir = Path(out_dir)
    viz_dir = out_dir / "viz"
    viz_dir.mkdir(parents=True, exist_ok=True)
    data = build_data(sets, reg)
    (viz_dir / "data.js").write_text(
        "window.DATA = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n",
        encoding="utf-8")
    if template.exists():
        (viz_dir / "index.html").write_text(template.read_text(encoding="utf-8"),
                                            encoding="utf-8")
    else:
        raise FileNotFoundError(f"缺可视化模板: {template}")
    return viz_dir
