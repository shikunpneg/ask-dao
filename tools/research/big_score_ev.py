# -*- coding: utf-8 -*-
"""tools/research/big_score_ev.py — 证据依赖版当务评分(整改版)
每分项必须提供证据字段, 缺则记 0; 用于阻断"模板自带触发词=自灌水"。
证据字段: sources[(claim, ref)], route(判定器/experiment/仿真/none),
         prediction(可检验新预言原文), measurement(测量名), anomalies[refs>=3],
         age_years, experiment_design
"""
from typing import Dict, List

ITEMS = [("H1统一", 2.0), ("H2悖论", 2.0), ("H3公设", 2.0), ("H4预言", 1.5),
         ("H5测量", 1.5), ("H6异常", 1.0), ("H7工具", 1.0), ("H8逆向", 1.0),
         ("H9悬置", 1.0), ("H10判决实验", 1.0)]


def score_ev(c: Dict) -> Dict:
    ev = c.get("evidence", {})
    src = ev.get("sources", [])
    per, notes = {}, {}
    # 统一: 需 ≥2 条有出处的独立陈述, 且分属不同领域/框架
    per["H1统一"] = 2.0 if len(src) >= 2 and ev.get("distinct_frameworks") else 0.0
    notes["H1统一"] = "需≥2条带出处陈述且框架不同" if per["H1统一"] == 0 else "OK"
    per["H2悖论"] = 2.0 if ev.get("conflicting_pair_refs") and len(ev["conflicting_pair_refs"]) >= 2 else 0.0
    notes["H2悖论"] = "需两个公认结论的出处" if per["H2悖论"] == 0 else "OK"
    per["H3公设"] = 2.0 if ev.get("axiom_ref") else 0.0
    notes["H3公设"] = "需指出被追问的公设/定义及出处" if per["H3公设"] == 0 else "OK"
    per["H4预言"] = 1.5 if ev.get("prediction") else 0.0
    notes["H4预言"] = "需写出尚未观测的可检验预言" if per["H4预言"] == 0 else "OK"
    per["H5测量"] = 1.5 if ev.get("measurement") else 0.0
    notes["H5测量"] = "需点名测量/仪器" if per["H5测量"] == 0 else "OK"
    per["H6异常"] = 1.0 if len(ev.get("anomaly_refs", [])) >= 3 else 0.0
    notes["H6异常"] = "需≥3条独立异常出处" if per["H6异常"] == 0 else "OK"
    per["H7工具"] = 1.0 if ev.get("method_gap") else 0.0
    notes["H7工具"] = "需说明缺哪种方法/工具" if per["H7工具"] == 0 else "OK"
    per["H8逆向"] = 1.0 if ev.get("reverse_evidence") else 0.0
    notes["H8逆向"] = "需给出已知结果与反推目标" if per["H8逆向"] == 0 else "OK"
    a = ev.get("age_years", 0)
    per["H9悬置"] = 2.0 if a >= 100 else (1.0 if a >= 30 else 0.0)
    notes["H9悬置"] = f"悬置{a}年" if per["H9悬置"] else "未提供悬置年限"
    per["H10判决实验"] = 1.0 if ev.get("experiment_design") else 0.0
    notes["H10判决实验"] = "需给出5年内可做的实验设计" if per["H10判决实验"] == 0 else "OK"
    return {"per": per, "total": round(sum(per.values()), 1), "notes": notes,
            "route": ev.get("route", "none")}
