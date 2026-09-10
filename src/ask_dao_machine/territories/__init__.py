# -*- coding: utf-8 -*-
"""territories — 领地注册表(LONG_PLAN_V2 Phase 1)

每个领地 = 一族猜想 + 该族的结构族名与文献路由。
新增领地只需: 建模块 -> 造 Territory -> 在此登记。
"""
from .digit_base import DIGIT_BASE

# 领地池(按实测稀疏度排序; 每轮用 literature_silence 实测而非假设)
TERRITORIES = {
    DIGIT_BASE.name: DIGIT_BASE,
}


def get(name):
    return TERRITORIES[name]


def names():
    return sorted(TERRITORIES)
