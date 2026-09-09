# -*- coding: utf-8 -*-
"""ask_dao_machine — 问题制造器(Problem Maker)。

一个把"问题"当作一等对象制造出来的可复用模块:
  母题库(登记库) × 组合引擎(模板) → 候选命题 → 判定器(真/假/悬置/待实验)
  → 问题记录(完整出处链) → 可视化(解释问题怎么长出来的)。

用法(编程):
    from ask_dao_machine import ProblemMaker
    maker = ProblemMaker()
    ps = maker.run("math")
    print(ps.stats())
    maker.save(ps, "out/math.json")
CLI:
    python -m ask_dao_machine all --out out/demo
"""
from .pipeline import ProblemMaker
from .registry import Registry
from .model import ProblemRecord, ProblemSet
from . import viz, math_engine, aesthetics_engine

__version__ = "0.1.0"
__all__ = ["ProblemMaker", "Registry", "ProblemRecord", "ProblemSet",
           "viz", "math_engine", "aesthetics_engine", "__version__"]
