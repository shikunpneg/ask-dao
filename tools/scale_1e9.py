# -*- coding: utf-8 -*-
"""tools/scale_1e9.py — 把"回文数+素数"覆盖推进到 10⁹（K2-10）

R42 已推到 10⁸(零例外)。本文件推到 10⁹, 看边界是否浮现新例外。
内存优化: 不用 10⁹ 布尔数组。用**分段扫描**:
  对每个回文 p, 检查区间 [lo, hi] 内哪些 n = p+素数, 用一个滑动 bool 数组(区间大小 B)。
  例外 = 该区间内未被任何 p 覆盖的数。

实际可行性: 回文数到 10⁹ ≈ 2×10⁵ 个; 对每个 p, 需要知道 p+素数 覆盖了 [4,10⁹] 的哪些偶区间。
"""
import bisect
import json
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent.parent


def sieve_range(n):
    """返回 (布尔, 素数数组) 到 n。"""
    is_p = np.ones(n + 1, dtype=bool)
    is_p[:2] = False
    for i in range(2, int(n ** 0.5) + 1):
        if is_p[i]:
            is_p[i * i::i] = False
    return is_p, np.flatnonzero(is_p).astype(np.int64)


def palindromes_upto(base, n):
    """base 进制下 <= n 的回文数(含 0)。"""
    out = {0}
    d = 1
    while base ** (d - 1) <= n:
        half = (d + 1) // 2
        lo = base ** (half - 1) if half > 1 else 1
        hi = base ** half
        for h in range(lo, hi):
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
    return sorted(out)


def scan_to(N, pal_base=10, seg=5_000_000):
    """分段扫 [4,N] 的偶数, 检查是否都被 回文(pal_base)+素数 覆盖。"""
    t0 = time.time()
    is_p, primes = sieve_range(N)
    primes_ar = primes
    pals = [p for p in palindromes_upto(pal_base, N) if p <= N]
    print(f"  素数到 {N:,}: {len(primes_ar):,} 个 | 回文: {len(pals):,} 个", flush=True)

    exceptions = []
    lo = 4
    while lo <= N:
        hi = min(lo + seg, N)
        mark = np.zeros(hi - lo + 1, dtype=bool)
        for p in pals:
            need = lo - p
            k = bisect.bisect_right(primes_ar, hi - p)
            start = bisect.bisect_left(primes_ar, need)
            if k > start:
                idx = primes_ar[start:k] + p - lo
                idx = idx[(idx >= 0) & (idx <= hi - lo)]
                mark[idx] = True
        exc_seg = np.flatnonzero(~mark[::2]) * 2 + lo   # 只偶数
        exceptions.extend(int(x) for x in exc_seg)
        if lo % (10 * seg) == 0:
            print(f"    ... 到 {lo:,}, 累计例外 {len(exceptions)}", flush=True)
        lo = hi + 1
    return exceptions, len(primes_ar), len(pals), time.time() - t0


def main():
    print("=" * 100)
    print("K2-10: 回文数(b10)+素数 覆盖推进到 10⁹")
    print("=" * 100)
    for N in (10 ** 8, 5 * 10 ** 8, 10 ** 9):
        exc, npr, npal, secs = scan_to(N)
        print(f"\n  N={N:,}: 例外 {len(exc)} 个  素数 {npr:,}  回文 {npal:,}  [{secs:.0f}s]")
        if exc:
            print(f"    例外: {exc[:20]}")
        print(f"    -> {'零例外(10⁸→10⁹ 维持)' if not exc else '**出现例外!**'}", flush=True)
        (HERE / f"out/demo/scale_1e9_{N}.json").write_text(
            json.dumps({"N": N, "exceptions": exc[:100] if exc else [],
                        "count": len(exc)}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n诚实: 零例外 = 证据推进(K2); 若 10⁹ 出现例外 = '机器算到才见'的接口新边界。")


if __name__ == "__main__":
    main()
