# -*- coding: utf-8 -*-
"""tools/arch_diagram.py — 系统架构图（墨纸风, 与 problem_tree.svg 同一套设计系统）

风格参考 OJO Design Skills 的 theme-guide：材质隐喻（宣纸/墨/朱砂/石青）、粗粝不磨平
（纸面噪点 3–5%）、极疏留白、0–2px 圆角、无 drop shadow / 无发光 / 不用 SaaS 灰蓝紫渐变。

内容全部对得上仓库实现（模块名、引擎数量、判定器、诚实边界），不画没有的东西。

用法: python tools/arch_diagram.py
产出: assets/architecture.svg + docs/assets/architecture.svg + docs/viz/architecture.svg
"""
from pathlib import Path

from design_ink import (BRONZE, DIM, HAIR, INK, INK_SOFT, PAPER, PAPER_2, TEAL, VERMILION,
                        caption, esc, save, svg_open, title_block)

ROOT = Path(__file__).resolve().parent.parent
W, H = 1480, 880
PAD = 54
RAIL = "#ded7c6"


def panel(o, x, y, w, h, label_en, title_cn, note=None, fill=PAPER_2, accent=None):
    """分区：极浅纸色块 + 1px 墨线 + 左上角拉丁小标签（不用标题栏色块）。"""
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2" fill="{fill}" '
             f'stroke="{HAIR}" stroke-width="1"/>')
    if accent:
        o.append(f'<rect x="{x}" y="{y}" width="{w}" height="3" fill="{accent}"/>')
    o.append(f'<text x="{x + 16}" y="{y + 24}" font-size="14.5" fill="{INK}">{esc(title_cn)}</text>')
    o.append(f'<text x="{x + 16}" y="{y + 40}" font-size="10" fill="{DIM}" '
             f'font-family="JetBrains Mono,Consolas,monospace" letter-spacing="2">'
             f'{esc(label_en.upper())}</text>')
    if note:
        o.append(f'<text x="{x + w - 16}" y="{y + 24}" text-anchor="end" font-size="10.5" '
                 f'fill="{DIM}">{esc(note)}</text>')
    return y + 60


def item(o, x, y, text, sub=None, color=INK, size=12.5, bullet=True):
    o.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}">'
             f'{esc(("· " if bullet else "") + text)}</text>')
    if sub:
        o.append(f'<text x="{x + 12}" y="{y + 15}" font-size="10" fill="{DIM}">{esc(sub)}</text>')
        return y + 32
    return y + 20


def rail(o, x1, x2, y, label=None, color=INK_SOFT):
    """一条细轨 + 端头小箭头，表示数据流；不用粗色带。"""
    o.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{color}" stroke-width="1.2" '
             f'marker-end="url(#tick)"/>')
    if label:
        o.append(f'<text x="{(x1 + x2) / 2}" y="{y - 7}" text-anchor="middle" font-size="10" '
                 f'fill="{BRONZE}">{esc(label)}</text>')


def chained(o, x, y, steps, bw=96, gap=13, fs=11, h=30):
    """一排方框 + 细箭头（0–2px 圆角, 细墨线）。返回右侧端点 x。"""
    sx = x
    for i, s in enumerate(steps):
        o.append(f'<rect x="{sx}" y="{y}" width="{bw}" height="{h}" rx="2" fill="{PAPER_2}" '
                 f'stroke="{HAIR}" stroke-width="1"/>')
        o.append(f'<text x="{sx + bw / 2}" y="{y + h / 2 + 4}" text-anchor="middle" font-size="{fs}" '
                 f'fill="{INK}">{esc(s)}</text>')
        if i < len(steps) - 1:
            o.append(f'<path d="M{sx + bw},{y + h / 2} L{sx + bw + gap - 2},{y + h / 2}" '
                     f'stroke="{INK_SOFT}" stroke-width="1" marker-end="url(#tick)"/>')
        sx += bw + gap
    return sx - gap


def main():
    o = svg_open(W, H)
    title_block(o, PAD, 62, "问道系统架构",
                "ask-dao-machine architecture · 两条相互独立的路 + 四模块 + 判定层",
                note="道生一，一生二，二生三，三生万物")

    # ── 左：输入 ──────────────────────────────────────────────────────
    lw = 300
    y = panel(o, PAD, 108, lw, 360, "inputs", "输入", "三条入口")
    for t, s in (("外部信息", "网页 / arXiv / 语料 → 结构化观测"),
                 ("日常问题", "困惑 → 前问题（先良构化）"),
                 ("母题库", "assets/registry.json · 86 个母题")):
        y = item(o, PAD + 18, y + 16, t, s)
    o.append(f'<line x1="{PAD + 16}" y1="{y + 4}" x2="{PAD + lw - 16}" y2="{y + 4}" stroke="{HAIR}"/>')
    item(o, PAD + 18, y + 26, "感受模块", "视觉/听觉/网络文本 → 结构化观测", DIM, 11)

    # ── 中：两条路 ────────────────────────────────────────────────────
    px = PAD + lw + 28
    pw = 700
    y = panel(o, px, 108, pw, 360, "two independent paths", "两条独立的路",
              "产出不同 · 标准不同", fill=PAPER, accent=INK)

    o.append(f'<text x="{px + 18}" y="{y + 14}" font-size="13" fill="{INK}">问题路</text>')
    o.append(f'<text x="{px + 74}" y="{y + 14}" font-size="9.5" fill="{DIM}" '
             f'font-family="JetBrains Mono,Consolas,monospace">PROBLEM PATH · 产问题 · 需要解决</text>')
    chained(o, px + 18, y + 28, ["日常问题", "前问题", "科学问题", "基础领域", "问题树", "领域融合"],
            bw=96, gap=13)
    o.append(f'<text x="{px + 18}" y="{y + 78}" font-size="10.5" fill="{DIM}">'
             f'判定路由：数值扫描 · 构造证明 · LLM 判（N0–N3）· 新颖性门（OEIS 离线索引）</text>')
    o.append(f'<line x1="{px + 16}" y1="{y + 92}" x2="{px + pw - 16}" y2="{y + 92}" stroke="{HAIR}"/>')

    o.append(f'<text x="{px + 18}" y="{y + 120}" font-size="13" fill="{INK}">想象路</text>')
    o.append(f'<text x="{px + 74}" y="{y + 120}" font-size="9.5" fill="{DIM}" '
             f'font-family="JetBrains Mono,Consolas,monospace">IMAGINATION PATH · 产概念 · 需要解释</text>')
    chained(o, px + 18, y + 134, ["组词", "拆词(深度 d)", "还原造句", "成段", "解释"],
            bw=104, gap=9)
    o.append(f'<text x="{px + 18}" y="{y + 188}" font-size="10.5" fill="{DIM}">'
             f'成功标准：语法正确 + 逻辑通畅 + 有推理判断（概念不是拿来"解决"的）</text>')
    o.append(f'<text x="{px + 18}" y="{y + 216}" font-size="10.5" fill="{BRONZE}">'
             f'两条路互不评判：用问题路的"这新吗"去判想象路的概念，是范畴错误</text>')

    # ── 右：判定与出口 ────────────────────────────────────────────────
    rx = px + pw + 28
    rw = W - PAD - rx
    y = panel(o, rx, 108, rw, 360, "judgement & output", "判定与出口", None,
              fill=PAPER, accent=VERMILION)
    for t, s in (("判定器", "数学引擎 25 条 / 记录 28 / 组合 23"),
                 ("独立复核", "tools/ai4s_harness.py · 裁决回灌"),
                 ("LLM 判", "N0 已知 → N1 大概率已知 → N2 疑似未见 → N3 强候选"),
                 ("人类裁决", "出版级 / N2–N3 才介入")):
        y = item(o, rx + 18, y + 18, t, s, INK, 12)
    o.append(f'<line x1="{rx + 16}" y1="{y + 2}" x2="{rx + rw - 16}" y2="{y + 2}" stroke="{HAIR}"/>')
    y = item(o, rx + 18, y + 26, "出口", "带出处链的问题清单（母题→模板→绑定→判定）",
             VERMILION, 12.5)
    o.append(f'<text x="{rx + 18}" y="{y + 16}" font-size="10.5" fill="{VERMILION}">'
             f'诚实边界：世界新问题（N3）至今为 0，不粉饰</text>')

    # ── 底部：真实数据流 ─────────────────────────────────────────────
    by = 508
    panel(o, PAD, by, W - 2 * PAD, 306, "data flow · real artifacts", "真实数据流",
          "每一步都留下可复核的 JSON")
    rows = [
        ("母题 → 问题", "registry.json（86 母题）→ combo / records / math 引擎 → out/demo/problems_*.json",
         "139 母题单元"),
        ("判定 → 状态", "判定器给出 真 / 假 / 悬置，写入 problem.status 与 judgement",
         "数学域：真 15 · 验证 2 · 悬置 8"),
        ("新颖性门", "OEIS 离线索引 399,061 条序列比对 + LLM 分层判 N0–N3",
         "S2 广义 Collatz 停时表：索引未见 ×7"),
        ("可视化", "问题树 + 概念树 + 概念论证 → docs/viz/paths.html",
         "全量 260+ 条 / 23 领域"),
    ]
    ry = by + 78
    for i, (k, v, note) in enumerate(rows):
        o.append(f'<text x="{PAD + 18}" y="{ry + i * 48}" font-size="12.5" fill="{INK}">'
                 f'{esc(k)}</text>')
        o.append(f'<text x="{PAD + 156}" y="{ry + i * 48}" font-size="11" fill="{INK_SOFT}">'
                 f'{esc(v)}</text>')
        o.append(f'<text x="{W - PAD - 18}" y="{ry + i * 48}" text-anchor="end" font-size="10.5" '
                 f'fill="{TEAL}">{esc(note)}</text>')
        if i < len(rows) - 1:
            o.append(f'<line x1="{PAD + 16}" y1="{ry + i * 48 + 15}" x2="{W - PAD - 16}" '
                     f'y2="{ry + i * 48 + 15}" stroke="{RAIL}" stroke-width="1"/>')

    # ── 三轨连接 ─────────────────────────────────────────────────────
    rail(o, PAD + lw, px, 200, "结构化观测 → 问题")
    rail(o, PAD + lw, px, 300, "母题 → 生长")
    rail(o, px + pw, rx, 190, "问题清单")
    rail(o, px + pw, rx, 330, "概念 → 解释")

    caption(o, PAD, H - 26,
            "图内每个数字、模块名与状态词都对应仓库实现或 out/demo/*.json 的真实记录；"
            "没有画进图里的能力，README 里也不声称", 10)

    svg = save(o, ROOT / "assets" / "architecture.svg",
               ROOT / "docs" / "assets" / "architecture.svg",
               ROOT / "docs" / "viz" / "architecture.svg")
    print(f"wrote assets/architecture.svg ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
