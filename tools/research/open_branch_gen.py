# -*- coding: utf-8 -*-
"""tools/research/open_branch_gen.py — 人类已知开放问题 -> 相邻问题生成(领域融合分支)（R60）

用户: "能在这些人类已知的开放问题上做问题树生成与领域融合吗, 看看能不能找出新问题。"

方法: 不重复问主干(人类已知), 而是问**相邻/分支问题**:
  - 参数泛化: 把开放问题里的参数放开(如 完全数 k=2 -> σ(n)=k·n 的 k 泛化)
  - 跨域表述: 用别的领域的量重新表述(如 曲线直线比较 -> 熵/复杂度刻画)
  - 密度/计数: 问"有多少"而非"是否存在"

选两个可计算的开放问题做分支:
  A 奇完全数(k=2): 泛化到 σ(n)=k·n, 枚举小 k 是否有解(机器可算)
  B π³ 有理倍数: 用高精度计算 π³ 看它是否接近某有理数(机器可测)
"""
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def sigma(n):
    s, d = 1, 2
    m = n
    while d * d <= m:
        if m % d == 0:
            p = 1
            while m % d == 0:
                m //= d
                p = p * d + 1
            s *= p
        d += 1
    if m > 1:
        s *= (1 + m)
    return s


def branch_A_perfect_generalization(N=100000):
    """奇完全数(k=2) -> 泛化: σ(n) = k·n 对 k≠2 是否有解? (机器可枚举)"""
    rows = []
    for k in range(1, 8):
        found = []
        for n in range(2, N, 2 if k == 2 else 1):
            if sigma(n) == k * n:
                found.append(n)
                if len(found) >= 3:
                    break
        rows.append({"k": k, "solutions": found,
                     "known": "奇完全数未解(人类已知)" if k == 2 else
                              ("k=1 平凡(仅 n=1)" if k == 1 else f"k={k} 小解(机器扫到{N})")})
    return rows


def branch_B_pi3_rational(N=100):
    """π³ 有理倍数 -> 用连分数看 π³ 是否接近低分母有理数。"""
    # 高精度 π³(用 math.pi 不够, 用分数逼近)
    # π³ ≈ 31.0062766802998201754763150671
    pi3 = Fraction(310062766802998201754763150671, 10**28)
    # 连分数逼近, 找分母小的好逼近
    from fractions import Fraction as F
    a, b = pi3.numerator, pi3.denominator
    cf = []
    while len(cf) < N and b:
        cf.append(a // b)
        a, b = b, a % b
    # 用连分数前 n 项逼近
    best = []
    for depth in range(1, min(N, len(cf))):
        num, den = 1, 0
        for c in reversed(cf[:depth]):
            num, den = den + c * num, num
        # 逼近误差
        err = abs(F(num, den) - pi3)
        best.append((depth, num, den, float(err)))
    best.sort(key=lambda x: x[3])
    top = best[:5]
    return {"pi3_approx": "31.006276680299820...", "best_rational_approx": top}


def main():
    print("=" * 100)
    print("开放问题 -> 相邻分支生成(领域融合)")
    print("=" * 100)

    print("\n== 分支A: 奇完全数(k=2) -> 参数泛化 σ(n)=k·n ==")
    A = branch_A_perfect_generalization()
    for r in A:
        print(f"  k={r['k']}: 解 {r['solutions']}  {r['known']}")

    print("\n== 分支B: π³ 有理倍数 -> 连分数逼近 ==")
    B = branch_B_pi3_rational()
    print(f"  π³ ≈ {B['pi3_approx']}")
    print(f"  最佳低分母有理逼近:")
    for depth, num, den, err in B["best_rational_approx"][:5]:
        print(f"    {num}/{den} (分母{den}) 误差 {err:.2e}")

    print("\n" + "=" * 100)
    print("新问题候选(人类没直接问的相邻分支)")
    print("=" * 100)
    new_probs = [
        {"from": "奇完全数", "new_question":
         "σ(n)=k·n 对 k∈{3,4,5,6} 是否存在解? 哪些 k 有解, 哪些无?(参数泛化分支, 机器可枚举)",
         "judge_route": "数值枚举到 N"},
        {"from": "奇完全数", "new_question":
         "σ(n)=k·n 的解密度随 k 如何变化? 是否只对 k=2 特殊?(密度分支)",
         "judge_route": "数值统计"},
        {"from": "曲线直线比较", "new_question":
         "曲线与直线的'比较'能否用**局部复杂度(曲率/熵)**重新表述, 变成一个可判的数值问题?(跨域表述)",
         "judge_route": "计算几何/信息论"},
        {"from": "π³有理倍数", "new_question":
         "π³ 是否落在某个**低分母有理数**的 δ-邻域? 若否, 连分数系数的增长律是什么?(计算分支)",
         "judge_route": "连分数+高精度计算"},
    ]
    for p in new_probs:
        print(f"  从「{p['from']}」长出:")
        print(f"    ? {p['new_question']}")
        print(f"      路由: {p['judge_route']}")

    print("\n诚实: 这些**相邻分支**是机器从已知开放问题长出的; 它们**可能**比主干更易推进,")
    print("  且是'参数泛化/跨域表述'的产物 —— 是否文献未见需查证。")

    (HERE / "out/demo/open_branch.json").write_text(
        json.dumps({"A_perfect": A, "B_pi3": B, "new_problems": new_probs},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n已存 out/demo/open_branch.json")


if __name__ == "__main__":
    main()
