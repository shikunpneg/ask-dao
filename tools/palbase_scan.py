# -*- coding: utf-8 -*-
"""tools/palbase_scan.py — 多进制扫描：回文数(b)+素数 覆盖，找"稳定小例外集"（R51）

b10 例外 0, b3 例外 68, b5 例外 4(疑似有限)。本文件一次扫 b=2..16,
对每个进制给出例外集 + 是否稳定(到 N 不增长) + OEIS 状态。
目标: 找"机器算到、疑似有限、参照系未见"的跨进制事实(接口新候选)。
"""
import bisect
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
from oeis_index import OEISIndex  # noqa: E402


def sieve_np(n):
    is_p = np.ones(n + 1, dtype=bool)
    is_p[:2] = False
    for i in range(2, int(n ** 0.5) + 1):
        if is_p[i]:
            is_p[i * i::i] = False
    return np.flatnonzero(is_p).astype(np.int64)


def pals(base, n):
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
            for dig in full:
                v = v * base + dig
            if v > n:
                break
            out.add(v)
        d += 1
    return sorted(out)


def scan(base, N, lo=4):
    primes = sieve_np(N)
    ps = [p for p in pals(base, N)]
    mark = np.zeros(N + 1, dtype=bool)
    for p in ps:
        hi = N - p
        if hi < 2:
            continue
        k = bisect.bisect_right(primes, hi)
        if k:
            mark[primes[:k] + p] = True
    exc = np.flatnonzero(~mark[lo:]) + lo
    return exc, len(ps), len(primes)


def main():
    idx = OEISIndex.load()
    N = 5_000_000
    print("=" * 100)
    print(f"多进制扫描: 回文数(b) + 素数 覆盖到 {N:,}")
    print("=" * 100)
    print(f"{'b':>3}{'回文':>7}{'素数':>8}{'例外':>6}{'最后例外':>9}{'贴边界':>6}  OEIS")
    print("-" * 100)
    rows = []
    for b in range(2, 17):
        exc, np_, npr = scan(b, N)
        last = int(exc[-1]) if len(exc) else None
        atb = bool(len(exc) and exc[-1] >= N - 100)
        hits = idx.lookup(exc[:12].tolist() if len(exc) else [0], max_hits=1)
        oeis = "HIT" if hits else "未见"
        rows.append({"b": b, "pals": np_, "primes": npr, "exc": len(exc),
                     "last": last, "at_boundary": atb, "oeis": oeis,
                     "exc_list": exc[:12].tolist() if len(exc) else []})
        print(f"{b:>3}{np_:>7}{npr:>8}{len(exc):>6}{str(last):>9}{str(atb):>6}  {oeis}"
              + (f"  {exc[:6].tolist()}" if len(exc) else ""))

    print("\n== 候选: 例外>0 且不贴边界(疑似有限) 且 OEIS 未见 ==")
    cands = [r for r in rows if r["exc"] > 0 and not r["at_boundary"] and r["oeis"] == "未见"]
    for r in cands:
        print(f"  b={r['b']}: 例外 {r['exc']} 个 {r['exc_list']}  (最后 {r['last']}, 疑似有限)")
    if not cands:
        print("  (无)")

    print("\n诚实: '疑似有限'是证据非证明; 'OEIS 未见'只是手头参照系未见。")
    (HERE / "out/demo/palbase_scan.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已存 out/demo/palbase_scan.json")


if __name__ == "__main__":
    main()
