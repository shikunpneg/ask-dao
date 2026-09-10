# -*- coding: utf-8 -*-
"""tools/p_C_ev_regrade.py — 整改后重跑: 证据依赖评分 vs 关键词评分"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from big_score_ev import score_ev

HERE = Path(__file__).resolve().parent.parent


def main():
    cands = json.loads((HERE / "out/demo/gap_template_candidates.json").read_text(encoding="utf-8"))
    rows = []
    for c in cands:
        r = score_ev(c)
        rows.append({"statement": c["statement"], "topic": c["topic"],
                     "H_keyword": c["H"], "H_evidence": r["total"], "notes": r["notes"]})
    pos = [x for x in rows if x["H_evidence"] > 0]
    ref = {"evidence": {"sources": [{"claim": "平行公设", "ref": "欧几里得原本"},
                                    {"claim": "非欧几何", "ref": "罗巴切夫斯基1829"}],
                        "distinct_frameworks": True, "axiom_ref": "欧几里得第五公设",
                        "age_years": 2000, "method_gap": "需要新几何", "route": "理论证明"}}
    print("参照史例(带证据) 当务分:", score_ev(ref)["total"])
    print(f"21 候选中 证据依赖分>0 的数量: {len(pos)} / {len(rows)}")
    for x in rows[:10]:
        print(f"  关键词{x['H_keyword']} -> 证据{x['H_evidence']} | {x['statement'][:50]}")
    out = HERE / "out/demo/p_C_evidence_regrade.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
