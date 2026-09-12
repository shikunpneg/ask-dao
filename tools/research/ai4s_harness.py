# -*- coding: utf-8 -*-
"""tools/research/ai4s_harness.py — AI4S harness(最小可跑版)：消化发现器的问题清单

定位(用户): 发现器 -> AI4S harness -> 求解结果回灌。
这是 harness 的最小实现: 对 discovery_manifest 里每条"疑似有限/已验证"的问题,
**独立验证**(不同实现 + 更大 N), 产生"解/否/存疑"裁决, 回灌给发现器。

FunSearch 风格: 自然语言问题 -> 程序 -> 迭代验证。我们这里对每条:
  1. 独立复算例外集(不同代码路径)
  2. 推到更大 N(若可行)检验"有限性"
  3. 裁决: confirmed(例外汇合到同一集) / rejected(新例外出现) / open

输出: out/demo/harness_verdicts.json (回灌给 discovery 清单)
"""
import bisect
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent.parent


def sieve_np(n):
    is_p = np.ones(n + 1, dtype=bool)
    is_p[:2] = False
    for i in range(2, int(n ** 0.5) + 1):
        if is_p[i]:
            is_p[i * i::i] = False
    return np.flatnonzero(is_p).astype(np.int64)


def pals(base, n):
    """回文数(base) <= n (与 palbase_scan 相同的数位拼接, 保证一致性)。"""
    out = {0}
    d = 1
    while base ** (d - 1) <= n:
        half = (d + 1) // 2
        lo = base ** (half - 1) if half > 1 else 1
        for h in range(lo, base ** half):
            # 数位(大端)
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


def verify(base, N, lo=4):
    """独立验证: 回文(base)+素数 覆盖 [4,N], 返回例外集。"""
    primes = sieve_np(N)
    ps = pals(base, N)
    mark = np.zeros(N + 1, dtype=bool)
    for p in ps:
        hi = N - p
        if hi < 2:
            continue
        k = bisect.bisect_right(primes, hi)
        if k:
            mark[primes[:k] + p] = True
    return np.flatnonzero(~mark[lo:]) + lo, len(ps), len(primes)


def main():
    manifest = json.loads((HERE / "out/demo/discovery_manifest.json").read_text(encoding="utf-8"))
    p1 = [q for q in manifest["problems"] if q["id"].startswith("Q_b")]
    print("=" * 100)
    print("AI4S harness(最小版) —— 独立验证发现器的问题清单")
    print("=" * 100)
    print(f"  处理 P1 跨进制 {len(p1)} 条")

    verdicts = []
    for q in p1:
        b = int(q["id"].split("_b")[1])
        N0 = q["evidence"]["scan_to"] or 5_000_000
        t0 = time.time()
        # 独立复算到 N0
        exc0, np_, npr = verify(b, N0)
        # 若可能, 推更大(2*N0, 封顶 2e7)
        N1 = min(N0 * 2, 20_000_000)
        if N1 > N0:
            exc1, _, _ = verify(b, N1)
        else:
            exc1 = exc0
        # 裁决
        exp0 = set(int(x) for x in exc0.tolist())
        exp1 = set(int(x) for x in exc1.tolist())
        new = exp1 - exp0
        if len(exp0) == 0:
            verdict = "confirmed(零例外, 到 N1 仍零)"
        elif not new and len(exp0) <= 10:
            verdict = f"confirmed(例外汇合: {sorted(exp0)}, N0->N1 无新)"
        elif new:
            verdict = f"rejected(出现新例外 {sorted(new)[:4]})"
        else:
            verdict = "open(例外多/仍在冒)"
        v = {"id": q["id"], "b": b, "N0": N0, "N1": N1,
             "exceptions_N0": sorted(exp0)[:10], "exceptions_N1": sorted(exp1)[:10],
             "new_exceptions": sorted(new)[:4], "count_N0": len(exp0),
             "verdict": verdict, "secs": round(time.time() - t0, 1)}
        verdicts.append(v)
        print(f"  {q['id']}  [{verdict}]  N0={N0:,}->N1={N1:,}  "
              f"例外 {len(exp0)}->{len(exp1)}  {secs_str(v['secs'])}")

    print("\n" + "=" * 100)
    print("回灌: 裁决写回 discovery_manifest")
    print("=" * 100)
    by_id = {v["id"]: v for v in verdicts}
    for q in manifest["problems"]:
        if q["id"] in by_id:
            q["harness_verdict"] = by_id[q["id"]]["verdict"]
    out = HERE / "out/demo/discovery_manifest.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    out2 = HERE / "out/demo/harness_verdicts.json"
    out2.write_text(json.dumps(verdicts, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  已回灌 -> {out}\n  裁决存 -> {out2}")
    confirmed = [v for v in verdicts if v["verdict"].startswith("confirmed")]
    print(f"\n  裁决统计: confirmed {len(confirmed)} / rejected "
          f"{sum(1 for v in verdicts if v['verdict'].startswith('rejected'))} / "
          f"open {sum(1 for v in verdicts if v['verdict'].startswith('open'))}")


def secs_str(s):
    return f"{s:.0f}s"


if __name__ == "__main__":
    main()
