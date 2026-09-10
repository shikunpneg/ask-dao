# -*- coding: utf-8 -*-
"""territories/combo_control.py — 领地: 组合约束族(**稠密对照组**)

它不是用来产问题的, 是用来**验证领地方法本身**的阴性对照:
组合约束(禁构/游程)是已知稠密领地(R23 实测幸存率 0%), 预期本领地的猜想
**全部被例外稠密度守卫否证**或产出无结构问题。若本领地也"产出开放问题",
说明守卫失灵 —— 它是方法学对照, 不是候选产地。
"""
from ..territory_engine import Spec, Territory

HI = 20000


def _avoid_word_spec(word: str, cls: dict) -> Spec:
    def holds(n, _w=word):
        return _w not in bin(n)[2:]

    return Spec(
        id=f"cc_avoid_{word}",
        claim=f"每个 n 的二进制表示不含子串 '{word}'",
        holds=holds, classes=cls, params={"禁构": word, "进制": 2},
        step=1, quantity=f"n ∈ [1,{HI}]; 二进制表示")


def _classes(hi=HI):
    return {"偶数": {n for n in range(1, hi + 1) if n % 2 == 0},
            "平方数": {x * x for x in range(1, int(hi ** 0.5) + 1)}}


def _specs():
    cls = _classes()
    return [_avoid_word_spec(w, cls) for w in ("11", "101", "000")]


COMBO_CONTROL = Territory(
    name="combo_control",
    family="组合约束(稠密对照)",
    literature="受限串/禁构计数: OEIS 高密度族(R23 实测本族幸存率 0%)。"
               "**本领地是对照组, 用于验证守卫与稀疏度判据, 不预期产出候选。**",
    motifs=["受限串", "禁构", "稠密对照"],
    seed="(对照)在已知稠密的组合约束族上跑同一套流程, 应当产出不了开放问题。",
    specs=_specs)
