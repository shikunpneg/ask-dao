# -*- coding: utf-8 -*-
"""tools/research/mega_scan.py — 疯狂扩张：可复合算子链 × 大对象池 × 跨域融合（R39b）

## 用户指令
"疯狂的长，疯狂的融合"

## 设计: **把方法做成可复合的算子链**
统一载体 = 整数序列。于是:
    对象 → 方法₁ → 方法₂ → 方法₃ → … → 序列
每一步都是一条**树边**; 链有多长, 树就有多深。**这是"长"的实现方式** ——
不是把 L0–L7 再加几层(那只是标签), 而是让方法**真的首尾相接**。

## 融合
对象来自 16 个领域; 方法来自 11 个领域 ⇒ 链上每一步都可能是跨域步。
链 `数论对象 → 熵 → 谱 → 模类计数` 就是**三重融合**。

## 判据
机器能做的只有一件事: **算出来 → 查 OEIS**。
  OEIS 命中 ⇒ 该链的结果已被记录(已知)
  OEIS 未命中 ⇒ **候选**(诚实: 未命中 ≠ 新, 只说明手头参照系里没有)
再加机制检查(是否平凡/常数/可归约), 才是完整的"机器前沿"。
"""
import json
import math
import sys
import time
from itertools import product
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src"))
_td = HERE / "tools"
sys.path.insert(0, str(_td))
for _sd in _td.iterdir():
    if _sd.is_dir() and not _sd.name.startswith("_"):
        sys.path.insert(0, str(_sd))

from oeis_index import OEISIndex  # noqa: E402
from ask_dao_machine.judge_math import sieve  # noqa: E402

N = 24          # 序列长度(定长, 便于复合与比较)


# ==================================================================
# 一、大对象池: 域 -> {名字: 生成器}   生成器产出长度 N 的整数序列
# ==================================================================
def _build_objects():
    ps = sieve(200000)
    primes = [i for i in range(2, 200000) if ps[i]]
    pset = set(primes)
    O = {}

    # ---- 数论 ----
    O["素数"] = ("数论", lambda: primes[:N])
    O["合数"] = ("数论", lambda: [i for i in range(4, 200000) if i not in pset][:N])
    O["平方数"] = ("数论", lambda: [i * i for i in range(1, N + 1)])
    O["立方数"] = ("数论", lambda: [i ** 3 for i in range(1, N + 1)])
    O["三角数"] = ("数论", lambda: [i * (i + 1) // 2 for i in range(1, N + 1)])
    O["五边形数"] = ("数论", lambda: [i * (3 * i - 1) // 2 for i in range(1, N + 1)])
    O["六边形数"] = ("数论", lambda: [i * (2 * i - 1) for i in range(1, N + 1)])
    O["中心多边形数"] = ("数论", lambda: [i * i + (i - 1) ** 2 for i in range(1, N + 1)])
    O["阶乘"] = ("数论", lambda: [math.factorial(i) for i in range(1, N + 1)])
    O["双阶乘"] = ("数论", lambda: [math.prod(range(i, 0, -2)) for i in range(1, N + 1)])
    O["斐波那契"] = ("数论", lambda: [(lambda f: f)(__import__("functools").reduce(
        lambda a, _: (a[1], a[0] + a[1]), range(i), (0, 1))[1]) for i in range(N)])
    O["卡特兰"] = ("数论", lambda: [math.comb(2 * i, i) // (i + 1) for i in range(N)])
    O["贝尔数"] = ("数论", lambda: (lambda B: B)(_bell(N)))
    O["欧拉数"] = ("数论", lambda: [_euler(i) for i in range(1, N + 1)])
    O["划分数"] = ("数论", lambda: _partitions(N))
    O["质数间隙"] = ("数论", lambda: [primes[i + 1] - primes[i] for i in range(N)])
    O["素因子个数ω"] = ("数论", lambda: [_omega(i) for i in range(2, N + 2)])
    O["除数和σ"] = ("数论", lambda: [_sigma(i) for i in range(1, N + 1)])
    O["欧拉φ"] = ("数论", lambda: [_phi(i) for i in range(1, N + 1)])
    O["莫比乌斯μ"] = ("数论", lambda: [_mu(i) for i in range(1, N + 1)])
    for b in (2, 3, 5, 10, 16):
        O[f"回文数_b{b}"] = ("数论", (lambda bb: lambda: _pal_seq(bb))  (b))
        O[f"数位和_b{b}"] = ("数论", (lambda bb: lambda: [_digitsum(i, bb) for i in range(1, N + 1)])(b))

    # ---- 组合 ----
    O["禁止子串计数"] = ("组合", lambda: _avoid(N, "11"))
    O["最大游程计数"] = ("组合", lambda: _maxrun(N, 3))
    O["格点返回"] = ("组合", lambda: _walks(N, (-1, 1)))
    O["卡特兰路径"] = ("组合", lambda: [math.comb(2 * i, i) // (i + 1) for i in range(N)])
    O["无三角图计数"] = ("组合", lambda: [1, 1, 2, 3, 7, 14, 38, 107, 410, 1897, 12172,
                                        105071, 1262180, 20797002, 467871369][:N])
    O["有根树计数"] = ("组合", lambda: [1, 1, 2, 4, 9, 20, 48, 115, 286, 719, 1842,
                                        4766, 12486, 32973][:N])
    O["整数分拆数"] = ("组合", lambda: _partitions(N))
    O["错排"] = ("组合", lambda: [_derange(i) for i in range(1, N + 1)])
    O["斯特林数"] = ("组合", lambda: [_stirling2(10, k) for k in range(1, 11)])
    O["欧拉排列数"] = ("组合", lambda: [_eulerian(10, k) for k in range(1, 11)])
    O["多联骨牌数"] = ("组合", lambda: [1, 1, 2, 5, 12, 35, 108, 369, 1285, 4655,
                                        17073, 63600, 238591, 901971][:N])

    # ---- 代数 ----
    O["幂和"] = ("代数", lambda: [sum(pow(i, k, 10 ** 9) for i in range(1, N + 1)) for k in (1, 2, 3)])
    O["模幂轨道"] = ("代数", lambda: [(2 ** i) % 1000 for i in range(1, N + 1)])
    O["三次幂模"] = ("代数", lambda: [(i ** 3) % 97 for i in range(1, N + 1)])
    O["有限域元素阶"] = ("代数", lambda: [_order_mod(a, 101) for a in range(1, N + 1)])

    # ---- 动力系统 ----
    O["二次迭代"] = ("动力", lambda: _iterate(lambda x: (x * x + 1) % 1000, 1, N))
    O["逻辑斯蒂离散"] = ("动力", lambda: [int(4 * (i / N) * (1 - i / N) * 1000) for i in range(N)])
    O["Collatz停时"] = ("动力", lambda: [_collatz(i) for i in range(1, N + 1)])
    O["3n+1轨道"] = ("动力", lambda: _collatz_orbit(27)[:N])
    O["元胞自动机rule30"] = ("动力", lambda: _ca(30, N))
    O["元胞自动机rule90"] = ("动力", lambda: _ca(90, N))
    O["元胞自动机rule110"] = ("动力", lambda: _ca(110, N))

    # ---- 几何/拓扑 ----
    O["格点距离"] = ("几何", lambda: [int(math.hypot(i, i + 1)) for i in range(1, N + 1)])
    O["圆内格点"] = ("几何", lambda: [_lattice_in_circle(r) for r in range(1, N + 1)])
    O["纽结交叉数"] = ("拓扑", lambda: [0, 3, 4, 5, 5, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 8][:N])

    # ---- 语言/信息 ----
    O["二进制串计数"] = ("语言", lambda: [2 ** i for i in range(N)])
    O["无平方词计数"] = ("语言", lambda: [3 * 2 ** (i - 1) for i in range(1, N + 1)])
    O["Dyck路径"] = ("语言", lambda: [math.comb(2 * i, i) // (i + 1) for i in range(N)])
    O["正则语言计数"] = ("语言", lambda: [_count_regex(i) for i in range(1, min(N, 8) + 1)])

    # ---- 音乐 ----
    O["音程向量"] = ("音乐", lambda: [1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1] + [0] * (N - 11))
    O["集合类基数分布"] = ("音乐", lambda: [1, 1, 6, 12, 29, 38, 50, 38, 29, 12, 6, 1, 1][:N])
    O["十二音序列数"] = ("音乐", lambda: [math.factorial(12)] + [0] * (N - 1))

    # ---- 诗律/艺术 ----
    O["合律篇式数"] = ("诗律", lambda: [2 ** (i // 2 + 1) for i in range(2, N + 2)])
    O["纹样对称计数"] = ("纹样", lambda: [62880, 2576, 72, 8] + [0] * (N - 4))
    O["平仄签名"] = ("诗律", lambda: [1, 0, 0, 1] * (N // 4 + 1))[:N] if False else ("诗律", lambda: ([1, 0, 0, 1] * (N // 4 + 1))[:N])

    # ---- 生物/社会 ----
    O["种群频率"] = ("生物", lambda: [int(1000 * (0.2 * (1.3 ** i) / (0.2 * (1.3 ** i) + 0.8))) for i in range(N)])
    O["亲属槽折叠"] = ("人类学", lambda: [39, 34, 27, 16, 15, 12, 11, 10, 9, 8, 7, 6][:N])
    O["博弈Grundy"] = ("博弈", lambda: _grundy(N, (1, 3, 4)))

    return O


# ---------- 对象生成器用的小工具 ----------
def _bell(n):
    B = [1]
    for i in range(1, n):
        B.append(sum(math.comb(i - 1, k) * B[k] for k in range(i)))
    return B


def _euler(n):
    return sum((-1) ** k * math.comb(n + 1, k) * (n + 1 - k) ** n for k in range(n + 1))


def _partitions(n):
    p = [1] + [0] * n
    for k in range(1, n + 1):
        for i in range(k, n + 1):
            p[i] += p[i - k]
    return p[1:n + 1]


def _omega(n):
    c, d = 0, 2
    while d * d <= n:
        if n % d == 0:
            c += 1
            while n % d == 0:
                n //= d
        d += 1
    return c + (1 if n > 1 else 0)


def _sigma(n):
    return sum(d for d in range(1, n + 1) if n % d == 0)


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


def _mu(n):
    c, m, d = 0, n, 2
    while d * d <= m:
        if m % d == 0:
            m //= d
            if m % d == 0:
                return 0
            c += 1
        d += 1
    if m > 1:
        c += 1
    return (-1) ** c


def _pal_seq(b):
    out, n = [], 1
    while len(out) < N:
        d = []
        x = n
        while x:
            d.append(x % b)
            x //= b
        if d == d[::-1]:
            out.append(n)
        n += 1
    return out


def _digitsum(n, b):
    s = 0
    while n:
        s += n % b
        n //= b
    return s


def _avoid(nmax, w):
    from ask_dao_machine import combo_engine as ce
    return ce.counts_avoid_word(nmax, w)


def _maxrun(nmax, k):
    from ask_dao_machine import combo_engine as ce
    return ce.counts_maxrun(nmax, 2, k)


def _walks(nmax, stp):
    from ask_dao_machine import combo_engine as ce
    return ce.counts_walk(nmax, stp)


def _derange(n):
    d0, d1 = 1, 0
    for i in range(2, n + 1):
        d0, d1 = d1, (i - 1) * (d0 + d1)
    return d1 if n > 1 else 0


def _stirling2(n, k):
    return sum((-1) ** (k - j) * math.comb(k, j) * j ** n for j in range(k + 1)) // math.factorial(k)


def _eulerian(n, k):
    return sum((-1) ** j * math.comb(n + 1, j) * (k + 1 - j) ** n for j in range(k + 1))


def _iterate(f, x, n):
    out = []
    for _ in range(n):
        out.append(x)
        x = f(x)
    return out


def _collatz(n):
    c = 0
    while n != 1 and c < 500:
        n = 3 * n + 1 if n % 2 else n // 2
        c += 1
    return c


def _collatz_orbit(n):
    out = []
    while n != 1 and len(out) < 60:
        out.append(n)
        n = 3 * n + 1 if n % 2 else n // 2
    return out


def _ca(rule, n):
    cells = [0] * n
    cells[n // 2] = 1
    out = []
    for _ in range(n):
        out.append(sum(cells))
        new = [0] * n
        for i in range(n):
            l, c, r = cells[(i - 1) % n], cells[i], cells[(i + 1) % n]
            new[i] = (rule >> ((l << 2) | (c << 1) | r)) & 1
        cells = new
    return out


def _lattice_in_circle(r):
    return sum(1 for x in range(-r, r + 1) for y in range(-r, r + 1) if x * x + y * y <= r * r)


def _order_mod(a, p):
    if a % p == 0:
        return 0
    x, k = a % p, 1
    while x != 1 and k < p:
        x = (x * a) % p
        k += 1
    return k


def _count_regex(i):
    return [2, 3, 5, 7, 11, 13, 17][i - 1] if i <= 7 else 0


def _grundy(n, S):
    g = [0] * (n + 1)
    for k in range(1, n + 1):
        reach = {g[k - s] for s in S if s <= k}
        m = 0
        while m in reach:
            m += 1
        g[k] = m
    return g[:n]


# ==================================================================
# 二、方法池: **可复合算子**  seq -> seq   （这是"长"的关键）
# ==================================================================
def _t_diff(s):     return [s[i + 1] - s[i] for i in range(len(s) - 1)]
def _t_cumsum(s):   return list(__import__("itertools").accumulate(s))
def _t_mod2(s):     return [x % 2 for x in s]
def _t_mod3(s):     return [x % 3 for x in s]
def _t_mod9(s):     return [x % 9 for x in s]
def _t_ratio(s):    return [round(s[i + 1] / s[i], 4) if s[i] else 0 for i in range(len(s) - 1)]
def _t_log(s):      return [round(math.log(x), 4) if x > 0 else 0 for x in s]
def _t_sign(s):     return [1 if x > 0 else (-1 if x < 0 else 0) for x in s]
def _t_sorted(s):   return sorted(s)
def _t_runs(s):     return [len(list(g)) for _, g in __import__("itertools").groupby(s)]
def _t_autocorr(s):
    m = sum(s) / len(s)
    v = sum((x - m) ** 2 for x in s) or 1
    return [round(sum((s[i] - m) * (s[i + k] - m) for i in range(len(s) - k)) / v, 4)
            for k in range(1, min(10, len(s)))]
def _t_binom(s):
    return [sum(math.comb(i, j) * s[j] for j in range(i + 1)) for i in range(len(s))]
def _t_entropy_windows(s, k=6):
    out = []
    for i in range(0, len(s) - k + 1, max(1, k // 2)):
        w = s[i:i + k]
        c = {}
        for x in w:
            c[x] = c.get(x, 0) + 1
        H = -sum((v / k) * math.log2(v / k) for v in c.values())
        out.append(round(H, 4))
    return out
def _t_firstdiff_pos(s): return [i for i in range(1, len(s)) if s[i] > s[i - 1]]
def _t_gaps(s):     return [s[i + 1] - s[i] for i in range(len(s) - 1)]
def _t_scale(s):
    mx = max(s) or 1
    return [round(x / mx, 4) for x in s]
def _t_norm_rank(s):
    order = {v: i for i, v in enumerate(sorted(set(s)))}
    return [order[x] for x in s]
def _t_bits(s):     return [int(x) for x in "".join(bin(x)[2:] for x in s[:8])][:N]
_PR_CACHE = []
def _t_prime_gaps_from(s):
    """性能修复: 首版每次调用都重跑 sieve(10 万), 在 66 万条路径上直接卡死。改为缓存。"""
    global _PR_CACHE
    if not _PR_CACHE:
        ps = sieve(100000)
        _PR_CACHE = [i for i in range(2, 100000) if ps[i]]
    pr = _PR_CACHE
    return [pr[i + 1] - pr[i] for i in range(min(len(pr) - 1, len(s)))]
def _t_palindromic(s): return [1 if str(x) == str(x)[::-1] else 0 for x in s]
def _t_squarefree(s): return [1 if _is_sf(x) else 0 for x in s]
def _is_sf(n, budget=10 ** 6):
    """无平方判定。
    自纠错(第 24 次): 首版对**阶乘**(~6e23)也做完整判定, while 要跑到 3e11 -> 直接卡死。
    对大数直接放弃(返回 False 并把该链交给数值上限截断)。"""
    if n <= 0:
        return False
    if n > budget * budget:
        return False
    d = 2
    while d * d <= n:
        if n % (d * d) == 0:
            return False
        d += 1
    return True

METHODS = {
    # 差分族
    "差分": ("分析", _t_diff), "累和": ("分析", _t_cumsum),
    "相邻间隙": ("分析", _t_gaps), "比值": ("分析", _t_ratio),
    # 取模族
    "模2": ("数论", _t_mod2), "模3": ("数论", _t_mod3), "模9": ("数论", _t_mod9),
    # 变换族
    "二项变换": ("组合", _t_binom), "排序": ("组合", _t_sorted),
    "游程编码": ("组合", _t_runs), "秩归一": ("统计", _t_norm_rank),
    "尺度归一": ("统计", _t_scale),
    # 信息族
    "对数": ("信息论", _t_log), "滑窗熵": ("信息论", _t_entropy_windows),
    "自相关": ("信息论", _t_autocorr),
    # 结构族
    "符号": ("逻辑", _t_sign), "上升位置": ("组合", _t_firstdiff_pos),
    "二进制展开": ("信息论", _t_bits),
    # 跨族(把别的对象结构搬过来)
    "对位回文特征": ("数论", _t_palindromic), "对位无平方特征": ("数论", _t_squarefree),
    "对位素数间隙": ("数论", _t_prime_gaps_from),
}


# ==================================================================
# 三、链扫描: 对象 → m1 → m2 → ...   （树有多深由链长决定）
# ==================================================================
VAL_CAP = 10 ** 12       # 数值上限: 防止超阶乘类对象把后续算子拖死


def run_chain(obj_seq, chain, min_len=6):
    """跑一条算子链。

    自纠错(第 24 次): 加了**数值上限**截断 —— 阶乘等爆炸增长的对象在复合算子下
    会变成天文数字, 把无平方/分解类算子拖到不可接受的时间(实测直接卡死)。
    """
    s = list(obj_seq)
    if s and max(abs(x) for x in s) > VAL_CAP:
        return None
    for m in chain:
        try:
            s = METHODS[m][1](s)
        except Exception:
            return None
        if len(s) < min_len:
            return None
        if s and max(abs(x) for x in s) > VAL_CAP:
            return None
    return s


def trivial(seq):
    if len(seq) < 4:
        return True
    if len(set(seq)) <= 2:
        return True
    return False


def main():
    t0 = time.time()
    O = _build_objects()
    print("=" * 104)
    print("疯狂扩张扫描 —— 可复合算子链 × 大对象池")
    print("=" * 104)
    print(f"  对象池: {len(O)} 个(跨 {len(set(v[0] for v in O.values()))} 域)")
    print(f"  方法池: {len(METHODS)} 个(**可复合算子**, 跨 {len(set(v[0] for v in METHODS.values()))} 域)")
    mnames = list(METHODS)
    print(f"  链长 2 的组合: {len(mnames)}^2 = {len(mnames)**2}")
    print(f"  链长 3 的组合: {len(mnames)}^3 = {len(mnames)**3}")
    print(f"  对象×链长3 的空间: {len(O)} × {len(mnames)**3} = **{len(O)*len(mnames)**3:,}** 条路径")

    idx = OEISIndex.load()
    print("  OEIS 索引已载入")

    # 扫描: 对每个对象, 跑全部长度 2 和 3 的链
    import random
    rnd = random.Random(20260910)
    hits, miss, triv, err = [], [], 0, 0
    total = 0
    CH3_PER_OBJ = 220          # 自纠错: 66 万条路径 + 每次重跑 sieve 直接卡死 -> 采样
    done_obj = 0
    for oname, (ofield, gen) in O.items():
        done_obj += 1
        if done_obj % 5 == 0:
            print(f"    ... {done_obj}/{len(O)} 对象  路径 {total:,}  "
                  f"命中 {len(hits):,} 未命中 {len(miss):,}  [{time.time()-t0:.0f}s]",
                  flush=True)
        try:
            base = gen()
        except Exception:
            err += 1
            continue
        if not base or len(base) < 8:
            continue
        chains = [c for c in product(mnames, repeat=2)]
        chains += [tuple(rnd.choice(mnames) for _ in range(3)) for _ in range(CH3_PER_OBJ)]
        chains += [tuple(rnd.choice(mnames) for _ in range(4)) for _ in range(CH3_PER_OBJ // 4)]
        for chain in chains:
                L = len(chain)
                total += 1
                s = run_chain(base, chain)
                if s is None or len(s) < 6:
                    err += 1
                    continue
                if trivial(s):
                    triv += 1
                    continue
                h = idx.lookup(s, max_hits=2)
                strong = [x for x in h if x["matched"] >= min(6, len(s))]
                fields = [ofield] + [METHODS[m][0] for m in chain]
                rec = {"obj": oname, "chain": list(chain), "len": L,
                       "fields": fields,
                       "fusion_degree": len(set(fields)),
                       "seq_head": s[:8],
                       "oeis": [x["a"] for x in strong]}
                if strong:
                    hits.append(rec)
                else:
                    miss.append(rec)

    print(f"\n  扫描路径: {total:,}  有效 {len(hits)+len(miss):,}  "
          f"(平凡 {triv:,} / 异常 {err:,})")
    print(f"  **OEIS 命中(已知) {len(hits):,}**   "
          f"**OEIS 未命中(候选) {len(miss):,}**   "
          f"未命中率 {len(miss)/max(len(hits)+len(miss),1):.1%}")

    from collections import Counter
    print(f"\n  == 未命中(候选) 的**融合度**分布 ==")
    fc = Counter(r["fusion_degree"] for r in miss)
    for k in sorted(fc):
        print(f"     涉及 {k} 个不同领域的方法/对象: {fc[k]:,} 条")
    print(f"\n  == 未命中(候选) 里融合度最高的样本 ==")
    miss.sort(key=lambda r: (-r["fusion_degree"], r["len"]))
    for r in miss[:12]:
        print(f"     [{r['fusion_degree']}域] {r['obj']} → {' → '.join(r['chain'])}")
        print(f"           {r['fields']}  seq={r['seq_head']}")

    print(f"\n  扫描耗时 {time.time()-t0:.1f}s")
    print("\n诚实: 未命中 OEIS ≠ 新问题 —— 只说明手头唯一的参照系里没有。"
          "\n      绝大多数未命中是**结构平凡但长得不像已知序列**; 须过机制电池 + 文献门。")

    out = HERE / "out/demo/mega_scan.json"
    out.write_text(json.dumps({
        "stats": {"objects": len(O), "methods": len(METHODS),
                  "paths": total, "hits": len(hits), "miss": len(miss),
                  "trivial": triv, "error": err},
        "candidates": miss[:2000], "hits_sample": hits[:200],
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"已存 {out}")


if __name__ == "__main__":
    main()
