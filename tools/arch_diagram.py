# -*- coding: utf-8 -*-
"""tools/arch_diagram.py — 系统架构图（SVG, 极简风）

产出 assets/architecture.svg（README 内嵌）+ docs/viz/architecture.svg
内容: 四个模块 + 两条路 + 数据流 + AI4S 接口。
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
ASSETS = HERE / "assets"

INK = "#111111"
DIM = "#6b7280"
LINE = "#9ca3af"
ACCENT = "#b02a24"
BLUE = "#2563eb"
GOLD = "#a16207"
BG = "#ffffff"
BOX = "#f9fafb"


def box(x, y, w, h, title, lines, color=INK, dash=None, rx=10, fill=BOX):
    o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
         f'fill="{fill}" stroke="{color}" stroke-width="1.6"']
    if dash:
        o.append(f' stroke-dasharray="{dash}"')
    o.append('/>')
    o.append(f'<text x="{x + w / 2}" y="{y + 26}" text-anchor="middle" '
             f'font-size="15" font-weight="700" fill="{color}">{title}</text>')
    for i, l in enumerate(lines):
        o.append(f'<text x="{x + w / 2}" y="{y + 48 + i * 17}" text-anchor="middle" '
                 f'font-size="11.5" fill="{DIM}">{l}</text>')
    return "".join(o)


def arrow(x1, y1, x2, y2, color=LINE, label="", dash=None, lx=None, ly=None):
    o = [f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{color}" stroke-width="1.5" '
         f'marker-end="url(#ah)" fill="none"']
    if dash:
        o.append(f' stroke-dasharray="{dash}"')
    o.append('/>')
    if label:
        mx = lx if lx is not None else (x1 + x2) / 2
        my = ly if ly is not None else (y1 + y2) / 2
        o.append(f'<text x="{mx}" y="{my - 5}" text-anchor="middle" font-size="11" '
                 f'fill="{DIM}">{label}</text>')
    return "".join(o)


def build():
    W, H = 1080, 660
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'width="100%" font-family="Segoe UI,Microsoft YaHei,sans-serif">']
    p.append(f'''<defs>
<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7"
        orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{LINE}"/></marker>
<marker id="ahb" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7"
        orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{BLUE}"/></marker>
<marker id="ahr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7"
        orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{ACCENT}"/></marker>
</defs>''')
    p.append(f'<rect width="{W}" height="{H}" fill="{BG}"/>')

    # 标题
    p.append(f'<text x="{W/2}" y="34" text-anchor="middle" font-size="17" '
             f'font-weight="700" fill="{INK}">问道 · 系统架构</text>')
    p.append(f'<text x="{W/2}" y="56" text-anchor="middle" font-size="12" '
             f'fill="{DIM}">两条路：一条产问题（需解决），一条产概念（需解释）</text>')

    # ── 问题路（上排）───────────────────────────────
    p.append(f'<text x="40" y="96" font-size="13" font-weight="700" fill="{BLUE}">'
             f'问题路 · Problem Path</text>')
    p.append(box(40, 108, 208, 100, "① 感受模块",
                 ["视觉 / 听觉 / 网络文本", "→ 结构化观测", "perception · web · arxiv"]))
    p.append(box(276, 108, 208, 100, "② 问题制造模块",
                 ["日常问题 → 前问题 → 科学问题", "→ 基础领域 → 问题树 → 融合",
                  "corpus · counterex · territory"]))
    p.append(box(512, 108, 208, 100, "③ 执行模块 AI4S",
                 ["独立验证 / 求解", "裁决回灌", "ai4s_harness"]))
    p.append(box(748, 108, 292, 100, "出口 · 可判问题清单",
                 ["每条带 判定路由 + 证据", "→ 交 AI4S 求解",
                  "标准：答案成立 / 可判"],
                 color=BLUE, dash="5 4"))
    p.append(arrow(248, 158, 276, 158, BLUE, "结构化", lx=262, ly=150))
    p.append(arrow(484, 158, 512, 158, BLUE, "问题", lx=498, ly=150))
    p.append(arrow(720, 158, 748, 158, BLUE, "交付", lx=734, ly=150))

    # ── 想象路（下排）───────────────────────────────
    p.append(f'<text x="40" y="266" font-size="13" font-weight="700" fill="{GOLD}">'
             f'想象路 · Imagination Path</text>')
    p.append(box(40, 278, 208, 100, "输入 · 词",
                 ["任意词 / 词对", "例：记忆调性", "原则：每个词都有意义"],
                 color=GOLD, dash="5 4"))
    p.append(box(276, 278, 208, 100, "① 组词",
                 ["穷尽领域专业词组合", "82 × 82 = 6642", "word_fusion"]))
    p.append(box(512, 278, 208, 100, "② 拆词（深度 d）",
                 ["问\"它是什么?\" → 拆实体", "→ 再问 → 拆到原子概念",
                  "depth_sentence"]))
    p.append(box(748, 278, 292, 100, "③ 还原造句 → 成段 → 解释",
                 ["嵌套 + 推理 + 判断 + 比较", "定义 → 判断 → 比较 → 结论",
                  "reconstruct · understand_deep"]))
    p.append(arrow(248, 328, 276, 328, GOLD, "词对", lx=262, ly=320))
    p.append(arrow(484, 328, 512, 328, GOLD, "组合", lx=498, ly=320))
    p.append(arrow(720, 328, 748, 328, GOLD, "展开", lx=734, ly=320))

    # ── 想象路出口（单独一行）──────────────────────
    p.append(box(748, 400, 292, 76, "出口 · 被理解的概念 / 理论",
                 ["标准：语法正确 + 逻辑通畅", "     + 有推理判断"],
                 color=GOLD, dash="5 4"))
    p.append(arrow(894, 378, 894, 400, GOLD))

    # ── 两条路的隔离线 ─────────────────────────────
    p.append(f'<line x1="40" y1="232" x2="1040" y2="232" stroke="{LINE}" '
             f'stroke-width="1" stroke-dasharray="2 6"/>')
    p.append(f'<text x="546" y="228" text-anchor="middle" font-size="10.5" fill="{DIM}">'
             f'两条路互相独立 · 各有各的成功标准 · 不许互相评判</text>')

    # ── 底部：诚实边界 ─────────────────────────────
    p.append(f'<rect x="40" y="512" width="1000" height="112" rx="10" '
             f'fill="#fef2f2" stroke="{ACCENT}" stroke-width="1.3"/>')
    p.append(f'<text x="60" y="540" font-size="13" font-weight="700" fill="{ACCENT}">'
             f'诚实边界（不许粉饰）</text>')
    for i, t in enumerate([
        "N3（世界新问题）至今 = 0 —— 机器能产「真问题」「已知·未解问题」「参照系未见候选」，但无一条通过三重门槛；",
        "「检索未见」≠「新」—— 手头参照系只有 OEIS + 检索，真正的文献门需要人 / 联网；",
        "显著性 &gt; 新颖性 —— 任选参数的序列同样「OEIS 未见」，唯一拦得住的是显著性证书。",
    ]):
        p.append(f'<text x="60" y="565 + i * 20" font-size="11.5" fill="#7f1d1d">· {t}</text>')

    p.append('</svg>')
    return "".join(p)


def main():
    svg = build()
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "architecture.svg").write_text(svg, encoding="utf-8")
    viz = HERE / "docs" / "viz"
    viz.mkdir(parents=True, exist_ok=True)
    (viz / "architecture.svg").write_text(svg, encoding="utf-8")
    print("saved:", ASSETS / "architecture.svg")
    print("saved:", viz / "architecture.svg")


if __name__ == "__main__":
    main()
