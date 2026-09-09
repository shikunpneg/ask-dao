# -*- coding: utf-8 -*-
"""novelty_judge.py — LLM 新颖性裁判(操作层判官) + 分级协议。

分级(机器-LLM 操作层可裁, 无需人工):
  N0 明显已知         : honesty 含 已知/著名/已证, 或命中内置签名库
  N1 大概率已知/标准推论: 结构上可被已知定理族覆盖(如 稠密集相加覆盖=标准筛法/圆法推论;
                      记录型=平凡或经典; 模类反例=经典论证)
  N2 疑似未见(检索级)  : 未命中已知库+未见直接文献+LLM 直觉不排除新颖 —— 标记'建议二次检索/人工复核'
  N3 强候选           : N2 且结构上未见明显可推来源, 值得写成可验证命题
裁判证据: {retrieval(查证器结果), structural(LLM 结构推理), confidence}
人工介入门槛: 仅在 (a) N2/N3 候选进入正式发表流程, 或 (b) 用户要求盖章时。
"""
KNOWN_PATTERNS = {
    "两稀疏类相加覆盖全偶数": "N1 标准筛法/圆法推论(稠密或次稠密集相加覆盖; 例: 两平方free=Estermann系, 质数+半素数=Chen系)",
    "单项纪录取值": "N1 纪录是事实; 其'纪录=新'不成立, 除非纪录本身突破文献上界(需检索比对)",
    "模类反例": "N0 经典模论证",
    "已知著名开放题撞上": "N0 机器重发现著名题, 非新",
    "已证定理复核": "N0",
    "存在性例证": "N1 平凡或经典",
}


def judge(record: dict, retrieval: dict = None) -> dict:
    """对单个问题记录返回 LLM-裁判分级(启发式规则+可人工覆盖的结论字段)。"""
    hon = record.get("honesty", "")
    st = record.get("status", "")
    stmt = record.get("statement", "")
    tpl = record.get("template", "")
    if any(k in hon for k in ("已知", "著名", "已证")):
        return {"verdict": "N0 明显已知", "rule": hon, "confidence": 1.0,
                "human_needed": False}
    # 纪录型: 事实/纪录非新(除非突破文献上界)
    if "纪录" in hon or "纪录" in stmt or "记录" in hon:
        return {"verdict": "N1 纪录是事实, 非新(除非突破文献上界)", "rule": KNOWN_PATTERNS["单项纪录取值"],
                "confidence": 0.9, "human_needed": False}
    # 结构模式判定(LLM 记忆库/推理): 按模板+对象特征
    binds = record.get("binds", {})
    tpl = record.get("template", "")
    stmt = record.get("statement", "")
    if "惊喜" in hon or "需查证" in hon or "未见" in hon:
        # 覆盖型两数和: LLM 结构推理 -> 大概率 N1(除非模类/奇偶阻塞, 已有记录表明未阻塞)
        if any(k in tpl for k in ("两数和", "两项和", "覆盖扫描")) or \
           ("可写成" in stmt and "+" in stmt and "偶数" in stmt):
            return {"verdict": "N1 大概率已知/标准推论(稠密集相加覆盖=筛法/圆法推论)",
                    "rule": KNOWN_PATTERNS["两稀疏类相加覆盖全偶数"],
                    "retrieval": (retrieval or {}).get("status", "无"),
                    "confidence": 0.8, "human_needed": False}
        return {"verdict": "N2 疑似未见(检索级)·建议二次检索",
                "rule": "未命中已知库且结构未见明显可推来源",
                "retrieval": (retrieval or {}).get("status", "无"),
                "confidence": 0.5, "human_needed": True}
    if "悬置" in st:
        return {"verdict": "N0 著名开放题(重发现)", "rule": KNOWN_PATTERNS["已知著名开放题撞上"],
                "confidence": 1.0, "human_needed": False}
    if "假" in st:
        return {"verdict": "N0 经典模论证反例", "rule": KNOWN_PATTERNS["模类反例"],
                "confidence": 1.0, "human_needed": False}
    if "真" in st:
        return {"verdict": "N1 大概率已知/标准工具可证", "rule": "机器验证类: 覆盖或存在性, 多为经典",
                "confidence": 0.7, "human_needed": False}
    return {"verdict": "N2 疑似未见(检索级)", "rule": "默认升级待检", "confidence": 0.4,
            "human_needed": True}


def judge_all(problems_json_path: str, use_retrieval: bool = True) -> dict:
    import json
    from pathlib import Path
    data = json.loads(Path(problems_json_path).read_text(encoding="utf-8"))
    summary = {}
    for p in data["problems"]:
        r = judge(p, p.get("literature"))
        p["novelty_judge"] = r
        key = r["verdict"].split(" ")[0]
        summary[key] = summary.get(key, 0) + 1
    Path(problems_json_path).write_text(
        json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return summary
