# -*- coding: utf-8 -*-
"""motif_composer.py — 母题层自动组合器(第一版):
  按"类型兼容"把两个母题拼成候选复合母题(derived motif), 标出:
    - 适合的句式(frame)
    - 判定路由: math可判(fusion) / blueprint(实验)
    - 父母题(树生长溯源)
  注意: 产出的是"候选复合基元", 尚未实例化成问题——实例化由对应引擎/句式完成。"""
import json
from pathlib import Path
from typing import List

from .registry import Registry

# 复合母题生成规则: (类型A, 类型B) -> 复合类型 + 建议句式 + 判定路由
RULES = {
    # 数学内部(数值可判 -> fusion/math)
    ("对象类", "域构造"): ("受限对象", "F_threshold_sum", "math"),
    ("对象类", "对象类"): ("配对集", "F_threshold_sum", "math"),
    ("映射", "域构造"): ("值域受限映射", "F_parity_char", "math"),
    ("映射", "映射"): ("复合映射", "F_exist_equal", "math"),
    ("映射", "对象类"): ("映射作用对象", "F_char_if", "math"),
    ("规则", "对象类"): ("结构族", "F_threshold_sum", "math"),
    ("映射", "规则"): ("生成-映射链", "F_recur_converge", "math"),
    # 跨域(数值可判: 别域度量/机制 x 数学对象)
    ("度量", "对象类"): ("度量×对象", "F_record_max", "math"),
    ("关系", "对象类"): ("关系×对象", "F_exist_equal", "math"),
    # 跨域(需实验/人类判官 -> blueprint)
    ("机制", "解释类型"): ("机制组合", "F_recur_converge", "blueprint"),
    ("映射", "过程"): ("过程度量", "F_recur_converge", "blueprint"),
    ("结构", "对象"): ("结构×对象", "F_exist_equal", "blueprint"),
    ("解释类型", "度量"): ("解释-度量", "F_interval_exist", "blueprint"),
}


def compose(registry: Registry, cross_domains: bool = True,
            max_pairs: int = 200) -> List[dict]:
    pools = []
    for m in registry.math_core:
        pools.append({"domain": "数学", **m})
    if cross_domains:
        for dom, items in registry.domains.items():
            if dom in ("元层",):
                continue
            for m in items:
                pools.append({"domain": dom, **m})
    out = []
    used = set()
    for i in range(len(pools)):
        for j in range(i + 1, len(pools)):
            a, b = pools[i], pools[j]
            rule = RULES.get((a["type"], b["type"])) or RULES.get((b["type"], a["type"]))
            if not rule:
                continue
            if a["domain"] == b["domain"] == "数学" and a["name"] == b["name"]:
                continue
            key = tuple(sorted((a["domain"], a["name"], b["domain"], b["name"])))
            if key in used:
                continue
            used.add(key)
            ctype, frame, route = rule
            out.append({
                "id": f"DM{len(out):03d}",
                "derived": f"{a['name']} × {b['name']}",
                "type": ctype,
                "parents": [f"{a['domain']}::{a['name']}", f"{b['domain']}::{b['name']}"],
                "cross": a["domain"] != b["domain"],
                "frame": frame,
                "route": route,
                "note": f"复合母题候选: {a['name']}({a['type']}) 与 {b['name']}({b['type']}) 组合; "
                        f"若route=math则可由对应引擎直接实例化判定, 若blueprint则进 judge_blueprints",
            })
    # 采样优先级: blueprint 实验类 > 跨域 > 数学核心; 总量 80
    out.sort(key=lambda r: (0 if r["route"] == "blueprint" else 1,
                            0 if r["cross"] else 1,
                            r["derived"]))
    return out[:80]


def main(out_path: str = "out/demo/derived_motifs.json") -> dict:
    reg = Registry.bundled()
    res = compose(reg)
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    by_route = {"math": 0, "blueprint": 0}
    for r in res:
        by_route[r["route"]] = by_route.get(r["route"], 0) + 1
    return {"total": len(res), "by_route": by_route, "file": str(p)}


if __name__ == "__main__":
    print(main())
