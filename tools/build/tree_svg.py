# -*- coding: utf-8 -*-
"""tools/tree_svg.py — 节点连线树（SVG）: 展示来龙去脉与生成全过程（R91）

用户: 树的可视化要像参考图那样有节点、连线, 展现生成全过程。

渲染:
  · 概念树: 概念 → 实体 → 子实体 → 原子概念 (拆词的来龙去脉)
  · 问题树: 根 → 问题 (出处链: 从哪长出, 走什么边)

风格: 宣纸底 + 墨线 (与 logo 一致), 或深色(可配)。
"""
import html
from typing import List


# ---------------- 通用: 紧凑树布局 ----------------
class _Node:
    __slots__ = ("label", "sub", "x", "y", "depth", "note", "children")

    def __init__(self, label, note="", children=None):
        self.label = label
        self.note = note
        self.children = children or []
        self.x = 0
        self.y = 0
        self.depth = 0


def _build(d):
    """概念树 dict -> _Node."""
    if not isinstance(d, dict):
        return _Node(str(d))
    label = d.get("term") or d.get("label") or (d.get("essence", "")[:10])
    note = d.get("essence", "") if d.get("term") else ""
    kids = [_build(s) for s in d.get("sub", [])]
    return _Node(label, note, kids)


def _layout(root):
    """分配坐标: 叶子按序 x, 父取子中; y = depth。返回 (max_depth, n_leaves)。"""
    counter = [0]

    def walk(n, depth):
        n.depth = depth
        if not n.children:
            n.x = counter[0]
            counter[0] += 1
        else:
            for c in n.children:
                walk(c, depth + 1)
            n.x = sum(c.x for c in n.children) / len(n.children)
        return depth

    def maxd(n):
        return max([maxd(c) for c in n.children] + [n.depth])

    walk(root, 0)
    return maxd(root), counter[0]


# ---------------- SVG 渲染 ----------------
INK = "#1a1512"
LINE = "#8a7455"
PAPER = "#f5efe1"
ACCENT = "#b02a24"
GOLD = "#a8823c"


def render_concept_tree(tree: dict, leaf_w=104, level_h=88, pad=28) -> str:
    """概念树 -> SVG 字符串。"""
    root = _build(tree) if isinstance(tree, dict) and "sub" in tree \
        else _build({"term": tree.get("term", ""), "essence": tree.get("essence", ""),
                     "sub": tree.get("sub", [])})
    maxd, nleaf = _layout(root)
    W = max(nleaf * leaf_w + pad * 2, 420)
    H = (maxd + 1) * level_h + pad * 2

    def px(x):
        return pad + x * leaf_w + leaf_w / 2

    def py(y):
        return pad + y * level_h + 22

    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="max-width:{W}px" '
             f'font-family="Segoe UI,Microsoft YaHei,sans-serif">']
    parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" rx="10" fill="{PAPER}"/>')

    # 先画边(在节点下)
    def edges(n):
        for c in n.children:
            x1, y1, x2, y2 = px(n.x), py(n.depth) + 13, px(c.x), py(c.depth) - 13
            mid = (y1 + y2) / 2
            parts.append(f'<path d="M{x1:.1f},{y1:.1f} C{x1:.1f},{mid:.1f} '
                         f'{x2:.1f},{mid:.1f} {x2:.1f},{y2:.1f}" fill="none" '
                         f'stroke="{LINE}" stroke-width="1.3" opacity=".85"/>')
            edges(c)
    edges(root)

    # 再画节点
    def nodes(n):
        cx, cy = px(n.x), py(n.depth)
        is_leaf = not n.children
        r = 5 if is_leaf else 7
        col = GOLD if n.depth == 0 else (ACCENT if not is_leaf else INK)
        parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" '
                     f'fill="{col}"/>')
        # 标签
        size = 13 if n.depth == 0 else 11.5
        weight = "600" if n.depth == 0 else "400"
        parts.append(f'<text x="{cx:.1f}" y="{cy - r - 6:.1f}" text-anchor="middle" '
                     f'font-size="{size}" font-weight="{weight}" fill="{INK}">'
                     f'{html.escape(n.label)}</text>')
        # 叶子的本质(小字, 斜下)
        if n.note and n.depth >= 1:
            parts.append(f'<text x="{cx:.1f}" y="{cy + r + 13:.1f}" text-anchor="middle" '
                         f'font-size="10" fill="#7a6a52">{html.escape(n.note[:14])}</text>')
        parts.append(f'<title>{html.escape(n.label)} — {html.escape(n.note)}</title>')
        for c in n.children:
            nodes(c)
    nodes(root)
    parts.append("</svg>")
    return "".join(parts)


def render_problem_tree(root_label, root_note, problems: List[dict],
                        leaf_w=88, level_h=92, pad=30) -> str:
    """问题树: 根 -> 问题(带出处边)。问题 = {statement, status, edge}"""
    root = _Node(root_label, root_note,
                 [_Node(p.get("statement", "")[:16], p.get("status", "")[:8])
                  for p in problems])
    maxd, nleaf = _layout(root)
    W = max(nleaf * leaf_w + pad * 2, 420)
    H = (maxd + 1) * level_h + pad * 2

    def px(x):
        return pad + x * leaf_w + leaf_w / 2

    def py(y):
        return pad + y * level_h + 22

    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="max-width:{W}px" '
             f'font-family="Segoe UI,Microsoft YaHei,sans-serif">']
    parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" rx="10" fill="{PAPER}"/>')
    for c in root.children:
        x1, y1, x2, y2 = px(root.x), py(0) + 14, px(c.x), py(1) - 20
        mid = (y1 + y2) / 2
        parts.append(f'<path d="M{x1:.1f},{y1:.1f} C{x1:.1f},{mid:.1f} {x2:.1f},{mid:.1f} '
                     f'{x2:.1f},{y2:.1f}" fill="none" stroke="{LINE}" stroke-width="1.2" '
                     f'opacity=".8"/>')
    # 根
    parts.append(f'<circle cx="{px(root.x):.1f}" cy="{py(0):.1f}" r="7" fill="{GOLD}"/>')
    parts.append(f'<text x="{px(root.x):.1f}" y="{py(0)-13:.1f}" text-anchor="middle" '
                 f'font-size="14" font-weight="600" fill="{INK}">{html.escape(root_label)}</text>')
    for c in root.children:
        cx, cy = px(c.x), py(1)
        parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5" fill="{INK}"/>')
        parts.append(f'<text x="{cx:.1f}" y="{cy-9:.1f}" text-anchor="middle" font-size="10.5" '
                     f'fill="{INK}">{html.escape(c.label)}</text>')
        if c.note:
            parts.append(f'<text x="{cx:.1f}" y="{cy+15:.1f}" text-anchor="middle" font-size="9.5" '
                         f'fill="#7a6a52">{html.escape(c.note)}</text>')
        parts.append(f'<title>{html.escape(c.label)} · {html.escape(c.note)}</title>')
    parts.append("</svg>")
    return "".join(parts)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from depth_sentence import TREE
    svg = render_concept_tree(TREE["记忆调性"])
    print("概念树 SVG 长度:", len(svg))
