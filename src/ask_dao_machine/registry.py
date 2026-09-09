# -*- coding: utf-8 -*-
"""registry.py — 母题库登记库(86): 数学核心 + 全域(跨9域), 数据在 assets/registry.json。"""
import json
from pathlib import Path
from typing import Dict, List


class Registry:
    def __init__(self, path: Path):
        self.path = path
        raw = json.loads(path.read_text(encoding="utf-8"))
        self.math_core: List[dict] = raw["math_core"]           # 可实例化
        self.domains: Dict[str, List[dict]] = raw["domains"]    # 全域登记(待实例化)
        self._total = len(self.math_core) + sum(len(v) for v in self.domains.values())

    @classmethod
    def bundled(cls) -> "Registry":
        return cls(Path(__file__).parent / "assets" / "registry.json")

    @property
    def total(self) -> int:
        return self._total

    def domain_counts(self) -> List[dict]:
        return [{"domain": k, "count": len(v)} for k, v in self.domains.items()]

    def summarize(self) -> dict:
        return {"total": self.total, "math_core": len(self.math_core),
                "domains": self.domain_counts()}

    def math_motif(self, name: str) -> dict:
        for m in self.math_core:
            if m["name"] == name:
                return m
        return {"name": name, "type": "?", "note": ""}
