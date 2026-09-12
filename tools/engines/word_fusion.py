# -*- coding: utf-8 -*-
"""tools/engines/word_fusion.py — 穷尽关键词组合：先造词，再解释，再联想（R70）

用户: "组合是必要的，要穷尽所有关键词的组合，比如'文学'和一切领域的专业词汇。
我们要先造词，再解释，再联想。"

三步:
  1. **造词**: 领域A × 领域B 的全部组合(如 文学×工业 = "文学工业化")
  2. **解释**: 给组合词一个**候选定义**(它可能指什么)——基于 A 的对象 × B 的操作
  3. **联想**: 它指向什么**可判问题**(接判定路由)

重点: 不是日常已用词(如"人工智能"已存在), 而是**未见于日常的组合词** ——
这些"新造词"如果解释合理、指向可判问题, 就是"前所未有的概念"候选。
"""
import json
import sys
from itertools import product
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent.parent

# 领域专业词表(每个 = 领域 + 它带来的"对象/操作")
WORDS = {
    # 领域: 词汇
    "数学": ["公理化", "测度", "拓扑", "同调", "熵", "不变量", "递推", "极值"],
    "物理": ["对称性", "守恒", "相变", "场", "量子化", "纠缠", "临界"],
    "生物": ["演化", "选择", "适应性", "共生", "生态位", "代谢", "发育"],
    "化学": ["催化", "合成", "键合", "平衡", "周期律"],
    "心理": ["认知", "意识", "记忆", "学习", "情绪", "动机"],
    "语言": ["语法", "语义", "语用", "转喻", "隐喻", "话语"],
    "信息": ["编码", "信道", "压缩", "冗余", "反馈", "噪声"],
    "工程": ["工业化", "标准化", "自动化", "模块化", "可维护性", "优化"],
    "经济": ["资本", "市场", "效率", "分配", "增长", "稀缺"],
    "音乐": ["和声", "节奏", "对位", "旋律", "调性"],
    "艺术": ["美学", "形式", "风格", "再现", "表现"],
    "伦理": ["责任", "规范", "价值", "善", "正义"],
    "逻辑": ["可判定", "一致", "完备", "模型", "公设"],
    "哲学": ["本体", "认识", "现象", "本质", "自由"],
}

# 已存在的日常词(不当作新造词)
EXISTING = {"工业化", "自动化", "标准化", "模块化", "认知", "演化", "相变",
            "不变量", "公理化", "可判定", "完备", "一致", "对称性", "守恒",
            "生态位", "催化", "键合", "隐喻", "语义", "编码", "信道",
            "反馈", "美学", "形式", "责任", "规范", "意识"}


def interpret(a_word, b_word):
    """给组合词 a×b 一个候选定义(基于 a 的对象 × b 的操作)。"""
    return f"{a_word} 作为 {b_word} 处理的对象/操作"


def link(a_domain, b_domain, a_word, b_word):
    """联想: 这个组合词指向什么可判问题。"""
    # 规则: A的对象在B的操作下, 会呈现什么A单独看不到的性质
    return f"在{b_domain}的「{b_word}」操作下, {a_domain}的「{a_word}」对象会呈现什么"
    + f" {a_domain}单独问不出的性质?"


def main():
    # 领域分组
    domains = sorted(WORDS)
    pairs = list(product(domains, repeat=2))
    print("=" * 100)
    print("穷尽关键词组合 —— 先造词，再解释，再联想")
    print("=" * 100)
    print(f"  领域: {len(domains)} 个")
    print(f"  有序组合(领域×领域): {len(pairs)}")
    total_words = sum(len(v) for v in WORDS.values())
    print(f"  专业词: {total_words} 个")
    print(f"  词级组合: {total_words} × {total_words} = {total_words**2}")

    new_terms = []
    for a_dom, b_dom in pairs:
        for a_word in WORDS[a_dom]:
            for b_word in WORDS[b_dom]:
                term = f"{a_word}{b_word}"
                if term in EXISTING:
                    continue
                # 跳过已知复合词(粗略): 含明显不搭的
                if a_word == b_word:
                    continue
                # 评分: 陌生度(不常见组合) + 可解释度
                new_terms.append({
                    "term": term, "domains": f"{a_dom}×{b_dom}",
                    "words": f"{a_word}×{b_word}",
                    "interpret": interpret(a_word, b_word),
                    "link": link(a_dom, b_dom, a_word, b_word),
                    "judge_route": f"{b_dom}方法",
                })

    print(f"\n  造出未见于日常的新组合词: {len(new_terms)}")
    print(f"\n  == 样本(按领域) ==")
    from collections import Counter
    byd = Counter(t["domains"] for t in new_terms)
    for d, c in byd.most_common(10):
        print(f"    {d}: {c} 个")
    print(f"\n  == 精选(不常见组合 + 可解释) ==")
    # 挑几个有代表性的
    picks = []
    seen_pairs = set()
    for t in new_terms:
        if t["domains"] not in seen_pairs and len(picks) < 12:
            seen_pairs.add(t["domains"])
            picks.append(t)
    for t in picks:
        print(f"\n  ▸ 「{t['term']}」  ({t['domains']})")
        print(f"    解释: {t['interpret']}")
        print(f"    联想: {t['link'][:70]}")

    (HERE / "out/demo/word_fusion.json").write_text(
        json.dumps(new_terms, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n已存 out/demo/word_fusion.json ({len(new_terms)} 个新组合词)")


if __name__ == "__main__":
    main()
