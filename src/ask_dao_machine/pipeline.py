# -*- coding: utf-8 -*-
"""pipeline.py — ProblemMaker: 领域引擎 → ProblemSet(问题+出处链) → 序列化/统计
这是对外的主入口, 把"问题制造器"封装为单一可复用模块。"""
import json
import time
from pathlib import Path
from typing import Dict, List

from . import (math_engine, aesthetics_engine, records_engine, fusion_engine,
               lang_info_engine, combo_engine, direction_engine, sparse_engine,
               counterex_engine)
from .model import ProblemSet
from .registry import Registry


class ProblemMaker:
    """问题制造器: run(domain) -> ProblemSet; 每个问题带完整出处链。"""

    def __init__(self, registry: Registry = None):
        self.registry = registry or Registry.bundled()
        self.engines = {
            "math": self._run_math,
            "records": self._run_records,
            "fusion": self._run_fusion,
            "ling": self._run_ling,
            "combo": self._run_combo,
            "direction": self._run_direction,
            "sparse": self._run_sparse,
            "counterex": self._run_counterex,
            "digit_base": self._run_digit_base,
            "aesthetics": aesthetics_engine.run,
        }

    def _run_digit_base(self, limits: dict = None):
        """领地·进制依赖结构(LONG_PLAN_V2 Phase 1 首个稀疏领地)。"""
        from .territories import get as _get
        from .territory_engine import run_territory
        limits = limits or {}
        lo, hi = limits.get("lo", 4), limits.get("hi", 20000)
        roots, records, report = run_territory(_get("digit_base"), lo, hi)
        ps = ProblemSet("digit_base", roots, records)
        setattr(ps, "territory_report", report)
        return ps

    def _run_counterex(self, limits: dict = None):
        """反例驱动: 唯一产出'机器自己答不出的问题'的引擎(status=开放)。"""
        limits = limits or {}
        roots, records, report = counterex_engine.run(
            lo=limits.get("lo", 6), hi=limits.get("hi", 40000))
        ps = ProblemSet("counterex", roots, records)
        setattr(ps, "counterex_report", report)
        return ps

    def _run_sparse(self, limits: dict = None):
        limits = limits or {}
        roots, records = sparse_engine.run(m_hi=limits.get("m_hi", 64),
                                           q_hi=limits.get("q_hi", 9))
        return ProblemSet("sparse", roots, records)

    def _run_math(self, limits: dict = None):
        limits = limits or {}
        return math_engine.run(N=limits.get("N", 300000), M=limits.get("M", 500000))

    def _run_records(self, limits: dict = None):
        limits = limits or {}
        return records_engine.run(N=limits.get("N", 80000), SCAN=limits.get("SCAN", 40000))

    def _run_fusion(self, limits: dict = None):
        limits = limits or {}
        return fusion_engine.run(N=limits.get("N", 1000000), gapN=limits.get("gapN", 300000))

    def _run_ling(self, limits: dict = None):
        return lang_info_engine.run()

    def _run_combo(self, limits: dict = None):
        limits = limits or {}
        root, recs, stat, r = combo_engine.run(nmax=limits.get("nmax", 40))
        ps = ProblemSet("combo", [root], recs)
        setattr(ps, "combo_stat", stat)
        setattr(ps, "r_count", r)
        return ps

    def _run_direction(self, limits: dict = None):
        limits = limits or {}
        return direction_engine.run(N=limits.get("N", 400000), gapN=limits.get("gapN", 200000))

    def list_domains(self) -> List[str]:
        return sorted(self.engines.keys())

    def run(self, domain: str, limits: dict = None) -> ProblemSet:
        if domain not in self.engines:
            raise KeyError(f"未知域: {domain}; 可用: {self.list_domains()}")
        t0 = time.time()
        val = self.engines[domain](limits)
        if isinstance(val, ProblemSet):
            ps = val
        else:
            roots, records = val
            ps = ProblemSet(domain=domain, roots=roots, problems=records)
        ps.domain = domain
        setattr(ps, "elapsed", round(time.time() - t0, 2))
        return ps

    def run_all(self, limits: dict = None) -> Dict[str, ProblemSet]:
        return {d: self.run(d, limits) for d in self.engines}

    @staticmethod
    def save(ps: ProblemSet, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(ps.to_dict(), ensure_ascii=False, indent=1), encoding="utf-8")
        return path
