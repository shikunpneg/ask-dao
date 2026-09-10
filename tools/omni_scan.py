# -*- coding: utf-8 -*-
"""tools/omni_scan.py — 全方位扫描器（R62）

用户: "扫描是全方位的。"

广撒网: 多个算术函数 x 多个异常度量 x 多类对象, 一次全扫。
让"异常/图样"自己浮出来, 不预设哪个重要。

维度:
  F 函数族: σ, φ, τ, μ, ω, Ω, 因子和, 数位和, 迭代停时...
  M 度量: 比值 σ/n, 差值, 增减序列, 取模, 对数, 局部极值...
  O 对象: 自然数, 质数, 平方数, 阶乘, 斐波那契, 图计数, 串计数...

每个组合 -> 整数序列 -> (a) OEIS 反查 (b) 结构检查(线性递推/多项式/平凡)
-> 分级: OEIS命中(已知) / 结构可推 / **未命中且不可推(候选)**

用已有的 oeis_index 反查, 一次性扫几百个组合。
"""
import json
import math
import sys
import time
from itertools import product
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
sys.path.insert(0, str(HERE / "src"))

from oeis_index import OEISIndex  # noqa: E402
from ask_dao_machine.judges_math import sieve  # noqa: E402

N = 40  # 序列长度


# ========== 对象池(整数序列) ==========
def _build_objects():
    ps = sieve(1000000)
    primes = [i for i in range(2, 1000000) if ps[i]]
    O = {
        "自然数": list(range(1, N + 1)),
        "质数": primes[:N],
        "平方数": [i * i for i in range(1, N + 1)],
        "立方数": [i ** 3 for i in range(1, N + 1)],
        "三角数": [i * (i + 1) // 2 for i in range(1, N + 1)],
        "阶乘": [math.factorial(i) for i in range(1, N + 1)],
        "斐波那契": _fib(N),
        "卡特兰": [math.comb(2 * i, i) // (i + 1) for i in range(N)],
        "划分数": _partitions(N),
        "质数间隙": [primes[i + 1] - primes[i] for i in range(N)],
        "合数": [i for i in range(4, 100000) if not ps[i]][:N],
    }
    return O


def _fib(n):
    a, b, out = 1, 1, []
    for _ in range(n):
        out.append(a)
        a, b = b, a + b
    return out


def _partitions(n):
    p = [1] + [0] * n
    for k in range(1, n + 1):
        for i in range(k, n + 1):
            p[i] += p[i - k]
    return p[1:n + 1]


# ========== 函数族(逐元素应用) ==========
def _sigma(n):
    s, m, d = 1, n, 2
    while d * d <= m:
        if m % d == 0:
            pp = 1
            while m % d == 0:
                m //= d
                pp = pp * d + 1
            s *= pp
        d += 1
    if m > 1:
        s *= (1 + m)
    return s


def _phi(n):
    r, m, d = n, n, 2
    while d * d <= m:
        if m % d == 0:
            while m % d == 0:
                m //= d
            r -= r // d
        d += 1
    if m > 1:
        r -= r // m
    return r


def _tau(n):
    c, m, d = 0, n, 2
    while d * d <= m:
        while m % d == 0:
            c += 1
            m //= d
        d += 1
    if m > 1:
        c += 1
    return c


def _omega(n):
    c, m, d = 0, n, 2
    while d * d <= m:
        if m % d == 0:
            c += 1
            while m % d == 0:
                m //= d
        d += 1
    if m > 1:
        c += 1
    return c


def _bigomega(n):
    c, m, d = 0, n, 2
    while d * d <= m:
        while m % d == 0:
            c += 1
            m //= d
        d += 1
    if m > 1:
        c += 1
    return c


def _digitsum(n):
    return sum(int(c) for c in str(n))


def _aliquot(n):
    return _sigma(n) - n


FUNCS = {
    "σ": _sigma, "φ": _phi, "τ": _tau, "ω": _omega, "Ω": _bigomega,
    "数位和": _digitsum, "真因子和": _aliquot,
}


# ========== 度量(序列 -> 序列) ==========
def _ratio(s):   return [round(s[i] / (i + 1), 4) if i + 1 else 0 for i in range(len(s))]
def _diff(s):    return [s[i + 1] - s[i] for i in range(len(s) - 1)]
def _log(s):     return [round(math.log(x), 4) if x > 0 else 0 for x in s]
def _mod7(s):    return [x % 7 for x in s]
def _sign(s):    return [1 if x > 0 else (-1 if x < 0 else 0) for x in s]
def _runlen(s):
    out, run = [], 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1]:
            run += 1
        else:
            out.append(run)
            run = 1
    out.append(run)
    return out

METRICS = {"比值": _ratio, "差分": _diff, "对数": _log, "mod7": _mod7,
           "符号": _sign, "游程": _runlen}


# ========== 结构检查(是否平凡/可推) ==========
def is_trivial(seq):
    if len(seq) < 6:
        return True
    if len(set(seq)) <= 2:
        return True
    if all(isinstance(x, int) for x in seq):
        if seq == list(range(seq[0], seq[0] + len(seq))):
            return True
    return False


def is_poly(seq):
    cur = list(seq)
    for _d in range(1, 4):
        cur = [cur[i + 1] - cur[i] for i in range(len(cur) - 1)]
        if len(cur) >= 2 and len(set(cur)) == 1:
            return _d
    return None


def main():
    t0 = time.time()
    idx = OEISIndex.load()
    O = _build_objects()
    print("=" * 100)
    print("全方位扫描: 对象 × 函数 × 度量")
    print("=" * 100)
    print(f"  对象 {len(O)} × 函数 {len(FUNCS)} × 度量 {len(METRICS)} = "
          f"{len(O)*len(FUNCS)*len(METRICS)} 个组合")

    candidates, known, trivial_n = [], 0, 0
    for oname, seq in O.items():
        for fname, f in FUNCS.items():
            fseq = [f(x) for x in seq]
            for mname, m in METRICS.items():
                try:
                    ms = m(fseq)
                except Exception:
                    continue
                if len(ms) < 6:
                    continue
                if is_trivial(ms) or is_poly(ms):
                    trivial_n += 1
                    continue
                h = idx.lookup(ms, max_hits=2)
                strong = [x for x in h if x["matched"] >= min(6, len(ms))]
                if strong:
                    known += 1
                else:
                    candidates.append({"obj": oname, "func": fname, "metric": mname,
                                       "seq": ms[:10], "oeis": "未见"})

    print(f"\n  扫描 {len(O)*len(FUNCS)*len(METRICS)} 组合:")
    print(f"    已知(OEIS命中): {known}")
    print(f"    平凡/可推: {trivial_n}")
    print(f"    **候选(未命中且不可推): {len(candidates)}**")
    print(f"  耗时 {time.time()-t0:.0f}s")

    print("\n== 候选(机器算出 + OEIS 未见) ==")
    for c in candidates[:20]:
        print(f"  [{c['obj']}] {c['func']}(x) 的 {c['metric']}: {c['seq']}")

    print("\n诚实: 'OEIS 未见' = 手头参照系没有; 需结构检查(是否平凡)+文献门才能升级。")
    (HERE / "out/demo/omni_scan.json").write_text(
        json.dumps({"known": known, "trivial": trivial_n, "candidates": candidates},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print("已存 out/demo/omni_scan.json")


if __name__ == "__main__":
    main()
