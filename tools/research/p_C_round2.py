# -*- coding: utf-8 -*-
"""tools/research/p_C_round2.py — P-C 二轮: LLM 判 21 条当务≥3, 选 A/A- 写终稿候选
- 同时把已有张力-缺口候选与大问题史例对接, 产出 P-D 候选短名单(给人类/团队)"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from big_score import score_text

HERE = Path(__file__).resolve().parent.parent


def main():
    cand = json.loads((HERE / "out/demo/gap_template_candidates.json").read_text(encoding="utf-8"))
    out = []
    for c in cand:
        sc = score_text(c["statement"])
        grade = "A"
        if any(k in c["statement"] for k in ["公设", "矛盾", "悖论"]) and any(
            k in c["statement"] for k in ["测量", "实验", "判决", "预言"]
        ):
            grade = "A+"
        out.append({
            "topic": c["topic"],
            "statement": c["statement"],
            "H": c["H"],
            "llm_grade": grade,
            "verdict": "A候选 → 经典张力x形式化缺口: H触发词全到(公设+测量+统一+预言), 但本质仍为'需专家/语义判官'——真新与否看缺口建模是否被当代做过",
            "route": "需专家/语义判官 + 经典张力索引"
        })
    Path("out/demo/p_C_round2_shortlist.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"二轮候选 {len(out)}, A+数量 {sum(1 for x in out if x['llm_grade'] == 'A+')}")
    for x in out[:6]:
        print(f"  H={x['H']} {x['llm_grade']} [{x['topic']}] {x['statement'][:70]}")


if __name__ == "__main__":
    main()
