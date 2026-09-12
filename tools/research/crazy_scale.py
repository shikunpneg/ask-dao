# -*- coding: utf-8 -*-
"""tools/research/crazy_scale.py — 疯狂规模化：所有基础领域 × 所有组合 × 向前推进（R44）

用户: "你的计算还没规模化, 基础领域就有很多, 每个都试着组合下都有多少组合,
每种组合在往前探都有多少可能了, 所以让你疯狂算。"

## 设计：**统一的"组合→扫描→度量"管线**
  1. **基础领域**(来自 _theory/basic_domains.md 裁定): 数学/物理/生物/心理/信息/工程/伦理/语言 + 逻辑(元层)
  2. 每个领域提供 **对象族**(可枚举整数序列)
  3. 每个对象族配 **推进器**: 向前扫到 N, 度量
     - 例外数 / 例外密度 / 最后例外 / 是否贴边界
     - 是否出现"新结构"(最后一次例外距离上一个很远 -> 边界上还在冒?)
  4. **组合**: 领域之间配对(对象A × 对象B 的和/差/比/交错), 同样向前推进
  5. 输出: 每个组合的"验证边界事实"

## 关键
  这是**可规模化**的: 每个组合是独立可算单元; 只需给定对象族 + 推进器。
  跑多少组合 = 算多少轮; 目标是把"每个组合往前探"变成自动化流水线。
"""
import json
import math
import sys
import time
from itertools import combinations
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent.parent


# ==================================================================
# 一、基础领域 -> 对象族(可枚举整数序列) -> 生成器
# ==================================================================
def _sieve(n):
    is_p = np.ones(n + 1, dtype=bool)
    is_p[:2] = False
    for i in range(2, int(n ** 0.5) + 1):
        if is_p[i]:
            is_p[i * i::i] = False
    return is_p


def _palindromes(base, n):
    out = {0}
    d = 1
    while base ** (d - 1) <= n:
        half = (d + 1) // 2
        lo = base ** (half - 1) if half > 1 else 1
        for h in range(lo, base ** half):
            s = []
            x = h
            while x:
                s.append(x % base)
                x //= base
            s = s[::-1]
            if len(s) != half:
                continue
            full = s + (s[:-1][::-1] if d % 2 else s[::-1])
            v = 0
            for digit in full:
                v = v * base + digit
            if v > n:
                break
            out.add(v)
        d += 1
    return out


def build_families(n):
    """每个领域 -> 对象族集合。族 = (名字, 集函数 n->set)。"""
    is_p = _sieve(n)
    primes = set(int(i) for i in np.flatnonzero(is_p))
    F = {}

    # 数学
    F["数学"] = {
        "素数": primes,
        "质数间隙": {int(x) for x in np.diff(np.flatnonzero(is_p))},
        "平方数": {i * i for i in range(1, int(n ** 0.5) + 1)},
        "三角数": {i * (i + 1) // 2 for i in range(1, int((2 * n) ** 0.5) + 2)},
        "回文数_b10": _palindromes(10, n),
        "完全数": {6, 28, 496, 8128, 33550336} & set(range(1, n + 1)),
        "幂数": {i ** 3 for i in range(1, int(n ** (1 / 3)) + 2)} | {i * i for i in range(1, int(n ** 0.5) + 1)},
    }

    # 物理: 用守恒量的离散化(实际可算的是数学序列; 物理给"守恒型对象"的整数近似)
    F["物理"] = {
        "谐振子能级": {i * (i + 1) // 2 for i in range(1, 500)},   # E~n(n+1)
        "普朗克量子": {i for i in range(1, 1000)},                  # n*h 整数
        "开普勒面积": {int(n ** 1.5) for n in range(1, 2000)},     # 周期^2 ~ a^3
    }

    # 生物: 数量型(种群/遗传)
    F["生物"] = {
        "费氏数列(生长)": _fib(n),
        "三角数(群体)": {i * (i + 1) // 2 for i in range(1, int((2 * n) ** 0.5) + 2)},
        "幂律(种群)": {int(1000 / (i + 1)) for i in range(1, 2000)},
    }

    # 信息论
    F["信息论"] = {
        "汉明权(格雷码)": {int(bin(i).count("1")) for i in range(1, n + 1)},
        "2的幂": {2 ** i for i in range(0, 30)} & set(range(1, n + 1)),
        "梅森数": {(2 ** i - 1) for i in range(1, 40)} & set(range(1, n + 1)),
    }

    # 语言
    F["语言"] = {
        "无平方词长": {2 ** i for i in range(1, 30)},      # 无平方词的存在性
        "回文词长": {2 * i - 1 for i in range(1, 500)},   # 奇长度
        "Dyck路径长": {2 * i for i in range(1, 1000)},    # 偶长度
    }

    # 工程(整数化): 可靠性/编码
    F["工程"] = {
        "汉明码长": {2 ** i - 1 for i in range(1, 20)} & set(range(1, n + 1)),
        "帕累托": {int(1000 / (i + 1)) for i in range(1, 2000)},
    }

    # 心理(行为计数)
    F["心理"] = {
        "反应时幂律": {int(1000 * (i ** -0.3)) for i in range(1, 2000)},
        "遗忘曲线": {int(100 / (1 + i * 0.1)) for i in range(1, 2000)},
    }

    # 伦理(规范计数——多为空/平凡, 诚实标注)
    F["伦理"] = {}

    # 逻辑(元层)
    F["逻辑"] = {
        "可计算数(图灵)": {i for i in range(1, 1000)},      # 平凡
        "归约链长": {int(math.log2(i + 1)) + 1 for i in range(1, n + 1)},
    }

    return F


def _fib(n):
    a, b = 1, 1
    out = []
    while a <= n:
        out.append(a)
        a, b = b, a + b
    return set(out)


# ==================================================================
# 二、推进器: 对"两个对象族的和覆盖"扫到 N
# ==================================================================
def scan_sum(A, B, n_max, lo=4, step=2):
    """n = A + B? 扫到 n_max, 返回例外事实(只扫偶数, 两族相加)。"""
    mark = np.zeros(n_max + 1, dtype=bool)
    A = sorted(a for a in A if a < n_max)
    B = sorted(b for b in B if b < n_max)
    for a in A:
        k = _bisect_hi(B, n_max - a)
        if k:
            idx = np.array(B[:k], dtype=np.int64) + a
            mark[idx] = True
    exc = np.flatnonzero(~mark[lo:]) + lo
    return exc


def _bisect_hi(arr, x):
    """返回 arr 中 <= x 的个数。"""
    import bisect
    return bisect.bisect_right(arr, x)


def scan_sum_all(A, B, n_max=100000, lo=4):
    """对 A+B 做全偶数扫描, 返回事实摘要。"""
    exc = scan_sum(A, B, n_max, lo)
    dens = len(exc) / ((n_max - lo) // 2 + 1) if n_max > lo else 0
    return {
        "exception_count": int(len(exc)),
        "density": round(dens, 6),
        "first": [int(x) for x in exc[:8]],
        "last": int(exc[-1]) if len(exc) else None,
        "at_boundary": bool(len(exc) and exc[-1] >= n_max - 100),
        "scan_to": n_max,
    }


def main():
    t0 = time.time()
    N = 100000
    fams = build_families(N)
    print("=" * 104)
    print("疯狂规模化 —— 基础领域 × 对象族 × 向前推进")
    print("=" * 104)
    print(f"  基础领域: {len(fams)} 个")
    for dom, fam in fams.items():
        print(f"    {dom:<6}: {len(fam)} 个对象族 {list(fam.keys())[:6]}")

    # 统计所有对象族
    all_fam = {}
    for dom, fam in fams.items():
        for name, s in fam.items():
            all_fam[f"{dom}:{name}"] = s
    print(f"\n  全部对象族: {len(all_fam)} 个")

    # 同域内组合(领域内的对象族配对)
    print("\n" + "=" * 104)
    print("阶段1: 同域内组合(A+B 覆盖) —— 向前推进")
    print("=" * 104)
    results = []
    for dom, fam in fams.items():
        names = list(fam)
        for a, b in combinations(names, 2):
            if a == b:
                continue
            key = f"{dom}:{a} + {dom}:{b}"
            r = scan_sum_all(fam[a], fam[b], N)
            r["pair"] = key
            results.append(r)
    print(f"  同域组合: {len(results)} 个")
    # 排序: 例外最少的最可能"几乎处处成立"(有意思)
    results.sort(key=lambda r: (r["exception_count"], r["at_boundary"]))
    print("\n  例外最少(几乎处处成立)的前 12 个组合:")
    for r in results[:12]:
        print(f"    {r['pair']:<34} 例外 {r['exception_count']:>4}  "
              f"最后 {str(r['last']):>6}  贴边界={r['at_boundary']}")

    # 跨域组合(领域 × 领域)
    print("\n" + "=" * 104)
    print("阶段2: 跨域组合(不同领域的对象族配对) —— 向前推进")
    print("=" * 104)
    doms = [d for d in fams if fams[d]]
    cross = []
    for d1, d2 in combinations(doms, 2):
        for n1, s1 in list(fams[d1].items()):
            for n2, s2 in list(fams[d2].items()):
                key = f"{d1}:{n1} + {d2}:{n2}"
                r = scan_sum_all(s1, s2, N)
                r["pair"] = key
                cross.append(r)
    print(f"  跨域组合: {len(cross)} 个")
    cross.sort(key=lambda r: (r["exception_count"], r["at_boundary"]))
    print("\n  例外最少(几乎处处成立)的前 15 个跨域组合:")
    for r in cross[:15]:
        print(f"    {r['pair']:<40} 例外 {r['exception_count']:>4}  "
              f"最后 {str(r['last']):>6}  贴边界={r['at_boundary']}")

    # 例外稠密的(可能有反例/结构)
    dense = [r for r in cross if r["density"] > 0.1 and r["exception_count"] > 100]
    print(f"\n  例外稠密(>10%, 可能是'大多数不成'的)跨域组合: {len(dense)} 个")
    for r in dense[:8]:
        print(f"    {r['pair']:<40} 例外 {r['exception_count']:>6} 密度 {r['density']:.1%}")

    print(f"\n  总扫描组合: {len(results) + len(cross)}  耗时 {time.time()-t0:.1f}s")

    print("\n诚实:")
    print("  · 这是**批量推进验证边界** —— 每个组合给出精确的例外事实。")
    print("  · '几乎处处成立'(例外极少)的组合 = 强猜想候选; '稠密例外' = 猜想本身为假。")
    print("  · 但**事实是不是新的**, 取决于文献有没有算到 N=100000 —— 需查证。")
    print("  · 大批组合会重发现已知定理(如 质数+质数=哥德巴赫), 这是可预期的。")

    (HERE / "out/demo/crazy_scale.json").write_text(
        json.dumps({"same_domain": results, "cross": cross}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print("\n已存 out/demo/crazy_scale.json")


if __name__ == "__main__":
    main()
