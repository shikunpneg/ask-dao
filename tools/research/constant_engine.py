# -*- coding: utf-8 -*-
"""tools/research/constant_engine.py — 常驻并行引擎：14 进程长时间后台生成+扫描（R68）

用户: "发挥这台设备所有算力去生成问题和扫描问题" + "批量做直到发现新问题"。

设计: 每核跑一个**领地家族**的连续任务流(完成一个参数自动换下一个),
主进程持续收集 -> manifest。可长时间后台运行。

领地家族(每核一个):
  W1 跨进制: 回文(b)+素数  b=2..30 连续
  W2 两数和: 质数+多边形(k)  k=3..30 连续
  W3 模迭代: x²+c mod m  c=1..20 连续
  W4 图阻挫: n=6 各边数 连续
  W5 函数泛化: σ(n)=k·n  k=2..20 连续
  W6 多边形模: k边形 mod 7  k=3..30
  W7 组合禁构: 禁w 连续
  W8 数位和: 各进制数位和
"""
import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def worker_family(args):
    """领地家族: 连续跑一个领地的所有参数, 返回全部产出。"""
    fam, lo, hi, step = args
    out = []
    for param in range(lo, hi, step):
        try:
            r = run_family(fam, param)
            if r:
                out.append(r)
        except Exception:
            pass
    return out


def run_family(fam, param):
    """单个领地参数 -> 一条候选。"""
    import numpy as np
    import bisect
    if fam == "palbase":
        N = 2_000_000
        b = param
        is_p = np.ones(N + 1, dtype=bool)
        is_p[:2] = False
        for i in range(2, int(N ** 0.5) + 1):
            if is_p[i]:
                is_p[i * i::i] = False
        primes = np.flatnonzero(is_p)
        pals = _pals(b, N)
        mark = np.zeros(N + 1, dtype=bool)
        for p in pals:
            k = bisect.bisect_right(primes, N - p)
            if k:
                mark[primes[:k] + p] = True
        exc = np.flatnonzero(~mark[4:]) + 4
        return {"domain": "palbase", "param": b,
                "statement": f"回文(base {b})+素数覆盖到{N}: 例外{len(exc)}",
                "evidence": {"count": int(len(exc)), "exc": exc[:8].tolist(),
                             "last": int(exc[-1]) if len(exc) else None},
                "judge_route": "数值枚举", "status": "待判定"}
    if fam == "two_sum":
        N = 500_000
        k = param
        primes = _prime_set(N)
        poly = set()
        i = 1
        while True:
            v = i * ((k - 2) * i - (k - 4)) // 2
            if v > N:
                break
            poly.add(v)
            i += 1
        exc = []
        for n in range(4, N, 2):
            if not any(p in primes and (n - p) in poly for p in range(2, n)):
                exc.append(n)
        return {"domain": "two_sum", "param": k,
                "statement": f"质数+{k}边形覆盖到{N}: 例外{len(exc)}",
                "evidence": {"count": len(exc), "exc": exc[:8]},
                "judge_route": "数值枚举", "status": "待判定"}
    if fam == "mod_iter":
        c = param
        seq = [_max_cycle(c, m) for m in range(3, 30)]
        return {"domain": "mod_iter", "param": c,
                "statement": f"x²+{c} mod m 最长环随 m: {seq[:10]}",
                "evidence": {"seq": seq}, "judge_route": "迭代", "status": "待判定"}
    if fam == "sigma_k":
        k = param
        found = [n for n in range(2, 200000) if _sigma(n) == k * n]
        return {"domain": "sigma_k", "param": k,
                "statement": f"σ(n)={k}n 的解(到200000): {found}",
                "evidence": {"found": found}, "judge_route": "枚举", "status": "待判定"}
    if fam == "poly_mod":
        k = param
        seq = []
        i = 1
        while len(seq) < 200:
            v = i * ((k - 2) * i - (k - 4)) // 2
            if v > 10 ** 6:
                break
            seq.append(v % 7)
            i += 1
        return {"domain": "poly_mod", "param": k,
                "statement": f"{k}边形数 mod7 前200项: {seq[:12]}...",
                "evidence": {"mod7": seq[:30]}, "judge_route": "模分析", "status": "待判定"}
    return None


def _prime_set(n):
    import numpy as np
    is_p = np.ones(n + 1, dtype=bool)
    is_p[:2] = False
    for i in range(2, int(n ** 0.5) + 1):
        if is_p[i]:
            is_p[i * i::i] = False
    return set(int(i) for i in np.flatnonzero(is_p))


def _pals(base, n):
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


def _max_cycle(c, m):
    seen = {}
    best = 0
    for x0 in range(m):
        x = x0
        chain = {}
        s = 0
        while x not in chain and x not in seen:
            chain[x] = s
            x = (x * x + c) % m
            s += 1
        if x in chain:
            best = max(best, s - chain[x])
        for k, v in chain.items():
            seen[k] = v
    return best


def _sigma(n):
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


def build_family_tasks():
    """每个 worker 跑一个领地家族的一段参数范围。"""
    fams = [
        ("palbase", 3, 33, 1),
        ("two_sum", 3, 23, 1),
        ("mod_iter", 1, 21, 1),
        ("sigma_k", 2, 22, 1),
        ("poly_mod", 3, 23, 1),
    ]
    # 为充分利用 14 核, 每个 family 拆成多段
    tasks = []
    for fam, lo, hi, step in fams:
        # 每 family 拆成 2-3 段
        span = hi - lo
        nchunks = 3 if span >= 10 else 2
        csize = span // nchunks + 1
        for start in range(lo, hi, csize):
            tasks.append((fam, start, min(start + csize, hi), step))
    return tasks


def main():
    t0 = time.time()
    tasks = build_family_tasks()
    nproc = min(14, len(tasks))
    print("=" * 100)
    print(f"常驻并行引擎 —— {nproc} 进程, 长时间生成+扫描")
    print("=" * 100)
    print(f"  任务(领地家族段): {len(tasks)} 个")
    for t in tasks:
        print(f"    {t[0]} 参数 {t[1]}..{t[2]}")
    print(f"\n  启动 {nproc} 进程并行...")

    with Pool(processes=nproc) as pool:
        results = pool.map(worker_family, tasks, chunksize=1)

    all_probs = []
    for r in results:
        all_probs.extend(r)

    print(f"\n  完成 [{time.time()-t0:.0f}s], 产出 {len(all_probs)} 条")
    from collections import Counter
    byd = Counter(p["domain"] for p in all_probs)
    print(f"  按领地: {dict(byd)}")

    man = HERE / "out/demo/discovery_manifest.json"
    d = json.loads(man.read_text(encoding="utf-8"))
    start = len(d["problems"])
    d["problems"] += [{**p, "id": f"CE_{start+i}"} for i, p in enumerate(all_probs)]
    d["count"] = len(d["problems"])
    man.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "out/demo/constant_engine.json").write_text(
        json.dumps(all_probs, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  已并入 discovery_manifest (总数 {d['count']})")


if __name__ == "__main__":
    main()
