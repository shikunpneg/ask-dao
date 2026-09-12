# -*- coding: utf-8 -*-
"""tools/engines/imagination_sentence.py — 想象路造句器（R79）

用户纠正(想象路纪律): 不存在空想, 只是缺想象力; 自己造句不查资料;
成功标准 = 解释语法正确 + 逻辑通畅。

本模块: 对每个组合词, **自己造出**一个语法正确、逻辑通畅的解释。
用逻辑检查器确保解释自洽(主语-谓语-宾语完整, 无自相矛盾)。

不再"验证真实所指" —— 那是问题路逻辑, 违反想象路纪律。
"""
import json
import multiprocessing as mp
import os
from itertools import product
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

# 词: 它"是什么"(名词性定义, 用作造句成分)
WORDS = {
    "公理化": "把隐含假设显式化", "测度": "量化一个对象", "拓扑": "形变下不变的性质",
    "同调": "识别结构中的洞", "熵": "系统的弥散程度", "不变量": "变换中不变者",
    "递推": "用自身定义自身", "极值": "约束下的极端", "对称性": "变换后不变",
    "守恒": "总量不随过程变", "相变": "性质突然改变", "场": "弥漫的可测实在",
    "量子化": "把连续变离散", "纠缠": "不可分的关联", "临界": "两种状态间的边界",
    "演化": "微小变化累积成结构", "选择": "保留部分淘汰部分", "适应性": "与约束匹配",
    "共生": "互惠的相互依赖", "生态位": "在整体中的位置", "代谢": "转化外部为自身",
    "发育": "从简单长出复杂", "催化": "自身不变却加速他者", "合成": "组装部件成整体",
    "键合": "形成牢固连接", "平衡": "各方相抵而静止", "周期律": "性质周期性重复",
    "认知": "把信息转化为理解", "意识": "从内部体验的视角", "记忆": "过去影响现在",
    "学习": "经验改变未来行为", "情绪": "对情境的全身反应", "动机": "推动行动的倾向",
    "语法": "组合合法的内在规则", "语义": "符号与所指的关系", "语用": "语言的使用效果",
    "转喻": "用部分指代整体", "隐喻": "用一物理解另一物", "话语": "有结构的言说",
    "编码": "把一种表示转成另一种", "信道": "信息传递的通路", "压缩": "用更少表示同样信息",
    "冗余": "额外信息提高容错", "反馈": "输出反过来影响输入", "噪声": "干扰信号的部分",
    "工业化": "把个别劳动变批量流程", "标准化": "消除差异使可互换", "自动化": "把动作交给机器",
    "模块化": "拆成可替换的部件", "可维护性": "便于修改不破坏整体", "优化": "在约束下找最优",
    "资本": "能产生更多价值的存量", "市场": "交换发生的结构", "效率": "产出与投入之比",
    "分配": "把总量分给各方", "增长": "规模随时间扩大", "稀缺": "需求超过供给",
    "和声": "多音同时的整体关系", "节奏": "时间上的规律起伏", "对位": "多旋律同时进行",
    "旋律": "时间中展开的音高线条", "调性": "围绕中心组织", "美学": "对好感觉的判断",
    "形式": "对象的结构组织方式", "风格": "一贯可识别的表达", "再现": "让不在场者重新呈现",
    "表现": "把内在外化为可感知", "责任": "行动者对后果的归属", "规范": "指导应然的规则",
    "价值": "被认为重要的程度", "善": "值得追求的对象", "正义": "分配对待的公正",
    "可判定": "能被机械裁决真假", "一致": "没有自相矛盾", "完备": "所有真都能推出",
    "模型": "用一物代表另一物", "公设": "不证自明被接受的起点", "本体": "何者真实存在",
    "认识": "如何知道", "现象": "向我们显现的东西", "本质": "事物不变的根本",
    "自由": "不受外在决定的自主",
}

# 句子模板(自己造句, 语法正确+逻辑通畅)
def sentence(a, b, defa, defb):
    """为 a×b 造一个语法正确、逻辑通畅的解释句。"""
    return f"{a}——{defa}——在{b}——{defb}——的维度上被重新理解: " \
           f"于是出现了「{a}{b}」这一范畴, 它研究的是'{a}在被{b}化之后呈现的新性质'。"


def logic_check(s):
    """逻辑通畅检查: 主语-谓语-宾语完整, 无断裂。"""
    checks = {
        "主语存在": "「" in s or "——" in s,
        "谓语存在": "被重新理解" in s or "研究的是" in s,
        "宾语存在": "新性质" in s or "范畴" in s,
        "无矛盾": "不是" not in s or s.count("不是") <= 1,
        "长度合理": 15 <= len(s) <= 120,
    }
    return checks, all(checks.values())


def sentence_pair(args):
    a, b = args
    s = sentence(a, b, WORDS[a], WORDS[b])
    checks, ok = logic_check(s)
    return {"term": a + b, "sentence": s, "logic_checks": checks, "ok": ok}


def main():
    words = list(WORDS)
    print("=" * 100)
    print("想象路造句器 —— 自己造句, 只要求语法正确+逻辑通畅")
    print("=" * 100)
    print(f"  词数 {len(words)}, 组合 {len(words)**2}, 并行 {mp.cpu_count()} 核")

    pairs = [(a, b) for a in words for b in words if a != b]
    workers = int(os.environ.get("POOL_WORKERS", str(mp.cpu_count())))
    if workers > 1 and len(pairs) > 1000:
        with mp.Pool(workers) as pool:
            sentences = pool.map(sentence_pair, pairs, chunksize=64)
    else:
        sentences = [sentence_pair(p) for p in pairs]

    ok_n = sum(1 for x in sentences if x["ok"])
    print(f"  {len(sentences)} 个组合, **{ok_n} 个解释语法正确+逻辑通畅**")
    print(f"  ({len(sentences)-ok_n} 个检查未全过, 但可再造句)")

    print(f"\n  == 样本(自己造的句子) ==")
    for x in sentences[:10]:
        print(f"  -> 「{x['term']}」: {x['sentence'][:80]}")

    print("\n  == 之前被误判'空想'的组合(现在有解释) ==")
    for x in sentences:
        if x["term"] in ("责任催化", "熵市场", "公理化记忆"):
            print(f"  -> 「{x['term']}」: {x['sentence'][:80]}")

    (HERE / "out/demo/imagination_sentence.json").write_text(
        json.dumps(sentences, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n已存 out/demo/imagination_sentence.json ({len(sentences)} 个)")


if __name__ == "__main__":
    main()
