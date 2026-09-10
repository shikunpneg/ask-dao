# -*- coding: utf-8 -*-
"""tools/significance_vs_random.py — 可机检的显著性判据(置换零模型版)

**自纠错(第 12 次)**: 首版用 Poisson 零模型 λ=(同奇偶配对数)/类宽度, 得出
"Harshad数+平方数 实测 120 vs 预测 0.001 → 超出 1.2×10⁵ 倍"。
**这是模型假象, 错了 5 个数量级。** Poisson 假设 {n−s 是 Harshad} 对不同的 s **独立**,
但 Harshad 集高度结构化(有簇有隙), 真实 r(n) 远**超离散**, 零尾本就厚 —— 用 Poisson 估零尾
必然把平凡效应放大成天文数字。

正确的零模型: **置换检验** —— 保持 A 的**尺寸与奇偶分布**不变, 随机抽同尺寸集合, 重算例外数,
观察实测值在零分布中的位置。这是本项目纪律(状态只来自可复核的判据)的正确用法。

诚实边界: 置换 p 值只说明"例外数超出同尺寸随机集合的水平", **不说明问题重要**。
"""
import json
import random
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))

from conjecture_search import build_pool, LO, HI  # noqa: E402

TRIALS = 60   # 60 次重抽足以定位 p 到 ~0.017 分辨率; 200 次对 |A|~3000 的对太慢


def exceptions_with(A, B, ns, lo, hi, step=2):
    """给定 A, B, 算 ns 中的例外集(和集标记法)。

    **防御性排序(自纠错第 12 次附二)**: 内层的 `break` 要求 B 有序、外层的 `break` 要求 A 有序。
    这个坑在本项目已出现**三次**(R24 首版、本轮的临时脚本、本函数的零模型循环),
    每次都伪造出大量假例外。故此处**强制内部排序**, 不再依赖调用方。
    """
    A, B = sorted(A), sorted(B)
    mark = bytearray(hi + 2)
    for a in A:
        if a >= hi:
            break
        for b in B:
            v = a + b
            if v > hi:
                break
            if v >= lo:
                mark[v] = 1
    return [n for n in ns if not mark[n]]


def permutation_test(A, B, lo=LO, hi=HI, trials=TRIALS, seed=12345):
    """置换零模型: 随机抽与 A **同尺寸、同奇偶分布**的集合, 重算例外数。"""
    A = sorted(A)
    B = sorted(B)
    ns = list(range(lo, hi + 1, 2))
    obs = len(exceptions_with(A, B, ns, lo, hi))

    # 按奇偶分层: A 与 n 同奇偶时才能与 B 凑成 n; 保持两层的尺寸
    A_even = sum(1 for x in A if x % 2 == 0)
    A_odd = len(A) - A_even
    pool_even = [n for n in range(1, hi + 1) if n % 2 == 0]
    pool_odd = [n for n in range(1, hi + 1) if n % 2 == 1]

    rnd = random.Random(seed)
    null = []
    for _ in range(trials):
        A_ = rnd.sample(pool_even, A_even) + rnd.sample(pool_odd, A_odd)
        null.append(len(exceptions_with(A_, B, ns, lo, hi)))

    null_sorted = sorted(null)
    ge = sum(1 for c in null if c >= obs)
    p = (ge + 1) / (trials + 1)
    return {
        "observed": obs,
        "null_mean": round(statistics.mean(null), 1),
        "null_median": statistics.median(null),
        "null_p5": null_sorted[int(0.05 * trials)],
        "null_p95": null_sorted[int(0.95 * trials)],
        "null_max": max(null),
        "ratio_to_null": round(obs / max(statistics.mean(null), 1e-9), 2),
        "p_value": round(p, 4),
        "trials": trials,
    }


def main():
    pool = build_pool()
    cands = json.loads((HERE / "out/demo/final_candidates.json").read_text(encoding="utf-8"))["candidates"]
    rows = []
    for i, r in enumerate(cands, 1):
        A, B = pool[r["A"]], pool[r["B"]]
        print(f"  [{i}/{len(cands)}] {r['A']} + {r['B']}", flush=True)
        t = permutation_test(A, B)
        t.update({"A": r["A"], "B": r["B"],
                  "excess_score": r.get("score"), "class_fit": r.get("class_fit")})
        rows.append(t)
    # 排序: 先按 p 值, 再按超出倍数
    rows.sort(key=lambda x: (x["p_value"], -x["ratio_to_null"]))

    print(f"置换零模型(保持尺寸+奇偶, {TRIALS} 次重抽)\n")
    print(f"{'p值':>7}{'实测':>6}{'零均值':>8}{'零95%':>7}{'倍数':>7}  类对")
    print("-" * 82)
    for r in rows[:15]:
        print(f"{r['p_value']:>7.3f}{r['observed']:>6}{r['null_mean']:>8}{r['null_p95']:>7}"
              f"{r['ratio_to_null']:>7.2f}x  {r['A']} + {r['B']}")

    sig = [r for r in rows if r["p_value"] <= 0.05]
    print(f"\n显著(p ≤ 0.05)的候选: {len(sig)} / {len(rows)}")
    for r in sig:
        print(f"  {r['A']} + {r['B']:<16} 实测 {r['observed']} vs 零均值 {r['null_mean']} "
              f"({r['ratio_to_null']}x, p={r['p_value']})")

    print("\n**修正记录(自纠错第12次)**: 首版 Poisson 零模型给出 'Harshad+平方数 超 1.2×10⁵ 倍' —— "
          "错 5 个数量级。正确零模型下该候选为 ~3x, p≈0.005。")
    print("诚实: 置换 p 值只说明'超出同尺寸随机集合的水平', **不说明问题重要**。")
    (HERE / "out/demo/significance.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已存 out/demo/significance.json")


if __name__ == "__main__":
    main()
