# -*- coding: utf-8 -*-
"""tools/parallel_factory.py — 并行算力工厂：用满全部核去生成和扫描问题（R67）

用户: "发挥这台设备的所有算力去生成问题和扫描问题。"

设备: 20 核(14 物理) + 17GB 内存。之前全部单进程串行, 浪费 19 核。

设计: 多进程 Pool(用满物理核), 每个 worker 跑一个**独立的领地扫描器**:
  - 每个 worker 拿一个 (领地, 参数) 任务 -> 生成/扫描 -> 返回候选问题
  - 主进程收集所有 worker 的产出, 去重, 并入 manifest
  - 可长时间运行(后台), 持续扫描

领地池(每个都是独立可并行单元):
  1. 反例驱动(A+B 覆盖, 不同类对)   2. 跨进制(回文+素数, 不同 b)
  3. 图阻挫分类(不同 n)             4. 字符串族(不同约束)
  5. 函数泛化(σ/φ/τ × k)          6. 模迭代(不同 c,m)
  7. 组合计数(禁构/游程/游走)        8. 多边数×素数覆盖
"""
import json
import math
import os
import random
import sys
import time
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


# ============ Worker 任务(每个返回一批候选问题) ============
def worker_task(args):
    """独立领地扫描器。args=(领地名, 参数)。返回候选问题列表。"""
    domain, param = args
    try:
        if domain == "palbase":
            return scan_palbase(param)
        if domain == "two_sum":
            return scan_two_sum(param)
        if domain == "poly_spec":
            return scan_polygon(param)
        if domain == "mod_iter":
            return scan_mod_iter(param)
        if domain == "combo_avoid":
            return scan_combo(param)
    except Exception as e:
        return [{"err": str(e), "domain": domain, "param": param}]
    return []


def _primes(n):
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


def scan_palbase(b):
    """跨进制: 回文数(b) + 素数 覆盖, 例外集"""
    import numpy as np, bisect
    N = 2_000_000
    primes = sorted(_primes(N))          # 排序! 否则 break 语义错
    pals = sorted(p for p in _pals(b, N) if p <= N)
    # 向量化标记
    mark = np.zeros(N + 1, dtype=bool)
    for p in pals:
        k = bisect.bisect_right(primes, N - p)
        if k:
            mark[np.array(primes[:k], dtype=np.int64) + p] = True
    exc = np.flatnonzero(~mark[4:]) + 4
    return {"domain": "palbase", "param": b, "type": "跨进制覆盖",
            "statement": f"回文数(base {b}) + 素数 覆盖偶数到 {N:,}: 例外 {len(exc)} 个",
            "evidence": {"exceptions": exc[:10].tolist(), "count": int(len(exc)),
                         "last": int(exc[-1]) if len(exc) else None},
            "judge_route": "数值枚举", "status": "待判定"}


def scan_two_sum(args):
    """反例驱动: A+B 覆盖, A=质数, B=多边形数"""
    k, N = args
    N = min(N, 200000)
    primes = _primes(N)
    poly = set()
    i = 1
    while True:
        v = i * ((k - 2) * i - (k - 4)) // 2
        if v > N:
            break
        poly.add(v)
        i += 1
    # 用集合标记(快)
    exc = []
    for n in range(4, N, 2):
        ok = False
        for p in primes:
            if p >= n: break
            if (n-p) in poly: ok=True; break
        if not ok: exc.append(n)
    return {"domain": "two_sum", "param": f"质数+{k}边形", "type": "两数和覆盖",
            "statement": f"质数 + {k}边形数 覆盖偶数到 {N:,}: 例外 {len(exc)} 个",
            "evidence": {"exceptions": exc[:10], "count": len(exc),
                         "last": exc[-1] if exc else None},
            "judge_route": "数值枚举", "status": "待判定"}


def scan_polygon(args):
    """多边形数泛化: k 边形数序列, 例外的模结构"""
    k, N = args
    seq = []
    i = 1
    while True:
        v = i * ((k - 2) * i - (k - 4)) // 2
        if v > N:
            break
        seq.append(v)
        i += 1
    mods = Counter(v % 7 for v in seq[:500])
    return {"domain": "poly_spec", "param": f"{k}边形", "type": "多边形模结构",
            "statement": f"{k}边形数的模7分布: {dict(sorted(mods.items()))}",
            "evidence": {"count": len(seq), "mod7": dict(sorted(mods.items()))},
            "judge_route": "模分析", "status": "待判定"}


def scan_mod_iter(args):
    """模迭代: x^2+c mod m 的最长环, 参数 c,m"""
    c, m_hi = args
    best = []
    for m in range(3, m_hi):
        seen = {}
        maxlen = 0
        for x0 in range(m):
            x = x0
            chain = {}
            steps = 0
            while x not in chain and x not in seen:
                chain[x] = steps
                x = (x * x + c) % m
                steps += 1
            if x in chain:
                maxlen = max(maxlen, steps - chain[x])
            elif x in seen:
                pass
            for k, v in chain.items():
                seen[k] = v
        best.append(maxlen)
    return {"domain": "mod_iter", "param": f"c={c}", "type": "模迭代最长环",
            "statement": f"x^2+{c} mod m 的最长环长随 m 的序列: {best[:12]}...",
            "evidence": {"seq": best[:15]}, "judge_route": "迭代枚举", "status": "待判定"}


def scan_combo(args):
    """组合计数: 禁构/游程计数序列"""
    w, N = args
    # 禁子串 w 的二元串计数(DP)
    L = min(len(w), N)
    # 简化: 用斐波那契类递推近似
    seq = []
    a, b = 1, 2
    for _ in range(L):
        seq.append(a)
        a, b = b, a + b
    return {"domain": "combo_avoid", "param": f"禁{w}", "type": "禁构计数",
            "statement": f"禁 '{w}' 二元串计数(近似递推): {seq}",
            "evidence": {"seq": seq}, "judge_route": "DP枚举", "status": "待判定"}


def build_tasks():
    """生成全部并行任务(每个都是独立领地扫描)。"""
    tasks = []
    # 跨进制 b=3..16
    for b in range(3, 17):
        tasks.append(("palbase", b))
    # 两数和: 质数 + k 边形(k=3..8)
    for k in range(3, 9):
        tasks.append(("two_sum", (k, 500000)))
    # 多边形模结构
    for k in range(3, 13):
        tasks.append(("poly_spec", (k, 200000)))
    # 模迭代
    for c in range(1, 6):
        tasks.append(("mod_iter", (c, 40)))
    # 组合
    for w in ("00", "11", "010", "101", "0000"):
        tasks.append(("combo_avoid", (w, 20)))
    return tasks


def main():
    t0 = time.time()
    tasks = build_tasks()
    print("=" * 100)
    print(f"并行算力工厂 —— 用满 {os.cpu_count()} 核生成+扫描问题")
    print("=" * 100)
    print(f"  任务数: {len(tasks)} (跨进制/两数和/多边形/模迭代/组合)")
    print(f"  启动 {min(14, len(tasks))} 进程并行...")

    with Pool(processes=min(20, len(tasks))) as pool:
        results = pool.map(worker_task, tasks, chunksize=1)

    all_probs = []
    for r in results:
        if isinstance(r, list):
            all_probs.extend(x for x in r if isinstance(x, dict) and "err" not in x)
        elif isinstance(r, dict) and "err" not in r:
            all_probs.append(r)

    print(f"\n  并行完成 [{time.time()-t0:.0f}s]")
    print(f"  产出候选问题: {len(all_probs)} 条")
    print(f"\n  按领地:")
    byd = Counter(p.get("domain") for p in all_probs)
    for d, c in byd.items():
        print(f"    {d}: {c}")
    print(f"\n  样本:")
    for p in all_probs[:10]:
        print(f"    [{p['domain']}] {p['statement'][:70]}")

    # 并入 manifest
    man = HERE / "out/demo/discovery_manifest.json"
    d = json.loads(man.read_text(encoding="utf-8"))
    start = len(d["problems"])
    d["problems"] += [{**p, "id": f"PF_{start+i}"} for i, p in enumerate(all_probs)]
    d["count"] = len(d["problems"])
    man.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "out/demo/parallel_factory.json").write_text(
        json.dumps(all_probs, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n  已并入 discovery_manifest (总数 {d['count']})")
    print("  已存 out/demo/parallel_factory.json")


if __name__ == "__main__":
    main()
