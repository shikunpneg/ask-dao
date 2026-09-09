# -*- coding: utf-8 -*-
"""preproblems.py — 前问题检测器:
  在判定记录的"意外信号"里找 前问题(问题成形前的张力)。
  信号类型: 阈值尾窗异常(最后一个例外离扫描上界很近 -> 反例还在远处吗?)
            / 结构反例(模类永久失败) / 覆盖空洞(扫描截断) / 阈值离群(远超同伴)。
  输出 PreProblem: {type, source_id, evidence, pre_problem(未成形), suggest(成形问题), status}
"""
import json
from pathlib import Path
from typing import List


def detect(problems_path: Path, scan_limit: int = 40000,
           tail_frac: float = 0.9) -> List[dict]:
    data = json.loads(Path(problems_path).read_text(encoding="utf-8"))
    out = []
    for p in data["problems"]:
        j = p.get("judgement", {})
        st = p.get("status", "")
        pid = p.get("id", "?")
        if st.startswith("假"):
            fails = j.get("fails_head", [])
            if fails:
                ev = fails[:6]
                out.append({
                    "type": "结构反例",
                    "source_id": pid,
                    "evidence": ev,
                    "pre_problem": f"{pid} 被一个'看着像特例、其实是恒失败类'的东西否决——这个类到底是什么?",
                    "suggest": f"找出使 {p.get('statement','')[:30]}… 恒失败的刻画(模类/结构类)",
                    "status": "已成形(假)+ 前问题: 失败类的完整刻画"})
            continue
        th = j.get("threshold")
        if th is not None:
            frac = th / scan_limit if scan_limit else 1
            if th >= scan_limit:
                out.append({
                    "type": "边界例外(阈值是扫描假象)",
                    "source_id": pid,
                    "evidence": {"last_fail_at": th - 2, "scan_limit": scan_limit, "fails_head": j.get("fails_head", [])[:6]},
                    "pre_problem": f"{pid}: 最后例外贴在扫描边界——可能根本没有'最后一个例外', 失败或许无限地稀疏出现",
                    "suggest": f"转问真正的全称问题: '{p.get('statement','')[:36]}… 的例外有限还是无限?' 并刻画例外族的结构",
                    "status": "真(到上限) -> 前问题: 例外有限性"})
            elif frac >= tail_frac:
                out.append({
                    "type": "阈值尾窗异常",
                    "source_id": pid,
                    "evidence": {"threshold": th, "scan_limit": scan_limit, "fails_head": j.get("fails_head", [])[:6]},
                    "pre_problem": f"{pid}: 最后一个例外紧贴扫描边界 {scan_limit}——扫描之外还有反例吗? 是真定理还只是'碰巧'?",
                    "suggest": f"证明或找反例: 判定 {p.get('statement','')[:50]}… 的阈值是否真的有限",
                    "status": "真(验证到上限) -> 前问题: 边界外未验证"})
        if j.get("capped"):
            out.append({
                "type": "覆盖空洞(扫描截断)",
                "source_id": pid,
                "evidence": {"fails_head": j.get("fails_head", [])[:6]},
                "pre_problem": f"{pid}: 连续失败超上限即截断——空洞的结构(周期? 稀疏?)还没被问出来",
                "suggest": f"刻画 {pid} 失败集合的结构(模类/密度), 而不是满足于'疑似无覆盖'",
                "status": "悬置 -> 前问题: 失败集的结构"})
    return out
