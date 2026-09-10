# -*- coding: utf-8 -*-
"""tools/mega_branch_scan.py — 全力扫描: 算术函数 x k泛化 x 奇偶 x 大N（R61）

用户: "加大力度, 不停, 全力扫描。"

思路: 完全数(k=2, σ(n)=2n)是已知; 但**泛化到不同算术函数**可能产生新图样:
  σ(n) 除数函数  -> k-perfect (已知, 但奇数版偏)
  φ(n) 欧拉函数  -> φ(n)=k·n 无解(k≥2, 因 φ(n)<n) -> 变 φ(n)=k·m 泛化? 或 φ(n) 的子结构
  τ(n) 除数个数  -> τ(n)=k 的解是"恰有 k 个因子的数"(已知), 但 τ(n)=k·n 恒假(τ<n)
  σ(n)-n 真因子和 -> k-perfect 的别名? 不, σ(n)-n = k·n => σ(n)=(k+1)n 是 k+1-perfect
  用**奇数版**: 奇数 k-perfect(奇数多完全数) —— 已知只有 σ(n)=2n 奇版(奇完全数)被研究,
  奇数 σ(n)=3n/4n 等多完全数可能**非常偏**(文献几乎未见)

真正的新方向:
  1. 奇数 σ(n)=k·n (k=3,4,5,6) —— 奇数多完全数, 偏僻
  2. σ(n)=k·n 对 n 的**结构**(如 n 的因子分解形状随 k)
  3. σ(n)=k·n + n 素性/合性分类

本脚本全力枚举奇数多完全数 + 记录每个解的结构。
"""
import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def sigma(n):
    s, m, d = 1, n, 2
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


def factor(n):
    """素因子分解 -> {p: e}"""
    f, m, d = {}, n, 2
    while d * d <= m:
        while m % d == 0:
            f[d] = f.get(d, 0) + 1
            m //= d
        d += 1
    if m > 1:
        f[m] = f.get(m, 0) + 1
    return f


def scan_multiperfect(odd_only, kmax=7, N=10**6, step=2 if None else 1):
    """枚举 σ(n)=k·n 的解。odd_only=True 只奇数 n。"""
    res = {}
    t0 = time.time()
    for k in range(2, kmax + 1):
        found = []
        lo = 3 if odd_only else 2
        st = 2 if odd_only else 1
        for n in range(lo, N, st):
            if sigma(n) == k * n:
                found.append(n)
        res[k] = found
        print(f"  k={k}: {len(found)} 个解 {found[:4]} [{time.time()-t0:.0f}s]")
    return res


def main():
    N = 2_000_000
    print("=" * 100)
    print(f"全力扫描: 多完全数 σ(n)=k·n, 奇偶分离, N={N:,}")
    print("=" * 100)

    print("\n== 奇数多完全数(偏僻分支) ==")
    odd = scan_multiperfect(odd_only=True, N=N)
    print("\n== 偶数多完全数(对照, 已知) ==")
    even = scan_multiperfect(odd_only=False, N=N)

    print("\n" + "=" * 100)
    print("发现与分析")
    print("=" * 100)
    for k in sorted(odd):
        o = odd[k]
        e = even[k]
        if o:
            print(f"  **奇数 σ(n)={k}n: 有解 {o}**  <- 偏僻/可能未见")
            # 结构
            for n in o[:3]:
                print(f"     {n} = {factor(n)}")
        else:
            print(f"  奇数 σ(n)={k}n: 无解(到{N})  | 偶数: {e[:3]}")
    print(f"\n  已知: k=2 偶 = 完全数(欧几里得-欧拉); 奇 = 奇完全数(千年未解)。")
    print(f"  k≥3 偶数 = 多完全数(已知概念); **k≥3 奇数 = 奇数多完全数(偏僻, 可能未见)**。")

    # 检查 OEIS
    try:
        sys.path.insert(0, str(HERE / "tools"))
        from oeis_index import OEISIndex
        idx = OEISIndex.load()
        for k in (3, 4, 5):
            if odd[k]:
                seq = odd[k][:8]
                hits = idx.lookup(seq)
                print(f"  奇数 σ(n)={k}n 前8 {seq} -> OEIS: "
                      f"{[h['a'] for h in hits] if hits else '**未见**'}")
    except Exception as e:
        print(f"  (OEIS 检查失败: {e})")

    (HERE / "out/demo/mega_branch.json").write_text(
        json.dumps({"odd": {str(k): v for k, v in odd.items()},
                    "even": {str(k): v for k, v in even.items()},
                    "N": N}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n已存 out/demo/mega_branch.json")


if __name__ == "__main__":
    main()
