# -*- coding: utf-8 -*-
"""tools/make_problem_tree.py — 用**真实数据**画「问题生成树」

数据源（全部来自机器跑出来的记录，不是手画示意）:
  out/demo/problems_math.json   : roots[{id,label,motifs,seed}] + problems[{id,statement,
                                  template,binds,judgement,status,tree:{parent,edge}}]
  out/demo/derived_motifs.json  : 母题×母题 → 派生母题（含 parents 与 frame）
  out/demo/grown_motifs.json    : 母题×母题 → 命题（含 stage 与探针阈值）
  out/ 被 .gitignore 忽略时，回退到 tools/site/tree_data.json 快照。

画什么:
  母题根 → 一级问题（边 = 真实操作: 把'质数'换成'奇合数' / 加约束:两数不同 /
  参数移动 c:0→1 / 升级为无穷性 …）→ 二级问题；节点颜色 = 真实判定状态
  （朱砂 = 真/假 已落锤，石青 = 有限/数值验证，青铜虚线 = 悬置开放）。

风格: 墨纸（tools/design_ink.py，参考 OJO：材质隐喻 / 极疏 / 0–2px 圆角 / 无发光 / 纸面噪点）。

用法: python tools/make_problem_tree.py
产出: assets/problem_tree.svg + docs/assets/problem_tree.svg
"""
import json
from collections import Counter, OrderedDict
from pathlib import Path

from design_ink import (BRONZE, DIM, HAIR, INK, TEAL, VERMILION, caption, legend, node, save,
                        status_style, svg_open, title_block, esc)

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "out" / "demo"
SNAP = ROOT / "tools" / "site" / "tree_data.json"

W = 1480
COL_W, COL_GAP = 196, 32
PAD_X, TOP = 54, 152
NODE_H, V_GAP = 64, 22
TAIL = 420                      # 图例 + inset + 说明 需要的底部空间


def load():
    """真实数据；out/ 不在时用仓库里的快照。"""
    if (D / "problems_math.json").exists():
        pm = json.loads((D / "problems_math.json").read_text(encoding="utf-8"))
        data = {
            "roots": pm.get("roots") or [],
            "problems": pm.get("problems") or [],
            "derived": json.loads((D / "derived_motifs.json").read_text(encoding="utf-8")),
            "grown": json.loads((D / "grown_motifs.json").read_text(encoding="utf-8")),
        }
        SNAP.parent.mkdir(parents=True, exist_ok=True)
        SNAP.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print("数据源: out/demo/*.json（并已写快照）")
        return data
    print("数据源: 快照", SNAP.name)
    return json.loads(SNAP.read_text(encoding="utf-8"))


def build_tree(data):
    """按 problem.tree.parent 还原父子关系；根 = roots ∪ (parent 中不是问题 id 的节点)。"""
    probs = data["problems"]
    by_id = {p["id"]: p for p in probs}
    children = OrderedDict()
    for p in probs:
        children.setdefault((p.get("tree") or {}).get("parent"), []).append(p)
    for k in children:
        children[k].sort(key=lambda p: str(p["id"]))
    explicit = [r["id"] for r in data.get("roots") or []]
    implicit = [k for k in children if k and k not in by_id and k not in explicit]
    roots = [r for r in explicit + implicit if children.get(r)]
    seed = {r["id"]: r for r in data.get("roots") or []}
    return by_id, children, roots, seed


def place(children, roots):
    """先算布局（列 → 节点序列），得到总高，再画。"""
    cols, bottom = [], TOP
    for rid in roots:
        nodes, y = [], TOP + 10
        for k, p in enumerate(children.get(rid, [])):
            nodes.append({"kind": "child", "y": y, "p": p, "first": k == 0})
            y += NODE_H + V_GAP + 14
            for g in children.get(p["id"], []):
                nodes.append({"kind": "grand", "y": y, "p": g, "parent_of": p["id"]})
                y += NODE_H + V_GAP
        cols.append({"root": rid, "nodes": nodes})
        bottom = max(bottom, y)
    return cols, bottom


def main():
    data = load()
    by_id, children, roots, seed = build_tree(data)
    probs = data["problems"]
    cols, bottom = place(children, roots)

    H = int(bottom + TAIL)
    st = Counter()
    for p in probs:
        c, _ = status_style(p.get("status", ""))
        st["真/假（已落锤）" if c == VERMILION else
           "有限/数值验证" if c == TEAL else "悬置（开放）"] += 1
    ops = sorted({(p.get("tree") or {}).get("edge") for p in probs
                  if (p.get("tree") or {}).get("edge")})

    o = svg_open(W, H)
    title_block(o, PAD_X, 62, "问题生成树",
                "problem generation tree · every node is a real machine output",
                note=f"{len(probs)} 个问题 · {len(roots)} 个母题根 · {len(ops)} 类生成操作")

    for ci, col in enumerate(cols):
        rid = col["root"]
        x = PAD_X + ci * (COL_W + COL_GAP)
        r = seed.get(rid, {})
        label = str(r.get("label") or rid)
        motifs = " · ".join(r.get("motifs") or [])[:32]
        o.append(f'<text x="{x}" y="{TOP - 42}" font-size="12.5" fill="{INK}">'
                 f'{esc(label[:13])}</text>')
        o.append(f'<text x="{x}" y="{TOP - 26}" font-size="10" fill="{DIM}" '
                 f'font-family="JetBrains Mono,Consolas,monospace">{esc(rid)}</text>')
        o.append(f'<text x="{x}" y="{TOP - 11}" font-size="9.5" fill="{DIM}">'
                 f'{esc(motifs if motifs else "母题根（由 problem.tree.parent 反推）")}</text>')
        o.append(f'<line x1="{x}" y1="{TOP - 4}" x2="{x + COL_W}" y2="{TOP - 4}" '
                 f'stroke="{HAIR}" stroke-width="1"/>')

        for nd in col["nodes"]:
            p, y, grand = nd["p"], nd["y"], nd["kind"] == "grand"
            t = p.get("tree") or {}
            edge_label = "↳ " + str(t.get("edge") or "")[:18]
            if grand:
                gx = x + 18
                o.append(f'<path d="M{x + COL_W - 8},{y - 52} C{x + COL_W + 12},{y - 52} '
                         f'{x + COL_W + 12},{y + 6} {gx},{y + 6}" fill="none" stroke="{HAIR}" '
                         f'stroke-width="1" marker-end="url(#tick)"/>')
                o.append(f'<text x="{gx + 10}" y="{y - 4}" font-size="9.5" fill="{BRONZE}">'
                         f'{esc(edge_label)}</text>')
                node(o, gx, y, COL_W - 18, NODE_H, p["id"], p.get("statement", ""),
                     p.get("status", ""))
            else:
                if not nd.get("first"):
                    o.append(f'<line x1="{x + 6}" y1="{y - V_GAP - 14}" x2="{x + 6}" y2="{y + 8}" '
                             f'stroke="{HAIR}" stroke-width="1"/>')
                o.append(f'<path d="M{x + 6},{y - 14} C{x + 6},{y - 2} {x + 6},{y + 2} '
                         f'{x + 14},{y + 6}" fill="none" stroke="{HAIR}" stroke-width="1" '
                         f'marker-end="url(#tick)"/>')
                o.append(f'<text x="{x + 16}" y="{y - 4}" font-size="9.5" fill="{BRONZE}">'
                         f'{esc(edge_label)}</text>')
                node(o, x, y, COL_W, NODE_H, p["id"], p.get("statement", ""), p.get("status", ""))

    # ── 图例（用真实状态词） ────────────────────────────────────────────
    legend(o, PAD_X, bottom + 26,
           [(f"真 / 假 · 已落锤 {st['真/假（已落锤）']}", VERMILION, False),
            (f"有限 / 数值验证 {st['有限/数值验证']}", TEAL, False),
            (f"悬置 · 开放 {st['悬置（开放）']}", BRONZE, True)])
    caption(o, PAD_X, bottom + 50,
            "节点正文 = 机器产出的原始 statement（节选）；节点内小字 = 真实判定状态；"
            "边上的 ↳ = 真实生成操作（problem.tree.edge）", 10)

    # ── 底部 inset：真实跨域融合（两行，避免右侧溢出画布） ────────────────
    line_y = bottom + 86
    o.append(f'<line x1="{PAD_X}" y1="{line_y}" x2="{W - PAD_X}" y2="{line_y}" stroke="{HAIR}"/>')
    o.append(f'<text x="{PAD_X}" y="{line_y + 26}" font-size="12.5" fill="{INK}">'
             f'领域交叉：母题 × 母题 → 派生母题（真实记录）</text>')

    iy = line_y + 62
    x = PAD_X
    for r in [r for r in data["derived"] if r.get("cross")][:3]:
        pa = r["parents"][0].split("::")[-1]
        pb = r["parents"][1].split("::")[-1]
        o.append(f'<text x="{x}" y="{iy}" font-size="11.5" fill="{INK}">{esc(pa[:9])}</text>')
        o.append(f'<text x="{x}" y="{iy + 15}" font-size="11.5" fill="{INK}">× {esc(pb[:9])}</text>')
        o.append(f'<path d="M{x + 100},{iy + 6} C{x + 120},{iy + 6} {x + 116},{iy + 54} '
                 f'{x + 132},{iy + 54}" fill="none" stroke="{BRONZE}" stroke-width="1" '
                 f'marker-end="url(#tick)"/>')
        o.append(f'<text x="{x + 138}" y="{iy + 42}" font-size="11" fill="{INK}">'
                 f'{esc(str(r["derived"])[:15])}</text>')
        o.append(f'<text x="{x + 138}" y="{iy + 56}" font-size="9.5" fill="{DIM}" '
                 f'font-family="JetBrains Mono,Consolas,monospace">{esc(r["id"])} · '
                 f'{esc(r["frame"])} · {esc(r["route"])}</text>')
        x += 440

    gy = iy + 96
    o.append(f'<text x="{PAD_X}" y="{gy}" font-size="12.5" fill="{INK}">'
             f'同类母题配对（质数 × 对象类 → 配对集命题, 机器实测阈值）</text>')
    gx = PAD_X
    for r in [r for r in data["grown"] if r.get("stage") == "confirmed"][:3]:
        pr = r.get("probe") or {}
        o.append(f'<text x="{gx}" y="{gy + 24}" font-size="11.5" fill="{INK}">'
                 f'{esc(str(r["derived"])[:13])}</text>')
        o.append(f'<text x="{gx}" y="{gy + 40}" font-size="9.5" fill="{TEAL}">'
                 f'stage=confirmed · 阈值 {pr.get("threshold")} · '
                 f'例外前 {len(pr.get("fails_head") or [])} 项</text>')
        o.append(f'<text x="{gx}" y="{gy + 54}" font-size="9.5" fill="{DIM}" '
                 f'font-family="JetBrains Mono,Consolas,monospace">{esc(r["id"])} · '
                 f'{esc(str(r["type"])[:16])}</text>')
        gx += 330

    caption(o, PAD_X, gy + 86,
            "节点 / 边 / 状态 / 操作文字全部取自 out/demo/*.json 的真实记录；"
            "完整问题集与证据见 docs/viz/paths.html", 10)

    svg = save(o, ROOT / "assets" / "problem_tree.svg", ROOT / "docs" / "assets" / "problem_tree.svg")
    print(f"wrote assets/problem_tree.svg ({W}x{H}, {len(svg)} bytes)")
    print(f"节点: {len(probs)} 问题 + {len(roots)} 母题根; 操作 {len(ops)} 类; 状态 {dict(st)}")


if __name__ == "__main__":
    main()

