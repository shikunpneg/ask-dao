# -*- coding: utf-8 -*-
"""tools/extended_probe.py — 把两个'未见'候选的验证范围扩到 N=300000, 记录新证据。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from ask_dao_machine.judge_math import sieve

N = 300000
ps = sieve(N)
primes = [i for i in range(2, N) if ps[i]]

# squarefree
sqf_ok = bytearray(b"\x01") * (N + 1)
sqf_ok[0:2] = b"\x00\x00"
i = 2
while i * i <= N:
    if ps[i]:
        for j in range(i * i, N + 1, i * i):
            sqf_ok[j] = 0
    i += 1

# semiprimes
semis = set()
for a, p in enumerate(primes):
    if p * p > N:
        break
    for q in primes[a:]:
        if p * q >= N:
            break
        semis.add(p * q)

# triangular
tri = [t for t in (i * (i + 1) // 2 for i in range(1, int((2 * N) ** 0.5) + 2)) if t <= N]


def probe(sqf_or_semi, name, lo=40002, hi=N):
    fails = []
    checked = 0
    for n in range(lo, hi + 1, 2):
        ok = False
        for t in tri:
            if t >= n:
                break
            r = n - t
            if (sqf_ok[r] if sqf_or_semi == "sqf" else r in semis):
                ok = True
                break
        checked += 1
        if not ok:
            fails.append(n)
            if len(fails) >= 5:
                break
    print(f"[{name}] 偶数 {lo}..{hi} 检查 {checked} 个, 反例前5: {fails}")
    return fails


f1 = probe("sqf", "无平方因子数+三角数", lo=40002)
f2 = probe("semi", "半素数+三角数", lo=40002)
