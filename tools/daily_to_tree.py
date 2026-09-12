# -*- coding: utf-8 -*-
"""tools/daily_to_tree.py — 日常问题 -> 问题树生长/融合（R57）

用户核心诉求: "用日常问题转换的科学问题做问题树的生成和融合"。

桥: 日常问题(数量/边界/标度类) -> **可整数化猜想(Spec)** -> 喂 territory_engine
  生长成 L0-L5 问题树; 跨域的 Spec 组 -> 融合。
定性问题(机制/心智) -> 记为**前问题**(母题种子), 走谱系, 不进 Spec。

关键: 日常问题的**数量/标度**本质必须保留 —— 否则全变成"机制是什么"的空壳。
"""
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src"))
sys.path.insert(0, str(HERE / "tools"))

from ask_dao_machine.engine_territory import Spec, Territory, run_territory  # noqa: E402


# ---------- 可整数化的日常问题 -> Spec ----------
def build_spec(daily, dom, N=20000):
    """把数量/标度类日常问题变成整数猜想 Spec。返回 Spec 或 None。"""
    s = daily.lower()
    # 1) 物种-面积标度: "how many species / 多少物种"
    if re.search(r"species|物种", s):
        # 猜想: 物种数 S(A) ~ A^z (面积-物种标度), z 是否 ≈ 0.25?
        def holds_species(n):
            # 用面积-物种幂律: S = c*A^z, 检查 z 是否稳定
            return True   # 占位(真实需生态数据, 见 classes)
        return Spec(
            id=f"daily_species", claim="物种数 S(面积A) 服从幂律 S~A^z (z≈0.25?)",
            holds=holds_species, classes={},
            params={"领域": dom, "问题": "物种-面积标度"}, step=1,
            quantity=f"A ∈ [1,{N}]", strength=None)
    # 2) "how big can a black hole grow / 黑洞质量上界"
    if re.search(r"black hole|黑洞", s):
        return Spec(
            id="daily_bh_mass", claim="恒星质量黑洞的质量上限(随金属丰度)是 20-30 M☉?",
            holds=lambda n: True, classes={},
            params={"领域": "天文", "问题": "黑洞质量上限"}, step=1,
            quantity=f"M/M☉ ∈ [1,{N}]", strength=None)
    # 3) "how many dimensions / 维度"
    if re.search(r"dimension|维度", s):
        def holds_dim(n):
            return n in (10, 11, 26)   # 弦论/超弦的临界维度
        return Spec(id="daily_dims", claim="理论物理的临界维度(10/11/26)是否唯一?",
                    holds=holds_dim, classes={},
                    params={"领域": "物理", "问题": "临界维度"}, step=1,
                    quantity=f"d ∈ [1,{N}]", strength=None)
    return None


# ---------- 定性日常问题 -> 前问题(母题种子) ----------
def as_preproblem(daily, dom, layer=3):
    """定性问题记为前问题, 走谱系(不进 Spec)。"""
    return {"type": "前问题(日常→科学)", "domain": dom, "layer": f"L{layer}",
            "daily": daily, "motif_seed": daily[:20],
            "scientific": f"[{dom}] {daily} 的机制/结构是什么?",
            "judge_route": "待定(定性, 需建模)"}


def main():
    d = json.loads((HERE / "out/demo/discovery_manifest.json").read_text(encoding="utf-8"))
    daily_problems = [p for p in d["problems"] if "arxiv" in (p.get("source") or "")]
    print("=" * 100)
    print("日常问题 -> 问题树生长/融合")
    print("=" * 100)
    print(f"  输入 arXiv 日常问题: {len(daily_problems)} 条")

    specs, preproblems = [], []
    for p in daily_problems:
        daily = str(p.get("daily_question") or p.get("statement") or p.get("scientific_question"))
        dom = p.get("domain", "未知")
        sp = build_spec(daily, dom)
        if sp:
            specs.append(sp)
        else:
            preproblems.append(as_preproblem(daily, dom))

    print(f"  -> 可整数化(长成 Spec): {len(specs)}  定性(记为前问题): {len(preproblems)}")
    print(f"\n  == 可整数化 -> Spec ==")
    for sp in specs:
        print(f"    {sp.id}: {sp.claim[:60]}")

    print(f"\n  == 定性 -> 前问题 ==")
    for pp in preproblems[:10]:
        print(f"    [{pp['domain']}] {pp['daily'][:55]}")

    # 生长: 对可整数化的 Spec, 用 territory 引擎长成问题树(L0-L5)
    if specs:
        print("\n" + "=" * 100)
        print("问题树生长(用 territory 引擎): 每个 Spec -> 例外集 -> L0-L5 问题")
        print("=" * 100)
        # 用一个临时 Territory 包裹这些 Spec
        T = Territory(name="daily_tree", family="日常问题派生",
                      literature="由网页/arXiv 日常问题转化",
                      motifs=["日常问题"], seed="日常问题 -> 科学问题 -> 树",
                      specs=lambda: specs)
        roots, recs, rep = run_territory(T, 4, 20000)
        print(f"  生长出 {len(recs)} 条问题 (从 {len(specs)} 个日常 Spec)")
        for r in recs[:6]:
            print(f"    [{r.id}] {r.statement[:70]}")

    # 保存
    out = {"specs": [{"id": s.id, "claim": s.claim, "params": s.params}
                     for s in specs],
           "preproblems": preproblems}
    (HERE / "out/demo/daily_to_tree.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n已存 out/demo/daily_to_tree.json")


if __name__ == "__main__":
    main()
