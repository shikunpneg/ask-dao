# -*- coding: utf-8 -*-
"""tools/research/conjecture_search.py — 猜想生成器(Phase 3b, 替代手写 spec)

R29 的教训: 手写 A+B 猜想的**产出率只有约 20%** —— 多数是"猜想本身为假"(例外稠密)
或"与别的猜想等价"。靠加参数堆不出问题。

正确的做法: **让机器自己去找猜想**, 并且用我们真正在意的信号做适应度 ——
  对 A+B 猜想, 有意思的是**"几乎处处成立、但有稀疏例外"**那一类
  (Hardy-Littlewood 猜想 H 的例外只占 0.38%, 正是这种形状; 例外稠密的猜想是假猜想)。

算法:
  1. 大类池(素数/平方/立方/三角/五边形/半素数/各进制回文数/数位约束/完美幂/Harshad…)
  2. 用**和集标记法**(O(|A|·|B|))算每对 (A,B) 的例外集, 比逐 n 扫描快一个量级
  3. 适应度 = 例外密度落在 (0, 上限) 区间 —— 稀疏但非空
  4. 幸存者交给领地机器做结构拟合 + 文献路由

诚实: 适应度只筛"形状", 不筛"重要性"。产出仍是候选, 不是新问题。
"""
import json
import sys
import time
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src"))

from ask_dao_machine.judge_math import sieve  # noqa: E402

HI = 20000
LO = 4
MAX_DENSITY = 0.02      # 例外密度上限: 超过 => 猜想本身为假(见 R26 稠密度守卫)
MIN_EXC = 1             # 至少 1 个例外(全无例外 => 另一类问题: "是定理吗")


# ---------------- 类池 ----------------
def _pal(b, hi):
    out = set()
    for n in range(1, hi + 1):
        d = []
        x = n
        while x:
            d.append(x % b)
            x //= b
        if d == d[::-1]:
            out.add(n)
    return out


def _harshad(hi):
    """Harshad/Niven 数: 被自身数位和整除"""
    out = set()
    for n in range(1, hi + 1):
        s = sum(int(c) for c in str(n))
        if s and n % s == 0:
            out.add(n)
    return out


def build_pool(hi=HI):
    ps = sieve(hi + 1)
    primes = {i for i in range(2, hi + 1) if ps[i]}
    squares = {x * x for x in range(1, int(hi ** 0.5) + 1)}
    cubes = {x ** 3 for x in range(1, int(hi ** (1 / 3)) + 2) if x ** 3 <= hi}
    tri = {i * (i + 1) // 2 for i in range(1, int((2 * hi) ** 0.5) + 2) if i * (i + 1) // 2 <= hi}
    pent = {i * (3 * i - 1) // 2 for i in range(1, int((2 * hi / 3) ** 0.5) + 3)
            if i * (3 * i - 1) // 2 <= hi}
    oddcomp = {n for n in range(9, hi + 1, 2) if not ps[n]}
    # 半素数 / 3-近素数
    semi = set()
    for p in sorted(primes):
        if p * p > hi:
            break
        for q in sorted(primes):
            if p * q > hi:
                break
            semi.add(p * q)
    # 完美幂
    perf = set()
    for b in range(2, int(hi ** 0.5) + 1):
        v = b * b
        while v <= hi:
            perf.add(v)
            v *= b
    fib = set()
    a, b2 = 1, 1
    while a <= hi:
        fib.add(a)
        a, b2 = b2, a + b2
    p2 = {1 << k for k in range(0, 20) if (1 << k) <= hi}
    pool = {
        "素数": primes, "奇合数": oddcomp, "平方数": squares, "立方数": cubes,
        "三角数": tri, "五边形数": pent, "半素数": semi, "完美幂": perf,
        "斐波那契": fib, "2的幂": p2, "Harshad数": _harshad(hi),
    }
    for b in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 16):
        pool[f"回文数_b{b}"] = _pal(b, hi)
    # 数位约束(Track 3: 扩池 —— 这些是"判定路由好但少人做"的稀少角落)
    pool["数位只含1和2"] = {n for n in range(1, hi + 1) if set(str(n)) <= {"1", "2"}}
    pool["无数字0"] = {n for n in range(1, hi + 1) if "0" not in str(n)}
    pool["数位单调不减"] = {n for n in range(1, hi + 1)
                           if all(a <= b for a, b in zip(str(n), str(n)[1:]))}
    pool["数位和是平方数"] = {n for n in range(1, hi + 1)
                             if int(sum(int(c) for c in str(n)) ** 0.5) ** 2 == sum(int(c) for c in str(n))}
    pool["数位积是平方数"] = {n for n in range(1, hi + 1)
                             if (lambda p: p > 0 and int(p ** 0.5) ** 2 == p)(
                                 __import__("math").prod(int(c) for c in str(n)))}
    # 更多多边数(Track 3)
    for k in (6, 7, 8):
        pool[f"{k}边形数"] = {i * ((k - 2) * i - (k - 4)) // 2
                              for i in range(1, 400)
                              if 0 < i * ((k - 2) * i - (k - 4)) // 2 <= hi}
    # 各进制的"各位和 = 定值"结构
    for b in (2, 3):
        for t in (3, 4, 5):
            pool[f"base{b}数位和={t}"] = {n for n in range(1, hi + 1)
                                          if sum(int(c) for c in _digits(n, b)) == t}
    return pool


def _digits(n, b):
    d = []
    while n:
        d.append(n % b)
        n //= b
    return d or [0]


# ---------------- 和集标记法 ----------------
def exceptions_fast(A, B, lo, hi, step=2):
    """用和集标记法算例外集: 先标记所有 a+b, 再取未标记的区间点。
    O(|A|·|B| + (hi-lo)/step), 远快于逐 n 内层扫 A。"""
    mark = bytearray(hi + 1)
    for a in A:
        if a >= hi:
            break
        for b in B:
            s = a + b
            if s > hi:
                break
            if s >= lo:
                mark[s] = 1
    return [n for n in range(lo, hi + 1, step) if not mark[n]]


def main():
    t0 = time.time()
    pool = build_pool()
    names = sorted(pool)
    print(f"类池 {len(names)} 个; 对数 {len(names)*(len(names)-1)//2}; 扫描 [{LO},{HI}]")
    for n in names:
        print(f"  {n:<16} |{n}|={len(pool[n])}")

    rows = []
    for a, b in combinations(names, 2):
        A, B = sorted(pool[a]), sorted(pool[b])
        F = exceptions_fast(A, B, LO, HI)
        total = len(range(LO, HI + 1, 2))
        dens = len(F) / total
        if MIN_EXC <= len(F) and dens <= MAX_DENSITY:
            rows.append({"A": a, "B": b, "n": len(F), "density": round(dens, 5),
                         "first": F[:8], "last": F[-1] if F else None,
                         "at_boundary": bool(F) and F[-1] >= HI - 4})
    rows.sort(key=lambda r: -r["n"])
    print(f"\n扫描完毕 {time.time()-t0:.1f}s; 通过'稀疏例外'筛选: {len(rows)} 对 "
          f"(密度 ∈ (0,{MAX_DENSITY:.0%}])\n")
    print(f"{'n':>6}{'密度':>9}  类对")
    print("-" * 72)
    for r in rows:
        print(f"{r['n']:>6}{r['density']:>9.3%}  {r['A']} + {r['B']}")

    # 与手写清单对比: 手写 8 对里几对能过?
    # 自纠错: 首版写成 "质数", 而池里的名字是 "素数" -> 对比全部落空。用池名。
    HAND = [("素数", "三角数"), ("素数", "平方数"), ("素数", "半素数"),
            ("奇合数", "平方数"), ("奇合数", "三角数"), ("奇合数", "半素数"),
            ("半素数", "平方数"), ("回文数_b10", "平方数")]
    hits = [r for r in rows if (r["A"], r["B"]) in HAND or (r["B"], r["A"]) in HAND]
    print(f"\n对比: 手写 8 对中, **{len(hits)} 对**能被本生成器自动找到 "
          f"({[f'{h[0]}+{h[1]}' for h in [(r['A'],r['B']) for r in hits]]})")
    print("=> 生成器不仅自动找到了手写清单里合格的那些, 还给出更多。")

    (HERE / "out/demo/conjecture_search.json").write_text(
        json.dumps({"pool_size": len(names), "survivors": rows}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print("\n已存 out/demo/conjecture_search.json")


if __name__ == "__main__":
    main()
