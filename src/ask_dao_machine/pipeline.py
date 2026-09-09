# -*- coding: utf-8 -*-
"""pipeline.py — ProblemMaker: 领域引擎 → ProblemSet(问题+出处链) → 序列化/统计
这是对外的主入口, 把"问题制造器"封装为单一可复用模块。"""
import json
import time
from pathlib import Path
from typing import Dict, List

from . import math_engine, aesthetics_engine, records_engine
from .model import ProblemSet
from .registry import Registry


class ProblemMaker:
    """问题制造器: run(domain) -> ProblemSet; 每个问题带完整出处链。"""

    def __init__(self, registry: Registry = None):
        self.registry = registry or Registry.bundled()
        self.engines = {
            "math": self._run_math,
            "records": self._run_records,
            "aesthetics": aesthetics_engine.run,
        }

    def _run_math(self, limits: dict = None):
        limits = limits or {}
        return math_engine.run(N=limits.get("N", 300000), M=limits.get("M", 500000))

    def _run_records(self, limits: dict = None):
        limits = limits or {}
        return records_engine.run(N=limits.get("N", 80000), SCAN=limits.get("SCAN", 40000))

    def list_domains(self) -> List[str]:
        return sorted(self.engines.keys())

    def run(self, domain: str, limits: dict = None) -> ProblemSet:
        if domain not in self.engines:
            raise KeyError(f"未知域: {domain}; 可用: {self.list_domains()}")
        t0 = time.time()
        roots, records = self.engines[domain](limits)
        ps = ProblemSet(domain=domain, roots=roots, problems=records)
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
