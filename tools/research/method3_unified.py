# -*- coding: utf-8 -*-
"""tools/research/method3_unified.py — 统一张力库(中31+西98) -> 注入生成 -> F4幸存 -> human_review
结果目标: 给出'当务H>=2 且机器可验/待裁决'的统一短名单, 并把数量与top写进台账。"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from big_score import score_text

HERE = Path(__file__).resolve().parent.parent


def gen(o):
    A = o["A"][0] if isinstance(o["A"], list) else o["A"]
    B = o["B"][0] if isinstance(o["B"], list) else o["B"]
    topic = o.get("topic", "张力")
    return [
        f"两套框架 '{A}' 与 '{B}' 能否统一? 冲突在哪一层(定义/前提/判定标准)?",
        f"若 '{A}' 成立, 是否与 '{B}' 相矛盾? 可消解还是真悖论?",
        f"何种判据能区分 '{A}' 与 '{B}' 两种立场?",
    ], topic


def main():
    pools = []
    for p in [HERE / "out/demo/tensions_v1.json", HERE / "out/demo/tensions_west.json"]:
        pools += json.loads(p.read_text(encoding="utf-8"))
    n0 = 0
    surv = []
    for o in pools:
        for s, topic in [gen(o)]:
            for t in s:
                n0 += 1
                sc = score_text(t)
                if sc["total"] >= 2.0:
                    surv.append({"topic": topic, "statement": t, "H": sc["total"]})
    surv.sort(key=lambda x: -x["H"])
    Path("out/demo/method3_unified_shortlist.json").parent.mkdir(parents=True, exist_ok=True)
    Path("out/demo/method3_unified_shortlist.json").write_text(
        json.dumps(surv, ensure_ascii=False, indent=1), encoding="utf-8")
    md = HERE / "docs/human_review_sheet.md"
    with md.open("a", encoding="utf-8") as f:
        f.write("\n## 统一张力注入短名单(METHODOLOGY3, 待人类裁决)\n")
        for s in surv[:20]:
            f.write(f"- H={s['H']} [{s['topic']}] {s['statement']}\n")
    print(f"统一张力池 {len(pools)} -> 生成 {n0} -> F4幸存 {len(surv)} (H>=2)")
    for s in surv[:8]:
        print(f"  H={s['H']} [{s['topic']}] {s['statement'][:70]}")


if __name__ == "__main__":
    main()
