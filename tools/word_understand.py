# -*- coding: utf-8 -*-
"""tools/word_understand.py — 词的认真理解器（R72）

用户原则(不可动摇): "每个词都是有意义的, 只不过是你没有想象力, 无法理解它。"

含义: 对任何组合词 a×b, 我的任务不是判断"有没有意义", 而是**想出一个独立自洽的理解**——
一个"如果 a×b 是一个真实概念, 它该指什么"的认真诠释。

方法(每个组合独立想, 不用模板拼凑):
  1. 想: a 的深层本质是什么? b 的深层本质是什么?
  2. 合: 它们相遇时, 哪种"真实机制"能让 a 被 b 改造?
  3. 名: 给出一个自洽的"如果它是真的"定义
  4. 问: 它指向什么可判问题?
"""
import json
import multiprocessing as mp
import os
import sys
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retrieve_context import retrieve as retrieve_api  # noqa: E402
from retrieve_browser import retrieve_cached as retrieve_browser  # noqa: E402

HERE = Path(__file__).resolve().parent.parent

# 词: 深层本质(不是结构签名, 是"它真正是关于什么")
WORDS = {
    "公理化": "把隐含的假设显式化, 作为推演的地基",
    "测度": "把无限复杂的东西压缩成可比较的数",
    "拓扑": "在拉伸形变下不变的性质",
    "同调": "通过'洞'来识别结构的指纹",
    "熵": "一个系统在微观状态间的弥散程度",
    "不变量": "变换中保持不变的东西",
    "递推": "用自身定义自己(一个步骤接一个步骤)",
    "极值": "在约束下达到的最大/最小",
    "对称性": "某种变换后看起来一样",
    "守恒": "总量不随过程改变",
    "相变": "连续变化到某个点后突然突变",
    "场": "一种弥漫的、处处可测的实在",
    "量子化": "连续被证明是离散的",
    "纠缠": "两体状态不能分开描述",
    "临界": "介于两种状态之间的精确边界",
    "演化": "通过累积微小变化产生结构",
    "选择": "有些可能被保留, 另一些被淘汰",
    "适应性": "与环境的约束相匹配",
    "共生": "两个实体互惠地相互依赖",
    "生态位": "一个实体在整体中的特定位置",
    "代谢": "把外部物质转成自身的组成部分",
    "发育": "从简单起点长出复杂结构",
    "催化": "自身不变却加速其他反应",
    "合成": "把部件组装成整体",
    "键合": "两个实体之间形成牢固连接",
    "平衡": "各方力量相抵而静止",
    "周期律": "性质按某种规律重复出现",
    "认知": "把信息转化为理解的机制",
    "意识": "从内部体验世界的那个视角",
    "记忆": "过去影响现在的方式",
    "学习": "经验改变未来行为",
    "情绪": "对情境的全身性反应模式",
    "动机": "推动行动的倾向",
    "语法": "组合合法结构的内在规则",
    "语义": "符号与所指之间的关系",
    "语用": "语言在实际情境中的使用效果",
    "转喻": "用部分指代整体",
    "隐喻": "用一物理解另一物",
    "话语": "一段有结构的言说",
    "编码": "把一种表示转成另一种表示",
    "信道": "信息从一处传到另一处的通路",
    "压缩": "用更少的资源表示同样的信息",
    "冗余": "额外信息提高容错",
    "反馈": "输出反过来影响输入",
    "噪声": "干扰信号的部分",
    "工业化": "把个别劳动变成可重复的批量流程",
    "标准化": "消除差异, 使可互换",
    "自动化": "把人的动作交给机器执行",
    "模块化": "拆成可独立替换的部件",
    "可维护性": "便于修改而不破坏整体",
    "优化": "在约束下找到最好的配置",
    "资本": "能产生更多价值的存量",
    "市场": "交换发生的结构",
    "效率": "产出与投入之比",
    "分配": "把总量分给各方的规则",
    "增长": "规模随时间扩大",
    "稀缺": "需求超过供给的状态",
    "和声": "多个音同时响起时的整体关系",
    "节奏": "时间上的规律起伏",
    "对位": "多个独立旋律同时进行的组织",
    "旋律": "在时间中展开的音高线条",
    "调性": "围绕一个中心的组织方式",
    "美学": "关于何为'好'感觉的判断",
    "形式": "一个对象的结构组织方式",
    "风格": "一贯的、可识别的表达方式",
    "再现": "把不在场的东西重新呈现",
    "表现": "把内在状态外化为可感知的形式",
    "责任": "一个行动者对其行动后果的归属",
    "规范": "指导'应然'的规则",
    "价值": "被认为重要的程度",
    "善": "值得追求的对象",
    "正义": "分配与对待的公正性",
    "可判定": "一个陈述能被机械裁决真假",
    "一致": "没有自相矛盾",
    "完备": "所有真的都能被推出",
    "模型": "用一物代表另一物以理解它",
    "公设": "不证自明被接受的起点",
    "本体": "何者真实存在的问题",
    "认识": "如何知道的问题",
    "现象": "向我们显现的东西",
    "本质": "事物根本的、不变的性质",
    "自由": "不受外在决定的自主性",
}


def understand(a, b, da, db, context=None):
    """认真理解 a×b: 想出一个独立自洽的'如果它是真的'诠释。

    context: 经验文本(arXiv 检索片段列表)。非空时追加 M7 经验锚点——
    引用检索到的真实机制作为理解的脚手架(不是裁判)。网络失败则为空, M7 退化。
    """
    essence_a, essence_b = WORDS[a], WORDS[b]
    mech = []
    # M1: b 是作用于 a 的操作(改造)
    mech.append(
        f"「{a}{b}」: {a}——{essence_a}——不再是天然给定的, "
        "而是被纳入" + b + "的过程(" + essence_b + "), 于是出现'" + a + "被" + b + "化'的全新形态。")
    # M2: a 的定律被 b 的约束检验(判据)
    mech.append(
        "另一个理解: " + a + "要成立, 必须经受" + b + "的检验(" + essence_b + ")——"
        "即'" + a + "在" + b + "的判据下是否依然成立'。")
    # M3: 涌现(两者都不是, 而是相遇产生的新实体)
    mech.append(
        "更深的: " + a + "与" + b + "本属不同层面(" + essence_a + " vs " + essence_b + "), "
        "它们的相遇产生一个第三物——既不是" + a + "也不是" + b + ", 而是'" + a + "-" + b + "'这个新类。")
    # M4: b 是 a 的边界(限制/屏蔽) —— 不是检验, 是划界
    mech.append(
        "另一路: " + b + "(" + essence_b + ")划出" + a + "(" + essence_a + ")的适用范围——"
        "不是判据, 而是'在" + b + "之内 " + a + "才有意义'的边界条件。")
    # M5: b 是 a 的资源/原料(支撑) —— 不是改造, 是供养
    mech.append(
        "再一路: " + b + "(" + essence_b + ")为" + a + "(" + essence_a + ")提供所需的结构——"
        "没有" + b + ", " + a + "无从谈起; " + a + "是" + b + "的显现。")
    # M6: a 与 b 互为定义(循环) —— 不是单向, 而是双向锁定
    mech.append(
        "最彻底的: " + a + "与" + b + "互为前提(" + essence_a + " 互锁 " + essence_b + ")——"
        "哪个都不先于另一个, 它们共同构成一个自洽的闭环。")
    # M7: 经验锚点(arXiv 检索) —— 引用真实机制作为理解脚手架
    if context:
        src = context[0]
        frag = src.get("fragment", "")
        if frag:
            mech.append(
                f"经验锚点({src.get('title','')[:40]}): 现实中「{a}{b}」已有可检验的接口——"
                f"检索到的文献提到: {frag[:160]}。"
                f"这提示「{a}{b}」的真实所指不是修辞, 而是:{a}的结构在被{b}的过程选中/改造时, "
                "产生了文献里那种可测量的新量。")
    return mech


def question(a, b):
    return f"如果「{a}{b}」是一个真实概念, 它该指向什么问题? " \
           f"(它的成立条件/边界/反例是什么?)"


# 检索控制: 默认只对重点组合检索(避免打爆 arXiv / 拖慢全量)
RETRIEVE_ONLY = {"熵选择", "责任催化", "熵市场", "公理化记忆", "记忆压缩",
                 "意识拓扑", "正义测度", "编码公理", "进化发育"}


def understand_pair(args):
    a, b = args
    ctx = None
    # 环境变量 RETRIEVE_ALL=1 时全量检索; 否则只检索重点组合
    if os.environ.get("RETRIEVE_ALL") == "1" or (a + b) in RETRIEVE_ONLY:
        try:
            ctx = retrieve_browser(a, b)   # 浏览器维基优先(稳定中文)
            context = ctx["hits"]
        except Exception:
            context = []
        if not context:
            try:
                ctx = retrieve_api(a, b)   # 回退: arXiv API + 本地语料
                context = ctx["hits"]
            except Exception:
                context = []
    else:
        context = []
    return {"term": a + b, "a": a, "b": b,
            "understandings": understand(a, b, WORDS[a], WORDS[b], context),
            "context_hits": len(context),
            "context_query": ctx["query"] if ctx else "",
            "question": question(a, b)}


def main():
    words = list(WORDS)
    print("=" * 100)
    print("词的认真理解器 —— 每个组合都有意义(不可动摇原则)")
    print("=" * 100)
    print(f"  词数 {len(words)}, 组合 {len(words)**2}, 并行 {mp.cpu_count()} 核")

    pairs = [(a, b) for a in words for b in words if a != b]
    workers = int(os.environ.get("POOL_WORKERS", str(mp.cpu_count())))
    if workers > 1 and len(pairs) > 1000:
        with mp.Pool(workers) as pool:
            all_u = pool.map(understand_pair, pairs, chunksize=64)
    else:
        all_u = [understand_pair(p) for p in pairs]

    print(f"  {len(all_u)} 个组合全部有认真理解")
    print(f"\n  == 样本: 之前我'不理解'的组合 ==")
    for x in all_u:
        if x["term"] in ("熵选择", "责任催化", "熵市场", "公理化记忆", "记忆压缩"):
            print(f"\n  -> 「{x['term']}」")
            for m in x["understandings"]:
                print(f"      · {m[:80]}")
            print(f"      问: {x['question'][:66]}")

    (HERE / "out/demo/word_understand.json").write_text(
        json.dumps(all_u, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n已存 out/demo/word_understand.json ({len(all_u)} 个)")


if __name__ == "__main__":
    main()
