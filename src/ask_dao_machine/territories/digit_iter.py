# -*- coding: utf-8 -*-
"""territories/digit_iter.py — 领地: 数位迭代族(第二个稀疏领地)

为什么稀疏: 乘法持续数(multiplicative persistence)依赖**进制**, 各族(base b, 阈值 k)
是独立问题。base 10 的"持续数是否有界"是著名未解问题(Erdős 猜想无界), 其余进制少人做。

本领地: holds(n) = pers_b(n) <= k; 例外集 = {n : pers_b(n) > k} = "需更多步才能塌到单位数"。
"""
from ..territory_engine import Spec, Territory

HI = 20000


def persistence(n: int, b: int) -> int:
    """乘法持续数: 反复取各位数字之积直到 < b。"""
    steps = 0
    while n >= b:
        prod, x = 1, n
        while x:
            prod *= x % b
            x //= b
        n = prod
        steps += 1
    return steps


def _spec(b: int, k: int, cls: dict) -> Spec:
    def holds(n, _b=b, _k=k):
        return persistence(n, _b) <= _k

    return Spec(
        id=f"di{b}_pers_k{k}",
        claim=f"每个 n 的乘法持续数(base {b}) ≤ {k}",
        holds=holds, classes=cls,
        params={"进制": b, "阈值k": k, "结构": "乘法持续数"},
        step=1, quantity=f"n ∈ [2,{HI}]; 进制 b={b}; 阈值 k={k}",
        strength="阈值k")   # 强度轴: k 越大主张越弱; 进制是语境, 不同进制不可比


def _classes(hi=HI):
    """类库: 供机器自主刻画例外(如"例外是否都含数字0")"""
    def digit_set(b, d):
        out = set()
        for n in range(2, hi + 1):
            x = n
            while x:
                if x % b == d:
                    out.add(n)
                    break
                x //= b
        return out
    return {
        "含数字0(十进制)": digit_set(10, 0),
        "含数字5(十进制)": digit_set(10, 5),
        "偶数": {n for n in range(2, hi + 1) if n % 2 == 0},
    }


def _specs():
    out = []
    cls = _classes()
    for b in (10, 3):
        for k in (3, 4, 5):
            out.append(_spec(b, k, cls))
    return out


DIGIT_ITER = Territory(
    name="digit_iter",
    family="数位迭代(乘法持续数)",
    literature="乘法持续数(multiplicative persistence): base 10 是否有界为著名未解问题"
               "(Erdős 猜想无界); 非十进制变体文献稀少。相关: Sloane A003001(最小持续数).",
    motifs=["数位迭代", "乘法持续数", "进制表示"],
    seed="数位反复相乘会塌到单位数; '需要很多步才塌'的 n 有多少、长什么样?",
    specs=_specs)
