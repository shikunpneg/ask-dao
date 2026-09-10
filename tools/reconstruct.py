# -*- coding: utf-8 -*-
"""tools/reconstruct.py — 拆后从底往上还原成段落（R85）

用户: "拆完之后还要从底往上还原啊, 成段落。"

过程: 拆到底(原子概念) -> 从底往上还原(叶子拼回父节点) -> 成段落。
还原 = 把叶子的本质"组装"回父节点的定义, 最终形成完整段落。
"""
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent

# 概念树(含本质)
TREE = {
    "记忆调性": {
        "essence": "记忆是否有调性——围绕中心组织",
        "sub": [
            {"term": "记忆", "essence": "过去影响现在",
             "sub": [
                 {"term": "过去", "essence": "已发生", "sub": [
                     {"term": "时间", "essence": "单向流逝"},
                     {"term": "事件", "essence": "已发生的事实"}]},
                 {"term": "影响", "essence": "改变", "sub": [
                     {"term": "因果", "essence": "前决定后"},
                     {"term": "塑造", "essence": "改造"}]},
                 {"term": "现在", "essence": "当下", "sub": [
                     {"term": "此刻", "essence": "正在"},
                     {"term": "进行中", "essence": "未完"}]},
             ]},
            {"term": "调性", "essence": "围绕主音组织",
             "sub": [
                 {"term": "主音", "essence": "中心", "sub": [
                     {"term": "引力点", "essence": "吸引其他音"}]},
                 {"term": "音级", "essence": "相对中心", "sub": [
                     {"term": "位置", "essence": "远近"}]},
                 {"term": "偏离", "essence": "离开中心", "sub": [
                     {"term": "张力", "essence": "不稳定"}]},
                 {"term": "回归", "essence": "回到中心", "sub": [
                     {"term": "解决", "essence": "张力释放"}]},
             ]},
        ],
    },
}


def reconstruct(node):
    """从底往上还原: 叶子 -> 父节点完整定义 -> 根节点段落。"""
    if not node.get("sub"):
        return node["essence"]
    # 先还原子节点
    child_phrases = [reconstruct(s) for s in node["sub"]]
    # 父节点定义 = 本质 + 每个子的完整描述
    return f"{node['essence']}({'；'.join(child_phrases)})"


def to_paragraph(node):
    """最终段落: 根的本质 + 逐步展开到全部。"""
    parts = [node["essence"]]
    for s in node["sub"]:
        parts.append(f"其中「{s['term']}」是{reconstruct(s)}")
    return "；".join(parts)


def main():
    print("=" * 100)
    print("拆后从底往上还原 —— 原子 -> 父 -> 段落")
    print("=" * 100)
    for name, root in TREE.items():
        print(f"\n『{name}』从底还原:\n")
        # 展示还原层次
        print("  最底层(叶子)定义:")
        for s in root["sub"]:
            for s2 in s["sub"]:
                for s3 in s2["sub"]:
                    print(f"    「{s3['term']}」= {s3['essence']}")
        print("\n  逐层还原:")
        for s in root["sub"]:
            print(f"    「{s['term']}」= {reconstruct(s)[:80]}")
        print("\n  最终段落:")
        print(f"    {to_paragraph(root)}")

    (HERE / "out/demo/reconstruct.json").write_text(
        json.dumps({name: to_paragraph(root) for name, root in TREE.items()},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n已存 out/demo/reconstruct.json")


if __name__ == "__main__":
    main()
