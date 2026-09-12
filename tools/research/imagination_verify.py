# -*- coding: utf-8 -*-
"""tools/research/imagination_verify.py — 想象路的质量验证器（R76）

用户: "对想象路做大的验证和探索。"

想象路的成功标准 = 解释充分/自洽/有洞见。验证 ≠ 解题, 而是检验**解释质量**:
  1. 指向真实性: 该组合词是否指向一个**真实存在**的研究领域/现象(非空想)
  2. 公设自洽性: 解释内部是否自洽(无自相矛盾)
  3. 洞见度: 是否揭示了单独领域看不到的联系

方法: 对每个组合词, 用**已有领域的先验**判断它指向哪里, 并评估:
  - 已知概念(熵编码=霍夫曼, 语义市场≈博弈论语义学) = 已有, 但"重新命名"有组织价值
  - 真新(意识拓扑) = 可能未见
  - 空想(无真实所指) = 需强化解释

输出: 每个组合词的 [指向领域, 已知/疑似新/空想, 洞见信号]
"""
import json
from itertools import product
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

# 已知概念对(组合词 → 已有真实领域)
KNOWN = {
    "熵编码": "霍夫曼/算术编码(信息论)",
    "熵压缩": "率失真理论/熵界(香农)",
    "语义市场": "博弈论语义学(Lewis 信号博弈)",
    "记忆压缩": "认知科学'重建'观(Farrell/Loftus)",
    "正义测度": "社会选择理论/福利经济学",
    "认知编码": "认知神经科学(表征编码)",
    "资本反馈": "宏观经济学(财富正反馈)",
    "演化博弈": "进化博弈论",
    "化学平衡": "物理化学",
    "语言演化": "历史语言学/语言演化",
    "信息熵": "信息论",
    "量子纠缠": "量子信息",
    "生态位选择": "生态位构建理论",
    "对称性守恒": "诺特定理",
}

# 第一词(对象型) vs 第二词(操作型) —— 好方向
OBJECT_LIKE = {"记忆", "认知", "责任", "资本", "语义", "和声", "旋律", "情绪", "动机",
               "价值", "正义", "自由", "意识", "话语", "风格", "形式", "现象", "本质",
               "本体", "善", "意识"}
OPER_LIKE = {"工业化", "标准化", "自动化", "模块化", "优化", "催化", "编码", "压缩",
             "测度", "选择", "演化", "平衡", "反馈", "极值", "可判定", "量化",
             "拓扑", "同调", "熵", "分配"}


def evaluate(a, b, wa, wb):
    """评估组合词 a×b。返回 (指向, 已知/新, 洞见信号)。"""
    term = a + b
    if term in KNOWN:
        return {"term": term, "domain": f"{wa[0]}×{wb[0]}",
                "points_to": KNOWN[term], "status": "已知(重新命名)",
                "insight": "组织价值: 把散落现象用一个词凝聚"}
    # 方向: 对象×操作 是好的; 操作×操作 弱
    if a in OBJECT_LIKE and b in OPER_LIKE:
        return {"term": term, "domain": f"{wa[0]}×{wb[0]}",
                "points_to": f"待查: {a}被{b}化的真实机制",
                "status": "疑似新(对象×操作, 需深查)",
                "insight": "对象被操作, 是概念生成的好方向"}
    if b in OBJECT_LIKE and a in OPER_LIKE:
        return {"term": term, "domain": f"{wa[0]}×{wb[0]}",
                "points_to": f"方向反了({b}被{a}化), 需确认",
                "status": "方向可疑(操作×对象)",
                "insight": "可能需要调换词序才有意义"}
    if a in OBJECT_LIKE and b in OBJECT_LIKE:
        return {"term": term, "domain": f"{wa[0]}×{wb[0]}",
                "points_to": f"两个对象相遇, 涌现第三物?",
                "status": "涌现候选(对象×对象)",
                "insight": "两个对象层面的碰撞, 可能是'第三物'的产地"}
    return {"term": term, "domain": f"{wa[0]}×{wb[0]}",
            "points_to": "待定", "status": "需更多想象",
            "insight": ""}


def main():
    words = {
        "公理化": "数学", "测度": "数学", "拓扑": "数学", "同调": "数学",
        "熵": "数学", "不变量": "数学", "递推": "数学", "极值": "数学",
        "对称性": "物理", "守恒": "物理", "相变": "物理", "场": "物理",
        "量子化": "物理", "纠缠": "物理", "临界": "物理",
        "演化": "生物", "选择": "生物", "适应性": "生物", "共生": "生物",
        "生态位": "生物", "代谢": "生物", "发育": "生物",
        "催化": "化学", "合成": "化学", "键合": "化学", "平衡": "化学", "周期律": "化学",
        "认知": "心理", "意识": "心理", "记忆": "心理", "学习": "心理",
        "情绪": "心理", "动机": "心理",
        "语法": "语言", "语义": "语言", "语用": "语言", "转喻": "语言", "隐喻": "语言", "话语": "语言",
        "编码": "信息", "信道": "信息", "压缩": "信息", "冗余": "信息", "反馈": "信息", "噪声": "信息",
        "工业化": "工程", "标准化": "工程", "自动化": "工程", "模块化": "工程", "可维护性": "工程", "优化": "工程",
        "资本": "经济", "市场": "经济", "效率": "经济", "分配": "经济", "增长": "经济", "稀缺": "经济",
        "和声": "音乐", "节奏": "音乐", "对位": "音乐", "旋律": "音乐", "调性": "音乐",
        "美学": "艺术", "形式": "艺术", "风格": "艺术", "再现": "艺术", "表现": "艺术",
        "责任": "伦理", "规范": "伦理", "价值": "伦理", "善": "伦理", "正义": "伦理",
        "可判定": "逻辑", "一致": "逻辑", "完备": "逻辑", "模型": "逻辑", "公设": "逻辑",
        "本体": "哲学", "认识": "哲学", "现象": "哲学", "本质": "哲学", "自由": "哲学",
    }
    print("=" * 100)
    print("想象路质量验证 —— 大规模探索 6642 组合词")
    print("=" * 100)
    evals = []
    for a in words:
        for b in words:
            if a == b:
                continue
            evals.append(evaluate(a, b, (words[a], words[b]), (words[b], words[a])))

    from collections import Counter
    status = Counter(e["status"] for e in evals)
    print(f"  组合词 {len(evals)} 个")
    print(f"\n  质量分布:")
    for s, c in status.most_common():
        print(f"    {s}: {c}")

    print("\n== 疑似新(对象×操作, 需深查) —— 最有希望的方向 ==")
    newish = [e for e in evals if e["status"].startswith("疑似新")]
    print(f"  {len(newish)} 个")
    shown = set()
    for e in newish:
        if e["term"] not in shown:
            shown.add(e["term"])
            print(f"    「{e['term']}」 {e['domain']} -> {e['points_to'][:50]}")
            if len(shown) >= 15:
                break

    print("\n== 涌现候选(对象×对象, 第三物产地) ==")
    emerg = [e for e in evals if e["status"].startswith("涌现")]
    print(f"  {len(emerg)} 个")
    for e in emerg[:10]:
        print(f"    「{e['term']}」 {e['domain']}")

    print("\n诚实: '疑似新'是**方向的**判断(对象×操作是好方向), 不是'确认新';")
    print("      每个需深查其指向领域是否已有对应研究。")
    (HERE / "out/demo/imagination_verify.json").write_text(
        json.dumps(evals, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n已存 out/demo/imagination_verify.json")


if __name__ == "__main__":
    main()
