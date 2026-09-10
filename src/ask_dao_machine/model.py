# -*- coding: utf-8 -*-
"""model.py — 核心数据模型: 每个问题带完整出处链(provenance)。

问题记录字段:
  id, domain, seed(日常疑问), motifs[](组成母题), template, binds(参数),
  statement, judgement{method, evidence...}, status(VERDICT), honesty(诚实标记),
  tree{parent, edge}, origin_steps[](生长步骤文字, 由 tree/edge 推导渲染)
"""
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

TRUE = "真"
FALSE = "假"
OPEN = "悬置(开放)"
PENDING = "待实验/待评审"
# "验到上限"不等于"证明": 必须与 TRUE 分开, 否则是把有限验证冒充真。
FINITE = "有限验证(至扫描上限, 非证明)"

KNOWN = "已知(著名/已证)"
# 诚实纪律: 引擎不得自称新颖。新颖性只能由 novelty_gate 实查 OEIS 后给出。
AWAIT_GATE = "待参照系反查(未过 novelty_gate)"
BASELINE = "及格线产物"


@dataclass
class ProblemRecord:
    id: str
    domain: str
    seed: str
    motifs: List[str]
    template: str
    statement: str
    judgement: Dict[str, Any]
    status: str = OPEN
    honesty: str = ""
    binds: Dict[str, Any] = field(default_factory=dict)
    tree: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["provenance"] = self.provenance_steps()
        return d

    def provenance_steps(self) -> List[str]:
        """把'生长路径'翻译成人话, 供可视化解释。"""
        steps = []
        if self.tree and self.tree.get("parent"):
            steps.append(f"从 {self.tree['parent']} 生长: {self.tree.get('edge','')}".strip())
        if self.motifs:
            steps.append("母题组合: " + " × ".join(self.motifs))
        if self.template:
            steps.append("模板: " + self.template)
        if self.binds:
            steps.append("参数: " + ", ".join(f"{k}={v}" for k, v in self.binds.items()))
        if self.judgement:
            m = self.judgement.get("method", "")
            steps.append(f"判定({m}): {self.status}")
        return steps


@dataclass
class TreeRoot:
    id: str
    label: str
    domain: str
    motifs: List[str]
    seed: str


@dataclass
class ProblemSet:
    domain: str
    roots: List[TreeRoot]
    problems: List[ProblemRecord]

    def stats(self) -> Dict[str, int]:
        c = {"真": 0, "假": 0, "悬置(开放)": 0, "待实验/待评审": 0, "有限验证": 0}
        for p in self.problems:
            if p.status in c:
                c[p.status] += 1
            elif p.status.startswith("有限验证"):
                c["有限验证"] += 1
            elif p.status.startswith("真"):
                c["真"] += 1
            elif p.status.startswith("假"):
                c["假"] += 1
            elif p.status.startswith("悬置"):
                c["悬置(开放)"] += 1
            else:
                c["待实验/待评审"] += 1
        from collections import Counter
        used = Counter()
        for p in self.problems:
            for m in p.motifs:
                used[m] += 1
        return {"problems": len(self.problems), "status": c, "motifs_used": len(used)}

    def to_dict(self) -> Dict[str, Any]:
        return {"domain": self.domain,
                "roots": [asdict(r) for r in self.roots],
                "problems": [p.to_dict() for p in self.problems]}
