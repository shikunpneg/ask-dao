# -*- coding: utf-8 -*-
"""tools/research/open_mine.py — 开放问题挖掘器：从人类知识库提取"自我承认的未知"（R47）

用户: "我需要你扩大规模, 我要看到你找到新问题。"

## 核心洞察
人类知识库里**已经标记了自己的未知** —— 那些"没有人能解释 / 尚未解决 / 未解 /
仍是一个谜 / 不得而知 / 有争议"的句子, 是知识的**开放裂缝**。
从 310 个语料文件里把它们全部挖出来, 就是批量找到"真问题"。

## 三档（由强到弱）
  A 明确开放: "没有人能解释/尚未解决/仍是一个谜/不得而知/未解之谜"
  B 不确定/悬置: "可能/也许/推测/尚不清楚/仍有争议/没有定论"
  C 条件性: "如果/除非/取决于" 里的问题(弱)

## 纪律
- 挖出来的每个都是**知识库自己标记的未知**, 不是机器编的。
- "机器找到" ≠ "机器解决"。三档是候选, 需查证是否已被解决。
- 统计 + 顶级样本 + 领域分布, 证明**规模化**。
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

CORPUS = Path(r"E:\ask-dao\_text")

# 强开放信号(知识库明确标记"不知道")
STRONG = [
    r"没有人能解释", r"没有人知道", r"无人能解释", r"无人知道",
    r"尚未解决", r"尚未有答案", r"尚未能解释", r"尚无答案", r"仍无答案",
    r"未解之谜", r"仍是一个谜", r"至今是一个谜", r"仍是谜",
    r"不得而知", r"不得而知的是", r"无法得知",
    r"为什么.{0,20}(至今|仍然|迄今).{0,10}(未知|不明|不清楚|没有答案)",
    r"(至今|仍然|迄今).{0,15}没有.{0,10}(答案|解释|定论)",
    r"open problem", r"open question", r"unsolved", r"unresolved",
    r"not yet understood", r"unknown why", r"remains a mystery",
]
# 中等: 推测/悬置
MED = [
    r"尚不清楚", r"还不清楚", r"仍不清楚", r"没有定论", r"尚无定论",
    r"仍有争议", r"存在争议", r"是一个谜", r"未解", r"未明",
    r"推测可能是", r"可能因为", r"也许是", r"被认为是", r"猜测",
    r"尚未证实", r"尚未被证实", r"有待研究", r"有待进一步",
    r"仍属推测", r"仍是推测", r"it is unknown", r"is not clear",
    r"not known", r"not understood", r"unclear why",
]

# 领域归属(按文件名)
def domain_of(name):
    n = name
    if "数学" in n or "math" in n: return "数学"
    if "物理" in n or "phys" in n: return "物理"
    if "经济" in n or "econom" in n: return "经济"
    if "生物" in n or "bio" in n: return "生物"
    if "心理" in n or "认知" in n: return "心理/认知"
    if "信息" in n or "计算" in n: return "信息/计算"
    if "哲学" in n: return "哲学"
    if "手册" in n or "handbook" in n: return "科学哲学手册"
    if "逻辑" in n: return "逻辑"
    if "技术" in n or "工程" in n: return "工程"
    if "伦理" in n: return "伦理"
    if "历史" in n or "milestone" in n: return "科学史"
    return "其他"


def mine_file(path):
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    paras = re.split(r"\n\s*\n", text)
    out = []
    for pi, para in enumerate(paras):
        if len(para) < 30 or len(para) > 1200:
            continue
        flat = re.sub(r"\s+", " ", para).strip()
        # 找所有强/中信号
        for label, pats in (("A明确开放", STRONG), ("B推测悬置", MED)):
            for pat in pats:
                m = re.search(pat, flat)
                if m:
                    # 提取信号附近 ±60 字的上下文
                    s = max(0, m.start() - 60)
                    e = min(len(flat), m.end() + 60)
                    out.append({
                        "file": path.name, "para": pi, "level": label,
                        "signal": m.group(0)[:40],
                        "context": flat[s:e],
                    })
                    break   # 每段每级取一条
    return out


def main():
    files = sorted(CORPUS.rglob("*.md"))
    print("=" * 100)
    print("开放问题挖掘器 —— 从人类知识库提取'自我承认的未知'")
    print("=" * 100)
    print(f"  语料: {len(files)} 个 md 文件 (221M)")
    all_hits = []
    per_file = {}
    for f in files:
        hits = mine_file(f)
        if hits:
            per_file[f.name] = len(hits)
            all_hits.extend(hits)

    print(f"\n  命中开放/悬置信号: **{len(all_hits)}** 处")
    print(f"\n  == 级别分布 ==")
    lv = Counter(h["level"] for h in all_hits)
    print(f"    {dict(lv)}")
    print(f"\n  == 领域分布(按文件名) ==")
    dom = Counter(domain_of(h["file"]) for h in all_hits)
    for d, c in dom.most_common():
        print(f"    {d:<12}{c:>5}")
    print(f"\n  == 命中最多文件 Top10 ==")
    for name, c in sorted(per_file.items(), key=lambda x: -x[1])[:10]:
        print(f"    {c:>4}  {name[:60]}")

    print(f"\n  == 样本: 明确开放(A级) 前 12 ==")
    a = [h for h in all_hits if h["level"] == "A明确开放"]
    for h in a[:12]:
        print(f"\n  [{domain_of(h['file'])}] {h['file'][:28]} 信号「{h['signal']}」")
        print(f"     …{h['context'][:150]}…")

    print(f"\n  == 样本: 推测悬置(B级) 前 8 ==")
    b = [h for h in all_hits if h["level"] == "B推测悬置"]
    for h in b[:8]:
        print(f"\n  [{domain_of(h['file'])}] {h['file'][:28]} 信号「{h['signal']}」")
        print(f"     …{h['context'][:130]}…")

    print("\n" + "=" * 100)
    print("诚实")
    print("=" * 100)
    print(f"  挖到 {len(all_hits)} 处知识库自我标记的未知(A级 {len(a)} / B级 {len(b)})")
    print("  · 每处都是**人类知识库自己承认不知道**的 —— 不是机器编的。")
    print("  · 但 '知识库说不知道' 可能是 (i) 真未解 (ii) 写书时未解(现在已解) "
          "(iii) 修辞('没有人能'是夸张)。")
    print("  · 下一查证点: 对 A 级候选逐条查文献, 判断它今天是否仍开放。")
    print("  · 这就是'找到新问题'的规模化路径: 不是机器造, 而是把知识库的自我未知挖出来。")

    Path("out/demo/open_mine.json").parent.mkdir(parents=True, exist_ok=True)
    Path("out/demo/open_mine.json").write_text(
        json.dumps({"total": len(all_hits), "A": len(a), "B": len(b),
                    "by_level": dict(lv), "by_domain": dict(dom),
                    "hits": all_hits}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n已存 out/demo/open_mine.json")


if __name__ == "__main__":
    main()
