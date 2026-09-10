# -*- coding: utf-8 -*-
"""territories/digit_base.py — 领地: 进制依赖结构(Phase 1 的首选稀疏领地)

为什么选它(LONG_PLAN_V2 Axis T 的判据, 有 R25 实测支撑):
  * R25 实测: 加性数论领地 13 问**全部**落进已发表文献(N0×5/N1×5/N2×3);
  * 而同一引擎产出的「回文数+平方数」在文献检索中**返回空结果** ——
    回文数依赖**十进制表示**, 非常规加性数论对象, 因此文献难以穷尽;
  * 换进制即得新族 => 天然的参数化稀疏空间。

本领地: 多变进制 b, 对象类取 {回文数_b, 平方数, 三角数, 素数}, 组合成两加数覆盖猜想。
"""
from ..judges_math import sieve
from ..territory_engine import Spec, Territory

HI = 20000


def to_base(n: int, b: int):
    if n == 0:
        return [0]
    d = []
    while n:
        d.append(n % b)
        n //= b
    return list(reversed(d))


def is_pal(n: int, b: int) -> bool:
    d = to_base(n, b)
    return d == d[::-1]


def _classes(b: int, hi: int = HI):
    pals = {n for n in range(1, hi + 1) if is_pal(n, b)}
    sq = {x * x for x in range(1, int(hi ** 0.5) + 1)}
    tri = {i * (i + 1) // 2 for i in range(1, int((2 * hi) ** 0.5) + 2)}
    ps = sieve(hi + 1)
    primes = {i for i in range(2, hi + 1) if ps[i]}
    return {"回文数": pals, "平方数": sq, "三角数": tri, "素数": primes}


def _sum_spec(b, a_name, b_name, cls, step=1):
    """n = A + B 型猜想(不限奇偶: 回文数与平方/三角的奇偶都不定)"""
    A = sorted(cls[a_name])
    B = cls[b_name]

    def holds(n, _A=A, _B=B):
        for a in _A:
            if a >= n:
                break
            if (n - a) in _B:
                return True
        return False

    return Spec(
        id=f"dig{b}_{a_name}_{b_name}",
        claim=f"每个 n 可写成 {a_name}(base {b}) + {b_name}",
        holds=holds, classes=cls,
        params={"进制": b, "类A": a_name, "类B": b_name},
        step=step, quantity=f"n ∈ [4,{HI}]; 进制 b={b}")


def _self_number_spec(b, cls, lo=4, hi=HI):
    """通用性对照: 「自数」(self number) —— 不能写成 m + s_b(m) 的 n, 其中 s_b 为数位和。
    holds(n) = n 可被生成(即不是 self number)。
    这是**非两加数结构**的猜想, 用来证明领地协议不依赖'A+B'形状。
    (该族已知, 作对照: 应被文献门判为 N0。)"""
    def gen(m, _b=b):
        s, x = 0, m
        while x:
            s += x % _b
            x //= _b
        return m + s

    # 自纠错: 首版对每个 n 都遍历 m<n, 是 O(n²)(20000 规模直接卡死)。
    # 生成元只到 hi(因为 m + s_b(m) > m), 一次性预计算。
    gen_set = {gen(m, b) for m in range(1, hi + 1)}

    def holds(n):
        return n in gen_set

    return Spec(id=f"dig{b}_self_number",
                claim=f"每个 n 可写成 m + 数位和_b(m)(base {b})",
                holds=holds, classes=cls, params={"进制": b, "结构": "自数"},
                step=1, quantity=f"n ∈ [4,{HI}]; 进制 b={b}")


# Phase 3 (Axis S) 规模化: 多进制形成稀疏度梯度(进制越大越少人做)
BASES = (2, 3, 5, 10, 16)


def _specs():
    out = []
    for b in BASES:
        cls = _classes(b)
        for a, bb in (("回文数", "平方数"), ("回文数", "三角数"), ("回文数", "素数")):
            out.append(_sum_spec(b, a, bb, cls))
        out.append(_sum_spec(b, "回文数", "回文数", cls))
    # 结构对照(非 A+B 形状)
    for b in (10,):
        out.append(_self_number_spec(b, _classes(b)))
    return out


DIGIT_BASE = Territory(
    name="digit_base",
    family="进制依赖结构",
    literature="十进制/进制相关数论: 回文数(palindromic numbers)、self numbers(Colombian)、"
               "digit-sum 族。注: 该族依赖表示(base), 文献覆盖远稀于加性数论。",
    motifs=["进制表示", "回文数", "数位和", "两加数覆盖"],
    seed="把对象类换成'依赖进制的表示'(回文数/数位和), 覆盖例外会长成什么样?",
    specs=_specs)


if __name__ == "__main__":
    import json
    from pathlib import Path
    from ..territory_engine import run_territory
    _, recs, rep = run_territory(DIGIT_BASE, 4, HI)
    print(f"领地 {DIGIT_BASE.name}({DIGIT_BASE.family}): {len(recs)} 个开放问题\n")
    print(f"{'猜想':<44}{'例外':>6}  {'类型':<20}{'机器刻画'}")
    for r in rep["specs"]:
        if "n" not in r or r.get("n", 0) == 0:
            print(f"{r['claim']:<44}     0  {r.get('verdict','')}")
            continue
        cf = r.get("class_fit")
        tag = f"⊆ {cf['class']}" + (f"∪{cf['outside']}" if cf["outside"] else "") if cf else \
              (f"< {r['small_bound']}" if r.get("small_bound") else "—")
        print(f"{r['claim']:<44}{r['n']:>6}  {r['kind']:<20}{tag}")
    Path("out/demo/problems_digit_base.json").parent.mkdir(parents=True, exist_ok=True)
    Path("out/demo/problems_digit_base.json").write_text(
        json.dumps({"domain": "digit_base",
                    "roots": [{"id": "R_digit_base", "label": DIGIT_BASE.family,
                               "domain": "数学", "motifs": DIGIT_BASE.motifs,
                               "seed": DIGIT_BASE.seed}],
                    "problems": [p.to_dict() for p in recs], "report": rep},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n已存 out/demo/problems_digit_base.json")
