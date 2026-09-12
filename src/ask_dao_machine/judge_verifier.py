# -*- coding: utf-8 -*-
"""verifier.py — 新颖性查证器 (agent-in-the-loop):
  机器生成问题 -> 生成检索式 -> 外部检索(本环境由操作者执行 web_search) -> 结论回写
  三态结论: 已查证-未见直接文献 / 已查证-文献已有 / 需人工复核
  自动层: 内置"著名签名库", 已知命中直接标注, 不进检索队列。"""
import json
from pathlib import Path
from typing import Dict, List, Optional

ASSETS = Path(__file__).parent / "assets"

# 自动层: 著名/已知 签名(按模板+对象类 自动标注)
KNOWN_SIGNATURES = {
    ("T1", "质数", "质数"): {"name": "哥德巴赫猜想", "status": "开放(著名)"},
    ("T2", "质数", "质数"): {"name": "莱莫因/利维猜想", "status": "开放(著名)"},
    ("T3", "质数", "质数"): {"name": "弱哥德巴赫(已证 2013)", "status": "已证"},
    ("T4", "区间", "质数"): {"name": "贝特朗假设(已证)", "status": "已证"},
    ("T11", "连续平方", "质数"): {"name": "勒让德猜想", "status": "开放(著名)"},
    ("T14", "递推", "Collatz3n+1"): {"name": "Collatz 猜想", "status": "开放(著名)"},
    ("T5", "因子和", None): {"name": "σ(n)=2n+c 族", "status": "视 c(已扫范围证据)"},
}

OPEN_FAMOUS = {
    "准完全数", "奇完全数", "哥德巴赫", "莱莫因", "勒让德", "Collatz",
    "回文质数无穷性", "连续半素数无穷性", "孪生质数",
}


def auto_tag(template: str, class_a: str, class_b: Optional[str] = None) -> Optional[dict]:
    sig = KNOWN_SIGNATURES.get((template, class_a, class_b))
    if sig:
        return sig
    return None


def build_queries(record: dict) -> List[str]:
    """从问题记录生成英文检索式(把 statement 翻成检索关键词组合)。"""
    stmt = record.get("statement", "")
    motifs = record.get("motifs", [])
    m = " ".join(motifs)
    return [
        f'"{stmt[:90]}"',
        f'"{stmt[:60]}" number theory',
        f'{m} theorem conjecture sufficiently large',
    ]


def pending_surprises(problems_path: Path) -> List[dict]:
    """取出所有 honesty 含'惊喜/需查证/未见'的候选。"""
    data = json.loads(Path(problems_path).read_text(encoding="utf-8"))
    return [p for p in data["problems"]
            if ("惊喜" in p.get("honesty", "") or "需查证" in p.get("honesty", "")
                or "未见" in p.get("honesty", ""))]


def record_result(problems_path: Path, id_: str, status: str,
                  sources: List[str], note: str = "") -> Path:
    """把外部查证结论写回问题记录: literature={status, sources, note, date}"""
    path = Path(problems_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    for p in data["problems"]:
        if p.get("id") == id_:
            p["literature"] = {"status": status, "sources": sources, "note": note}
            break
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def record_result_by_ids(problems_path: Path, ids: List[str], status: str,
                         sources: List[str], note: str = "") -> int:
    """同族结论回写整批 id。"""
    path = Path(problems_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    n = 0
    for p in data["problems"]:
        if p.get("id") in set(ids):
            p["literature"] = {"status": status, "sources": sources, "note": note}
            n += 1
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return n


def pending_families(problems_path: Path) -> List[dict]:
    """records 型待查候选按(类A,类B)去重, 供按族检索。"""
    data = json.loads(Path(problems_path).read_text(encoding="utf-8"))
    fam = {}
    for p in data["problems"]:
        if "惊喜" not in p.get("honesty", ""):
            continue
        if "literature" in p:
            continue
        b = p.get("binds", {})
        key = (b.get("类A", ""), b.get("类B", ""))
        if key == ("", ""):
            key = (p["id"], "")
        fam.setdefault(key, []).append(p["id"])
    return [{"family": k, "ids": v, "statement": None} for k, v in fam.items()]
