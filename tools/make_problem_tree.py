"""生成 README 用「问题生成树」SVG: 母题 → 问题树 L0-L5 → 领域融合.
风格与 assets/architecture.svg 一致 (白底 + 蓝/金 + 灰箭头).
"""
from pathlib import Path

W, H = 1080, 720
out = Path("assets/problem_tree.svg")

svg = []
a = svg.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" font-family="Segoe UI,Microsoft YaHei,sans-serif">')
a('<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#9ca3af"/></marker>')
a('<marker id="ahb" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#2563eb"/></marker></defs>')
a(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')

# 标题
a(f'<text x="{W/2}" y="34" text-anchor="middle" font-size="17" font-weight="700" fill="#111111">问题生成树 · Problem Tree</text>')
a(f'<text x="{W/2}" y="56" text-anchor="middle" font-size="12" fill="#6b7280">母题通过组合模板生长为问题树，树与树在结构桥梁处融合 → 新问题</text>')

def box(x, y, w, h, title, lines, stroke="#111111", fill="#f9fafb", tcolor="#111111", dash=False):
    d = ' stroke-dasharray="5 4"' if dash else ""
    a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.6"{d}/>')
    a(f'<text x="{x+w/2}" y="{y+26}" text-anchor="middle" font-size="14" font-weight="700" fill="{tcolor}">{title}</text>')
    for i, ln in enumerate(lines):
        a(f'<text x="{x+w/2}" y="{y+48+i*18}" text-anchor="middle" font-size="11" fill="#6b7280">{ln}</text>')

def arrow(x1, y1, x2, y2, label="", color="#9ca3af", ly=None):
    a(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{color}" stroke-width="1.5" marker-end="url(#ah)" fill="none"/>')
    if label:
        lx, ly = (x1+x2)/2, ly if ly else (y1+y2)/2
        a(f'<text x="{lx}" y="{ly}" text-anchor="middle" font-size="11" fill="#6b7280">{label}</text>')

# ── 第 1 层: 输入 (三个来源) ──
y1 = 90
box(40, y1, 200, 76, "外部信息", ["视觉 / 听觉 / 文本", "网页 / arXiv"], stroke="#2563eb", tcolor="#2563eb")
box(270, y1, 200, 76, "日常问题", ["困惑 / 裂缝 / 疑问", "言不尽意 · 黑洞蒸发"], stroke="#2563eb", tcolor="#2563eb")
box(500, y1, 200, 76, "母题", ["质数 · 回文 · 对称 · …", "86 个母题登记"], stroke="#2563eb", tcolor="#2563eb")
box(730, y1, 310, 76, "感受 / 观察", ["结构化观测 → 输入", "问题路入口"], dash=True, stroke="#2563eb", tcolor="#2563eb")

# ── 第 2 层: 问题制造 ──
y2 = 216
box(40, y2, 1000, 84, "② 问题制造模块", ["日常问题 → 前问题 → 科学问题  →  基础领域", "territory_engine: 问题树 L0-L5 分层 · 谱系门 · 每爬一层必须机器实测"], stroke="#111111")

# 从 3 个输入汇聚到问题制造
arrow(140, y1+76, 140, y2)
arrow(370, y1+76, 370, y2)
arrow(600, y1+76, 600, y2)

# ── 第 3 层: 问题树生长 (L0-L5) ──
y3 = 352
box(40, y3, 1000, 150, "③ 问题树生长 · 母题 × 组合模板", [
    "L0 母题   →   L1 前问题   →   L2 科学问题   →   L3 基础领域   →   L4 问题树   →   L5 领域融合",
    "例: 质数 × 回文数(对象类) + 两项和(规则) + 域构造 → 「回文素数在进位制 b 中的例外」",
    "树与树在结构桥梁处交叉：无共享结构的配对是空洞笛卡尔积",
], stroke="#111111")
arrow(540, y2+84, 540, y3, color="#2563eb")

# 树节点视觉 (生长)
tcolors = ["#2563eb","#1d4ed8","#1e40af","#3730a3","#4f46e5","#7c3aed"]
tx = 120
for i, label in enumerate(["L0\n母题", "L1\n前问题", "L2\n科学问题", "L3\n基础领域", "L4\n问题树", "L5\n融合"]):
    yy = y3 + 88
    a(f'<circle cx="{tx}" cy="{yy}" r="26" fill="{tcolors[i]}" opacity="0.9"/>')
    l0, l1 = label.split("\n")
    a(f'<text x="{tx}" y="{yy-3}" text-anchor="middle" font-size="9.5" fill="#fff" font-weight="700">{l0}</text>')
    a(f'<text x="{tx}" y="{yy+9}" text-anchor="middle" font-size="9.5" fill="#fff" font-weight="700">{l1}</text>')
    if i < 5:
        a(f'<path d="M{tx+26},{yy} L{tx+66},{yy}" stroke="#9ca3af" stroke-width="1.5" marker-end="url(#ah)" fill="none"/>')
    tx += 152

# ── 第 4 层: 出口 ──
y4 = 572
box(40, y4, 460, 96, "出口 · 可判问题清单", ["每条带 判定路由 + 证据", "→ 交 AI4S 执行模块求解", "标准：答案成立 / 可判"], dash=True, stroke="#2563eb", tcolor="#2563eb")
box(540, y4, 500, 96, "出口 · 领域融合新问题", ["树 × 树 在结构桥梁处交叉", "反例驱动：只提机器答不出的", "标准：显著性 > 新颖性"], dash=True, stroke="#7c3aed", tcolor="#7c3aed")
arrow(540, y3+150, 270, y4, color="#2563eb")
arrow(540, y3+150, 790, y4, color="#7c3aed")

# 底部统计
a(f'<text x="{W/2}" y="{H-20}" text-anchor="middle" font-size="11.5" fill="#6b7280">已产出 260+ 条问题 · 23 个领域 · 其中 25 条数学题为 22 个母题的真实组合产物</text>')

a('</svg>')
out.write_text("\n".join(svg), encoding="utf-8")
print("wrote", out, out.stat().st_size, "bytes")
