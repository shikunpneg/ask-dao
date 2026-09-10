# -*- coding: utf-8 -*-
"""tools/significance_vs_random.py — 可机检的显著性信号(回答 R23 的"显著性瓶颈")

R23 的结论是: **新颖性不是瓶颈, 显著性才是** —— 但当时没有机器可算的显著性判据。
本工具给出一个: **实测例外数 vs 随机模型预测例外数**。

原理:
  把两个对象类 A, B 看作区间上的随机子集(|A|, |B| 给定), 则 n 的表示数近似 Poisson(λ),
  λ = |A||B| / (区间内被考察的 n 的个数)。于是
        预测例外数 = Σ_n exp(−λ)
  若 **实测例外 ≫ 预测例外** ⇒ 例外不是随机噪声, 而是**有结构**(数位/奇偶/代数阻碍)。
  这是机器**能**诚实算的量, 不需要文献、不需要人类。

诚实边界: "显著" ≠ "重要"。本工具只证明"例外集有结构", 不证明"该问题值得研究"。
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))

from conjecture_search import build_pool, LO, HI  # noqa: E402


def representations(A, B, lo, hi):
    """每个 n 的表示数 r(n) = #{(a,b): a+b=n}"""
    cnt = {}
    for a in A:
        if a >= hi:
            break
        for b in B:
            s = a + b
            if s > hi:
                break
            if s >= lo:
                cnt[s] = cnt.get(s, 0) + 1
    return cnt


def analyze(a, b, pool, lo=LO, hi=HI, step=2, parity_aware=True):
    A, B = sorted(pool[a]), sorted(pool[b])
    cnt = representations(A, B, lo, hi)
    ns = list(range(lo, hi + 1, step))
    observed = [n for n in ns if cnt.get(n, 0) == 0]

    # 随机模型: 对每个 n, 可用配对数 = |{(x,y) ∈ A×B : x+y=n}| 在随机模型下的期望
    # 奇偶感知: 若 n 为偶, 只有同奇偶的 (x,y) 可凑成 n
    if parity_aware:
        nA = {0: sum(1 for x in A if x % 2 == 0), 1: sum(1 for x in A if x % 2 == 1)}
        nB = {0: sum(1 for x in B if x % 2 == 0), 1: sum(1 for x in B if x % 2 == 1)}
        span = hi - lo or 1
        pred = 0.0
        for n in ns:
            p = n % 2
            lam = nA[p] * nB[p] / (span / 2)      # 同奇偶配对数 / 该奇偶类的宽度
            pred += math.exp(-lam)
    else:
        lam = len(A) * len(B) / (len(ns) or 1)
        pred = sum(math.exp(-lam) for _ in ns)

    return {"A": a, "B": b, "|A|": len(A), "|B|": len(B),
            "n_scanned": len(ns), "observed": len(observed),
            "predicted": round(pred, 2),
            "excess": round(len(observed) / pred, 1) if pred > 1e-12 else None,
            "observed_density": round(len(observed) / len(ns), 5),
            "predicted_density": round(pred / len(ns), 8),
            "examples": observed[:8]}


def main():
    pool = build_pool()
    pairs = json.loads((HERE / "out/demo/final_candidates.json").read_text(encoding="utf-8"))["candidates"]
    rows = []
    for r in pairs:
        rows.append(analyze(r["A"], r["B"], pool))
    rows.sort(key=lambda x: -(x["excess"] or 0))

    print("显著性检验: 实测例外 vs 随机模型预测(奇偶感知)\n")
    print(f"{'超额倍数':>10}{'实测':>7}{'预测':>9}  类对")
    print("-" * 76)
    for r in rows[:15]:
        ex = f"{r['excess']:.0f}x" if r["excess"] else "∞"
        print(f"{ex:>10}{r['observed']:>7}{r['predicted']:>9.2f}  {r['A']} + {r['B']}")
    print("\n判读: 超额倍数 ≫ 1 ⇒ 例外集**有结构**(不是随机噪声); 这是机器能诚实算的显著性信号。")
    print("      倍数极高者(如 |A||B|/N ≫ 1 却仍有例外)最值得追 —— 随机模型本该全覆盖。")
    print("\n诚实: '显著' ≠ '重要'。本工具只证明例外集有结构, 不证明该问题值得研究。")
    (HERE / "out/demo/significance.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已存 out/demo/significance.json")


if __name__ == "__main__":
    main()
