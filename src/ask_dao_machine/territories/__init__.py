# -*- coding: utf-8 -*-
"""territories — 领地注册表(LONG_PLAN_V2 Phase 1)

每个领地 = 一族猜想 + 该族的结构族名与文献路由。
新增领地只需: 建模块 -> 造 Territory -> 在此登记。

稀疏度(实测, `tools/core/territory_scan.py`):
  digit_base   进制依赖     — R26: 4 问 / 1 问公认未解
  digit_iter   数位迭代     — 待测
  combo_control 组合约束    — **阴性对照**(R23 实测幸存 0%)
"""
from .digit_base import DIGIT_BASE
from .digit_iter import DIGIT_ITER
from .combo_control import COMBO_CONTROL

TERRITORIES = {
    DIGIT_BASE.name: DIGIT_BASE,
    DIGIT_ITER.name: DIGIT_ITER,
    COMBO_CONTROL.name: COMBO_CONTROL,
}

# 对照领地: 不参与"候选产出"统计, 只用于验证守卫
CONTROL = {COMBO_CONTROL.name}


def get(name):
    return TERRITORIES[name]


def names():
    return sorted(TERRITORIES)


def candidate_territories():
    return [t for k, t in sorted(TERRITORIES.items()) if k not in CONTROL]
