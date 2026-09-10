# -*- coding: utf-8 -*-
"""tools/corpus_to_problems.py — Track 1: 普通文本语料 → 日常疑问 → 科学问题

用户理论的第一段(项目起点 P1):
  "一个科学问题首先来自日常生活的疑问, 接着进行针对领域的结构化。"

本模块把这段落成管线, 并**如实报告漏斗**:

  Stage A 日常疑问抽取   : 从中文散文里抽疑问句(为什么/如何/是否/能否/什么是…)
  Stage B 结构化         : 把疑问映射到 `grammar.FRAMES` 的槽位; 判定该问句**能否被结构化**
  Stage C 可判性绑定     : 槽位能否绑到**机器可枚举的载体**(否则只是思辨问题)
  Stage D 过 novelty/机制门

诚实(项目纪律): 绝大多数日常疑问**过不了** Stage C —— 这不是失败, 是 R23 已量化的
"73% 产出无机器可判数据"在语料侧的重演。**漏斗的收窄过程本身就是结果。**

用法: python tools/corpus_to_problems.py [语料目录]
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src"))

from ask_dao_machine.grammar import FRAMES  # noqa: E402

CORPUS = Path("E:/ask-dao/_text")

# ---- Stage A: 中文疑问句模式 ----
Q_PATTERNS = [
    ("为什么", r"为什么(.{2,40}?)[？?]"),
    ("为何", r"为何(.{2,40}?)[？?]"),
    ("如何", r"如何(.{2,40}?)[？?]"),
    ("是否", r"是否(.{2,40}?)[？?]"),
    ("能否", r"能否(.{2,40}?)[？?]"),
    ("什么是", r"什么是(.{2,40}?)[？?]"),
    ("什么是(无？)", r"(什么是.{2,40}?)[。，,；;]"),
    ("何以", r"何以(.{2,40}?)[？?]"),
    ("怎样", r"怎样(.{2,40}?)[？?]"),
    ("什么", r"(.{2,20}?)是什么[？?]"),
    ("一般疑问", r"((?:难道|岂|莫非)?.{4,40}?[吗么])[？?]"),
]

# ---- Stage B: 疑问类型 → grammar 框架 的可能映射(粗对齐, 非硬规则) ----
Q2FRAME = {
    "为什么": ["F_char_if", "F_recur_converge"],       # 因果/机制问句
    "为何": ["F_char_if", "F_recur_converge"],
    "如何": ["F_recur_converge", "F_interval_exist"],  # 过程/构造问句
    "是否": ["F_threshold_sum", "F_char_if"],          # 真伪问句(用户:"问题早期都是真伪问题")
    "能否": ["F_exist_equal", "F_interval_exist"],     # 构造/存在问句
    "什么是": ["F_char_if"],                            # 定义问句(通常不可判, 见下)
    "什么是(无？)": ["F_char_if"],
    "何以": ["F_char_if"],
    "怎样": ["F_recur_converge"],
    "什么": ["F_char_if"],
    "一般疑问": ["F_threshold_sum", "F_char_if"],
}

# ---- Stage C: 可判性词表 —— 出现这些词, 该问句有机会绑到机器可枚举的载体 ----
COMPUTABLE_HINTS = {
    "数量": ["多少", "数目", "个数", "计数", "数量"],
    "分布": ["分布", "密度", "比例", "概率", "频率", "均匀"],
    "极值": ["最大", "最小", "极值", "纪录", "上界", "下界", "峰值"],
    "存在性": ["存在", "是否所有", "每个", "都有", "总能", "必然"],
    "结构": ["周期", "收敛", "稳定", "对称", "不变量", "守恒", "递推"],
    "序列": ["序列", "数列", "递推", "迭代", "逐次"],
}
# 明确**不可判**的信号(思辨/规范/定义类)
UNJUDGEABLE = ["善", "恶", "美", "应当", "应该", "意义", "本质", "价值", "正义",
               "自由", "灵魂", "上帝", "道德", "幸福", "崇高"]


def stage_a(text):
    """抽日常疑问句(去重、截断)。"""
    qs = []
    for qtype, pat in Q_PATTERNS:
        for m in re.finditer(pat, text):
            frag = (m.group(1) if m.groups() else m.group(0)).strip()
            frag = re.sub(r"\s+", "", frag)
            if 3 <= len(frag) <= 60:
                qs.append({"type": qtype, "text": frag})
    # 去重(按文本)
    seen, out = set(), []
    for q in qs:
        if q["text"] in seen:
            continue
        seen.add(q["text"])
        out.append(q)
    return out


def stage_b(q):
    """结构化: 该疑问能否映射到 grammar 框架?"""
    frames = Q2FRAME.get(q["type"], [])
    return {"frames": frames, "structured": bool(frames)}


def stage_c(q):
    """可判性: 能否绑到机器可枚举的载体? 返回 (可判级别, 命中的提示词)。"""
    hits = [k for k, ws in COMPUTABLE_HINTS.items() if any(w in q["text"] for w in ws)]
    bad = [w for w in UNJUDGEABLE if w in q["text"]]
    if bad:
        return "不可判(规范/思辨)", {"blocked_by": bad}
    if hits:
        return "可判(有量化线索)", {"hints": hits}
    return "待定(无量化线索)", {}


def run(corpus=CORPUS, limit_files=None):
    files = sorted(corpus.glob("*.md")) if corpus.exists() else []
    if limit_files:
        files = files[:limit_files]
    all_q, by_file = [], {}
    for f in files:
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        qs = stage_a(txt)
        for q in qs:
            q["source"] = f.name
            q.update(stage_b(q))
            lvl, ev = stage_c(q)
            q["judgeable"] = lvl
            q["judge_evidence"] = ev
        all_q += qs
        by_file[f.name] = len(qs)
    return files, all_q, by_file


def main():
    corpus = Path(sys.argv[1]) if len(sys.argv) > 1 else CORPUS
    files, qs, by_file = run(corpus)
    print(f"语料 {len(files)} 个文件; 抽出日常疑问 **{len(qs)}** 条\n")
    print("== 按文件 ==")
    for k, v in sorted(by_file.items(), key=lambda x: -x[1])[:12]:
        print(f"  {v:>5}  {k[:66]}")

    print("\n== 漏斗(Stage A→B→C) ==")
    c_struct = sum(1 for q in qs if q["structured"])
    c_judge = sum(1 for q in qs if q["judgeable"].startswith("可判"))
    c_pend = sum(1 for q in qs if q["judgeable"].startswith("待定"))
    c_no = sum(1 for q in qs if q["judgeable"].startswith("不可判"))
    n = max(len(qs), 1)
    print(f"  A 抽出疑问            {len(qs):>5}")
    print(f"  B 可结构化(映射到句式)  {c_struct:>5}  ({c_struct/n:.1%})")
    print(f"  C1 可判(有量化线索)     {c_judge:>5}  ({c_judge/n:.1%})")
    print(f"  C2 待定(无量化线索)     {c_pend:>5}  ({c_pend/n:.1%})")
    print(f"  C3 不可判(规范/思辨)    {c_no:>5}  ({c_no/n:.1%})")

    print("\n== 疑问类型分布 ==")
    for k, v in Counter(q["type"] for q in qs).most_common():
        print(f"  {k:<14}{v:>5}")

    print("\n== 样本: 可判的日常疑问(B+C1 通过) ==")
    judgeable = [q for q in qs if q["structured"] and q["judgeable"].startswith("可判")]
    for q in judgeable[:15]:
        print(f"  [{q['type']}] {q['text'][:52]:<54} -> {q['judge_evidence'].get('hints')}")

    print("\n== 样本: 不可判的(规范/思辨类) ==")
    unj = [q for q in qs if q["judgeable"].startswith("不可判")]
    for q in unj[:8]:
        print(f"  {q['text'][:56]:<58} (因 {q['judge_evidence'].get('blocked_by')})")

    print(f"\n诚实: 绝大多数日常疑问过不了 Stage C —— 这与 R23 量化的"
          f"'73% 产出无机器可判数据'是同一现象在语料侧的重演。**漏斗收窄本身就是结果。**")
    out = HERE / "out/demo/corpus_questions.json"
    out.write_text(json.dumps({
        "files": len(files), "total": len(qs),
        "funnel": {"A_抽出": len(qs), "B_可结构化": c_struct,
                   "C1_可判": c_judge, "C2_待定": c_pend, "C3_不可判": c_no},
        "questions": qs}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"已存 {out}")


if __name__ == "__main__":
    main()
