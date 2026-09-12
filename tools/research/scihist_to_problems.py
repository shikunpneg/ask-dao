# -*- coding: utf-8 -*-
"""tools/research/scihist_to_problems.py — 科学史开放点 -> 正式问题 + 树融合（R59）

把 32 个 A 级科学史开放点提升为正式问题(每个指向真实未解/悬置), 并入 manifest;
再和跨进制问题树做**融合**(前问题并入谱系)。
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def sci_to_problem(h):
    """A 级开放点 -> 正式问题。"""
    ctx = h["context"]
    # 从上下文提取"对象"(尝试)
    return {
        "id": f"SCIHIST_{h['file'][:6]}_{h['para']}",
        "domain": "科学史", "source": f"书:{h['file']}",
        "statement": f"[科学史] {ctx[:90]}… 的答案/机制是什么?",
        "conjecture": "科学史自标未解/悬置",
        "evidence": {"signal": h["signal"], "context": ctx[:120]},
        "judge_route": "文献查证(是否仍开放)", "status": "未查证(科学史自标未知)",
        "layer": "L1",
    }


def main():
    sci = json.loads((HERE / "out/demo/scihist_open.json").read_text(encoding="utf-8"))
    probs = [sci_to_problem(h) for h in sci["A"]]
    print(f"科学史 A 级开放点 -> {len(probs)} 条正式问题")
    for p in probs[:5]:
        print(f"  [{p['statement'][:60]}")

    # 并入 manifest
    man = HERE / "out/demo/discovery_manifest.json"
    d = json.loads(man.read_text(encoding="utf-8"))
    d["problems"] += probs
    d["count"] = len(d["problems"])
    man.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n已并入 discovery_manifest (总数 {d['count']})")

    # 融合: 科学史前问题 -> 跨进制树的谱系(做一个"融合树"演示)
    print("\n" + "=" * 100)
    print("树融合: 跨进制问题树 × 科学史前问题")
    print("=" * 100)
    # 跨进制树的 _holds 问题(零例外"是否定理") 与 科学史"奇完全数" 融合
    tree = json.loads((HERE / "out/demo/palbase_tree.json").read_text(encoding="utf-8"))
    holds = [r for r in tree["recs"] if "holds" in r.get("id", "")]
    print(f"  跨进制树 '是否定理' 问题: {len(holds)} 条")
    print(f"  例: {holds[0]['statement'][:70] if holds else '(无)'}")
    print(f"\n  科学史 A 级(未解): 32 条, 例:")
    for h in sci["A"][:5]:
        print(f"    - {h['context'][:70]}")
    print(f"\n  => 融合: '跨进制是否定理'(机器可判) 与 '科学史奇完全数'(千年未解)")
    print(f"     都是'断言是否成立'型问题 —— 同层(L1/L2), 可共用判定路由(数值+文献)。")

    out = HERE / "out/demo/scihist_problems.json"
    out.write_text(json.dumps(probs, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n已存 out/demo/scihist_problems.json")


if __name__ == "__main__":
    main()
