# -*- coding: utf-8 -*-
"""tools/research/depth_batch.py — 批量深度造句: 10概念建树 + 自动d=自然深度（R84）

实验3: 10 个概念建概念树, d 自动=自然深度, 生成完整段落。
"""
import json, re
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent

# 10 个概念树(简化: 每个拆 2 层)
TREES = {
    "意识拓扑": {
        "essence": "意识是否有拓扑不变的性质",
        "sub": [
            {"term": "意识", "essence": "从内部体验的视角",
             "sub": [{"term": "体验", "essence": "主观经历",
                      "sub": [{"term": "质", "essence": "体验是什么感觉"}]},
                     {"term": "视角", "essence": "从哪看",
                      "sub": [{"term": "同一性", "essence": "是同一个视角"}]}]},
            {"term": "拓扑", "essence": "形变下不变",
             "sub": [{"term": "不变量", "essence": "不变的量",
                      "sub": [{"term": "洞", "essence": "连通性"}]},
                     {"term": "连续", "essence": "不撕裂",
                      "sub": [{"term": "拉伸", "essence": "变形"}]}]},
        ],
    },
    "语义市场": {
        "essence": "语义通过交换涌现为均衡",
        "sub": [
            {"term": "语义", "essence": "符号与所指",
             "sub": [{"term": "符号", "essence": "能指",
                      "sub": [{"term": "词", "essence": "语言单元"}]},
                     {"term": "所指", "essence": "指称对象",
                      "sub": [{"term": "意义", "essence": "内容"}]}]},
            {"term": "市场", "essence": "交换结构",
             "sub": [{"term": "供需", "essence": "需求与供给",
                      "sub": [{"term": "需求", "essence": "使用需要"}]},
                     {"term": "均衡", "essence": "稳定状态",
                      "sub": [{"term": "价格", "essence": "达成的条件"}]}]},
        ],
    },
    "责任催化": {
        "essence": "某些责任催化其他责任涌现",
        "sub": [
            {"term": "责任", "essence": "行动者对后果的归属",
             "sub": [{"term": "行动者", "essence": "行动的主体",
                      "sub": [{"term": "主体", "essence": "谁"}]},
                     {"term": "后果", "essence": "结果",
                      "sub": [{"term": "归属", "essence": "算谁的"}]}]},
            {"term": "催化", "essence": "自身不变加速他者",
             "sub": [{"term": "催化剂", "essence": "不消耗的加速者",
                      "sub": [{"term": "加速", "essence": "更快"}]},
                     {"term": "涌现", "essence": "新结构出现",
                      "sub": [{"term": "新责任", "essence": "催生出的"}]}]},
        ],
    },
    "记忆压缩": {
        "essence": "记忆是有损压缩, 回忆是重建",
        "sub": [
            {"term": "记忆", "essence": "过去影响现在",
             "sub": [{"term": "存储", "essence": "保存",
                      "sub": [{"term": "表示", "essence": "形式"}]},
                     {"term": "提取", "essence": "取回",
                      "sub": [{"term": "回忆", "essence": "重建"}]}]},
            {"term": "压缩", "essence": "用更少表示",
             "sub": [{"term": "有损", "essence": "丢细节",
                      "sub": [{"term": "失真", "essence": "偏离原物"}]},
                     {"term": "重建", "essence": "由表示还原",
                      "sub": [{"term": "噪声", "essence": "误差"}]}]},
        ],
    },
    "正义测度": {
        "essence": "正义能否压缩成可比较的数",
        "sub": [
            {"term": "正义", "essence": "分配与对待的公正",
             "sub": [{"term": "分配", "essence": "分给各方",
                      "sub": [{"term": "方案", "essence": "怎么分"}]},
                     {"term": "对待", "essence": "如何处置",
                      "sub": [{"term": "公平", "essence": "一样对待"}]}]},
            {"term": "测度", "essence": "压缩成数",
             "sub": [{"term": "可比", "essence": "能比较",
                      "sub": [{"term": "排序", "essence": "先后"}]},
                     {"term": "公理", "essence": "测度的规则",
                      "sub": [{"term": "Arrow", "essence": "不可比边界"}]}]},
        ],
    },
    "自由极值": {
        "essence": "自由是在约束下的最大化",
        "sub": [
            {"term": "自由", "essence": "不受外在决定",
             "sub": [{"term": "自主", "essence": "自己决定",
                      "sub": [{"term": "选择", "essence": "能做"}]},
                     {"term": "约束", "essence": "限制",
                      "sub": [{"term": "法律", "essence": "外在规则"}]}]},
            {"term": "极值", "essence": "约束下的最值",
             "sub": [{"term": "最大", "essence": "最多",
                      "sub": [{"term": "上限", "essence": "不能超过"}]},
                     {"term": "最优", "essence": "最好",
                      "sub": [{"term": "权衡", "essence": "取舍"}]}]},
        ],
    },
    "演化责任": {
        "essence": "责任随社会演化改变形态",
        "sub": [
            {"term": "演化", "essence": "微小变化累积成结构",
             "sub": [{"term": "选择压力", "essence": "环境筛选",
                      "sub": [{"term": "适应", "essence": "匹配"}]},
                     {"term": "分化", "essence": "变得不同",
                      "sub": [{"term": "新形态", "essence": "新样子"}]}]},
            {"term": "责任", "essence": "行动者对后果的归属",
             "sub": [{"term": "集体", "essence": "大家担",
                      "sub": [{"term": "氏族", "essence": "血缘"}]},
                     {"term": "个体", "essence": "个人担",
                      "sub": [{"term": "权利", "essence": "个体化"}]}]},
        ],
    },
    "情绪平衡": {
        "essence": "情绪趋向稳态平衡",
        "sub": [
            {"term": "情绪", "essence": "对情境的全身反应",
             "sub": [{"term": "正性", "essence": "积极的",
                      "sub": [{"term": "愉悦", "essence": "好感受"}]},
                     {"term": "负性", "essence": "消极的",
                      "sub": [{"term": "焦虑", "essence": "不安"}]}]},
            {"term": "平衡", "essence": "各方相抵而静止",
             "sub": [{"term": "稳态", "essence": "稳定状态",
                      "sub": [{"term": "恢复", "essence": "回到基线"}]},
                     {"term": "失衡", "essence": "打破",
                      "sub": [{"term": "创伤", "essence": "打破源"}]}]},
        ],
    },
    "资本反馈": {
        "essence": "资本通过正反馈自我强化",
        "sub": [
            {"term": "资本", "essence": "能产生更多价值的存量",
             "sub": [{"term": "收益", "essence": "产出",
                      "sub": [{"term": "积累", "essence": "攒下"}]},
                     {"term": "存量", "essence": "已有",
                      "sub": [{"term": "复利", "essence": "利滚利"}]}]},
            {"term": "反馈", "essence": "输出影响输入",
             "sub": [{"term": "正反馈", "essence": "放大",
                      "sub": [{"term": "富者愈富", "essence": "强者更强"}]},
                     {"term": "负反馈", "essence": "抵消",
                      "sub": [{"term": "税收", "essence": "稀释"}]}]},
        ],
    },
}


def tree_depth(node):
    if not node.get("sub"):
        return 0
    return 1 + max(tree_depth(s) for s in node["sub"])


def to_para(node, depth):
    if depth <= 0:
        return node["essence"]
    parts = [node["essence"]]
    for s in node.get("sub", [])[:3]:
        parts.append(f"其中「{s['term']}」{to_para(s, depth-1)}")
    return "；".join(parts)


def main():
    print("=" * 100)
    print("批量深度造句实验 —— 10 概念, d=自然深度")
    print("=" * 100)
    out = {}
    for name, root in TREES.items():
        d = tree_depth(root)
        para = to_para(root, d)
        out[name] = {"depth": d, "para": para}
        print(f"\n「{name}」 (自然深度 {d})")
        print(f"  {para[:110]}")
    (HERE / "out/demo/depth_batch.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n已存 out/demo/depth_batch.json ({len(out)} 个)")


if __name__ == "__main__":
    main()
