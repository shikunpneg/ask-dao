# -*- coding: utf-8 -*-
"""tools/research/depth_sentence.py — 可调深度造句器（R83）

用户: 拆分的深度设成一个变量 d。以"记忆调性"为例:
  记忆是"过去影响现在"的方式 -> 过去/影响/现在 都可再拆
  => 何时停 = 深度变量 d。

d=0: 只拆到实体(记忆+调性)
d=1: 再问"什么记忆/什么是调性"
d=2: 拆记忆的本质("过去影响现在") -> 过去/影响/现在 再拆
...
"""
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent

# 概念树: 每个节点 = {term, essence, sub:[子节点]}
TREE = {
    "记忆调性": {
        "essence": "记忆是否有调性——即围绕中心组织",
        "sub": [
            {"term": "记忆", "essence": "过去影响现在的方式",
             "sub": [
                 {"term": "过去", "essence": "已发生的时间/事件",
                  "sub": [{"term": "时间", "essence": "单向流逝"},
                          {"term": "事件", "essence": "已发生的事实"}]},
                 {"term": "影响", "essence": "改变/调制/塑造",
                  "sub": [{"term": "因果", "essence": "前一状态决定后一"},
                          {"term": "调制", "essence": "不复制而改造"}]},
                 {"term": "现在", "essence": "当下/正在进行",
                  "sub": [{"term": "当下", "essence": "此刻"},
                          {"term": "进行中", "essence": "未完的状态"}]},
             ]},
            {"term": "调性", "essence": "围绕一个主音组织其他音",
             "sub": [
                 {"term": "主音", "essence": "中心/引力点",
                  "sub": [{"term": "中心", "essence": "组织之源"}]},
                 {"term": "音级", "essence": "相对中心的关系",
                  "sub": [{"term": "关系", "essence": "距离/位置"}]},
                 {"term": "偏离", "essence": "离开中心",
                  "sub": [{"term": "张力", "essence": "离开的不稳定"}]},
                 {"term": "回归", "essence": "回到中心",
                  "sub": [{"term": "解决", "essence": "张力的释放"}]},
             ]},
        ],
    },
    "认知压缩": {
        "essence": "认知本质是压缩——用更少表示理解世界",
        "sub": [
            {"term": "认知", "essence": "把信息转化为理解",
             "sub": [
                 {"term": "知觉", "essence": "从感觉提取特征",
                  "sub": [{"term": "特征", "essence": "关键的差异"}]},
                 {"term": "记忆", "essence": "存储要点",
                  "sub": [{"term": "要点", "essence": "被选中的部分"}]},
             ]},
            {"term": "压缩", "essence": "用更少资源表示同样信息",
             "sub": [
                 {"term": "有损", "essence": "丢失部分细节",
                  "sub": [{"term": "丢失", "essence": "不可恢复"}]},
                 {"term": "特征提取", "essence": "保留关键、丢冗余",
                  "sub": [{"term": "关键", "essence": "决定性的"}]},
             ]},
        ],
    },
}


def render(node, depth, indent=0):
    """递归渲染节点树到指定深度。"""
    pad = "  " * indent
    lines = [f"{pad}「{node['term']}」: {node['essence']}"]
    if depth > 0 and node.get("sub"):
        for s in node["sub"]:
            lines.append(render(s, depth - 1, indent + 1))
    return "\n".join(lines)


def to_paragraph(node, depth):
    """按深度把树展开成段落理解。"""
    if depth <= 0:
        return node["essence"]
    parts = [node["essence"]]
    for s in node.get("sub", [])[:3]:
        parts.append(f"其中「{s['term']}」{to_paragraph(s, depth-1)}")
    return "；".join(parts)


def main():
    print("=" * 100)
    print("可调深度造句器 —— 拆分的深度是变量 d")
    print("=" * 100)
    for name, root in TREE.items():
        print(f"\n{'='*80}")
        print(f"## 「{name}」 (深度 d=0..3)")
        for d in (0, 1, 2, 3):
            print(f"\n  d={d}:")
            print(f"    {to_paragraph(root, d)}")
            # print(render(root, d))

    print("\n说明: d 是拆分深度变量。d=0 只一层, d=3 拆到'时间/事件/因果/调制'等底层。")
    print("     何时停 = 用户设 d; 也可设'深度=直到不再可拆或有意义地停'。")
    out = {}
    for name, root in TREE.items():
        out[name] = {"tree": root, "paragraphs": {
            str(d): to_paragraph(root, d) for d in (0, 1, 2, 3)}}
    (HERE / "out/demo/depth_sentence.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n已存 out/demo/depth_sentence.json")


if __name__ == "__main__":
    main()
