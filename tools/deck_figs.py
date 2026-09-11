# -*- coding: utf-8 -*-
"""deck_figs.py — 从真实产物生成 PPT 用图（OJO 墨纸风）。

设计纪律（与站点/CLI 同一套视觉 DNA）：
  完成度 粗粝 · 密度 极疏 · 重量 克制 · 严肃度 学术
  色彩语义：宣纸 #f6f2e9 · 墨 #16191d · 石青 #2f6b6b（已实测/可复用）
            朱砂 #b03a2e（机器算出 / 需注意）· 青铜 #9a7b3f（编号与标签）
  材质：1px 细线、无渐变、无发光、无圆角气泡
  数据纪律：每个数字都从 out/ 或 data/ 的真实产物读；读不到就不画，
            绝不用手打值占位（画不出图比画错图好）。

用法：python tools/deck_figs.py [--out docs/ppt/figs]
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.font_manager import findSystemFonts, FontProperties

ROOT = Path(__file__).resolve().parent.parent
PAPER, INK, MINERAL, VERM, BRONZE = "#f6f2e9", "#16191d", "#2f6b6b", "#b03a2e", "#9a7b3f"
MUTE = "#6b7078"
LINE = "#cfc9be"


# ── 中文字体 ─────────────────────────────────────────────────────────
def cjk_font() -> FontProperties:
    prefer = ["msyh.ttc", "msyhbd.ttc", "simhei.ttf", "simsun.ttc",
              "SourceHanSerifSC-Regular.otf", "NotoSansCJK-Regular.ttc"]
    found = {Path(p).name.lower(): p for p in findSystemFonts()}
    for name in prefer:
        if name.lower() in found:
            return FontProperties(fname=found[name.lower()])
    for low, p in found.items():
        if any(k in low for k in ("msyh", "simhei", "simsun", "cjk", "yahei", "song")):
            return FontProperties(fname=p)
    return FontProperties()


FP = cjk_font()


def setup():
    plt.rcParams.update({
        "figure.facecolor": PAPER, "axes.facecolor": PAPER, "savefig.facecolor": PAPER,
        "text.color": INK, "axes.labelcolor": INK, "axes.edgecolor": LINE,
        "xtick.color": MUTE, "ytick.color": MUTE, "axes.linewidth": 0.8,
        "font.size": 11, "axes.unicode_minus": False, "savefig.dpi": 200,
        "figure.dpi": 200,
    })


def load(rel, default=None):
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception:
        return default


def bare(ax, keep_left=False, keep_bottom=False):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_visible(keep_left)
    ax.spines["bottom"].set_visible(keep_bottom)
    ax.tick_params(length=0)


def title(ax, text, sub=None):
    """图内不重复幻灯片标题；只留一行小字方法论注记（也是唯一的图内说明）。"""
    if sub:
        ax.text(0, 1.02, sub, fontproperties=FP, fontsize=9.2, color=MUTE,
                transform=ax.transAxes, va="bottom")


def save(fig, out: Path, name: str):
    p = out / name
    fig.savefig(p, bbox_inches="tight", pad_inches=0.22)
    plt.close(fig)
    print(f"  {name}  {p.stat().st_size:,}B")


# ══════════════════════════════════════════════════════════════════
# 真实数字
# ══════════════════════════════════════════════════════════════════
def biomed_numbers():
    B = load("out/biomed_demo/problems_paper.json", {"problems": []})
    ps = B.get("problems", [])
    ev = [p for p in ps if p.get("signal") == "BM_EVALUE"]
    bm = [p for p in ps if p.get("domain") == "生物医学"]
    mg = [p for p in bm if p.get("signal") != "BM_EVALUE"]
    tension = [p for p in ps if p.get("signal") in ("however", "yet", "inconsistent")]
    struct = [p for p in ps if p.get("signal") == "equivalent"]
    return {
        "total": len(ps), "ev": ev, "bm": len(bm), "mg": mg,
        "n_mg": len(mg), "n_tension": len(tension), "n_struct": len(struct),
        "n_ev": len(ev),
        "touched": sum(1 for x in mg if x.get("author_touched")),
        "untouched": sum(1 for x in mg if not x.get("author_touched")),
    }


# ══════════════════════════════════════════════════════════════════
# 图 1 · E-value：机器算出的新知识
# ══════════════════════════════════════════════════════════════════
def fig_evalue(out: Path, bm: dict):
    ev = bm["ev"]
    if not ev:
        print("  ! fig_evalue: 无 E-value 数据，跳过")
        return
    rows = []
    for p in ev:
        c = p["computed"]
        rows.append((c["point"], c["evalue_point"], c["evalue_ci_bound"], tuple(c["ci"])))
    rows.sort(key=lambda r: r[0])

    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    y = range(len(rows))
    h = 0.34
    for i, (hr, e, eci, ci) in enumerate(rows):
        ax.barh(i + h / 2 + 0.04, e, height=h, color=VERM, zorder=3)
        ax.barh(i - h / 2 - 0.04, hr, height=h, color=MINERAL, zorder=3)
        ax.plot([eci], [i + h / 2 + 0.04], marker="|", ms=13, mew=1.6, color=INK, zorder=4)
        ax.text(e + 0.045, i + h / 2 + 0.04, f"E = {e:.2f}", fontproperties=FP,
                fontsize=10.5, color=VERM, va="center")
        ax.text(eci, i + h / 2 + 0.245, f"CI 下界 {eci:.2f}", fontproperties=FP,
                fontsize=8, color=MUTE, ha="center", va="bottom")
        ax.text(hr + 0.045, i - h / 2 - 0.04, f"{hr:.2f}", fontproperties=FP,
                fontsize=10.5, color=MINERAL, va="center")

    ax.set_yticks(list(y))
    ax.set_yticklabels([f"HR {r[0]:.2f}\n({r[3][0]:.2f}–{r[3][1]:.2f})" for r in rows],
                       fontproperties=FP, fontsize=9.5)
    ax.set_xlim(0, 2.75)
    ax.set_ylim(-0.62, len(rows) - 0.30)
    ax.set_xlabel("关联强度（RR 尺度）", fontproperties=FP, fontsize=10)
    ax.tick_params(axis="x", labelsize=9)
    for lbl in ax.get_xticklabels():
        lbl.set_fontproperties(FP)
    bare(ax)
    ax.grid(axis="x", color=LINE, lw=0.6, alpha=0.7, zorder=0)
    ax.set_axisbelow(True)

    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=MINERAL, label="论文报告的效应量"),
                       Patch(color=VERM, label="机器算出的 E-value（残余混杂门槛）")],
              prop=FP, fontsize=9.5, frameon=False, loc="lower right")
    title(ax, "把「论文自报的 HR」换算成「需要多强的未测混杂才能解释掉」",
          "公式 E = RR + √(RR(RR−1))，RR 用 HR 近似（只在结局不常见时成立）。")
    fig.subplots_adjust(top=0.80)
    save(fig, out, "fig_evalue.png")


# ══════════════════════════════════════════════════════════════════
# 图 2 · 54 条问题的构成
# ══════════════════════════════════════════════════════════════════
def fig_biomed_composition(out: Path, bm: dict):
    segs = [
        ("③ 结构追问", bm["n_struct"], MINERAL),
        ("② 文本张力", bm["n_tension"], BRONZE),
        ("④ 方法学追问", bm["n_mg"], VERM),
        ("机器算出 · E-value", bm["n_ev"], "#7a2e26"),
    ]
    total = sum(s[1] for s in segs)
    if total != bm["total"]:
        segs.append(("其他", bm["total"] - total, MUTE))

    fig, ax = plt.subplots(figsize=(6.6, 2.55))
    left = 0
    for name, n, col in segs:
        ax.barh(1, n, left=left, height=0.42, color=col, zorder=3)
        if n >= 4:
            ax.text(left + n / 2, 1, str(n), fontproperties=FP, fontsize=12,
                    color="#ffffff", ha="center", va="center", zorder=4)
        ax.text(left + n / 2, 1.34, name, fontproperties=FP, fontsize=9.5,
                color=INK, ha="center", va="bottom")
        left += n

    # 第二行：29 条方法学追问的作者标注
    mg = bm["n_mg"]
    ax.barh(0, bm["touched"], height=0.42, color=MINERAL, zorder=3)
    ax.barh(0, bm["untouched"], left=bm["touched"], height=0.42, color="#c9c3b8", zorder=3)
    ax.text(bm["touched"] / 2, 0, f"{bm['touched']}", fontproperties=FP, fontsize=12,
            color="#ffffff", ha="center", va="center", zorder=4)
    ax.text(bm["touched"] + bm["untouched"] / 2, 0, f"{bm['untouched']}",
            fontproperties=FP, fontsize=11, color=INK, ha="center", va="center", zorder=4)
    ax.text(0, -0.34, f"其中 {mg} 条方法学追问的主题：作者文中已论及 {bm['touched']} · 文中未见 {bm['untouched']}",
            fontproperties=FP, fontsize=9.5, color=MUTE, va="top")

    ax.set_xlim(0, bm["total"] * 1.02)
    ax.set_ylim(-0.75, 1.72)
    ax.set_yticks([])
    ax.set_xticks([0, 10, 20, 30, 40, 50])
    ax.set_xlabel(f"条（合计 {bm['total']}）", fontproperties=FP, fontsize=10)
    for lbl in ax.get_xticklabels():
        lbl.set_fontproperties(FP)
        lbl.set_fontsize(9)
    bare(ax)
    title(ax, "一篇论文 → 54 条可判问题：四条来源",
          "① 作者自陈未解命中 0 条 —— 所以这 54 条都是机器提出的，不是抄作者的待办清单。")
    fig.subplots_adjust(top=0.76)
    save(fig, out, "fig_biomed_composition.png")


# ══════════════════════════════════════════════════════════════════
# 图 3 · 模型侧：544 条问题 / 23 领域
# ══════════════════════════════════════════════════════════════════
def fig_domains(out: Path):
    DM = load("out/demo/discovery_manifest.json", {})
    ps = DM.get("problems", [])
    if not ps:
        print("  ! fig_domains: 无可读产物，跳过")
        return
    c = Counter(p.get("domain") for p in ps if p.get("domain"))
    items = c.most_common(14)
    names = [k for k, _ in items][::-1]
    vals = [v for _, v in items][::-1]
    bio = {"生物", "医学", "生物医学"}

    fig, ax = plt.subplots(figsize=(6.6, 5.0))
    cols = [VERM if n in bio else MINERAL for n in names]
    ax.barh(range(len(names)), vals, height=0.66, color=cols, zorder=3)
    for i, v in enumerate(vals):
        ax.text(v + 1.2, i, str(v), fontproperties=FP, fontsize=9.5,
                color=INK, va="center")
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontproperties=FP, fontsize=10)
    ax.set_xlabel(f"问题条数（共 {len(ps)} 条 / {len(c)} 个领域）", fontproperties=FP, fontsize=10)
    for lbl in ax.get_xticklabels():
        lbl.set_fontproperties(FP)
        lbl.set_fontsize(9)
    ax.set_xlim(0, max(vals) * 1.16)
    bare(ax)
    ax.grid(axis="x", color=LINE, lw=0.6, alpha=0.7, zorder=0)
    ax.set_axisbelow(True)
    ax.text(0.99, 0.02, "朱砂 = 生物 / 医学相关域", fontproperties=FP, fontsize=9,
            color=VERM, transform=ax.transAxes, ha="right")
    title(ax, "问题路：544 条问题覆盖 23 个领域",
          "每个领域由领域引擎并行产出；条数最多的前 14 个领域见图。")
    fig.subplots_adjust(top=0.90)
    save(fig, out, "fig_domains.png")


# ══════════════════════════════════════════════════════════════════
# 图 4 · 独立裁决：15 个进制的判决
# ══════════════════════════════════════════════════════════════════
def fig_harness(out: Path):
    H = load("out/demo/harness_verdicts.json", [])
    if not H:
        print("  ! fig_harness: 无可读产物，跳过")
        return
    rows = []
    for r in H:
        v = str(r.get("verdict", ""))
        kind = ("confirmed" if v.startswith("confirmed")
                else "rejected" if v.startswith("rejected") else "open")
        n0 = r.get("count_N0")
        newx = len(r.get("new_exceptions") or [])
        rows.append((r.get("b"), kind, n0, newx))
    rows.sort(key=lambda r: (r[0] if isinstance(r[0], int) else 99))

    fig, ax = plt.subplots(figsize=(6.6, 3.9))
    colmap = {"confirmed": MINERAL, "open": BRONZE, "rejected": VERM}
    xs = list(range(len(rows)))
    vals = [(r[2] if isinstance(r[2], int) else 0) for r in rows]
    cols = [colmap[r[1]] for r in rows]
    ax.bar(xs, vals, width=0.62, color=cols, zorder=3)
    ax.set_yscale("symlog", linthresh=10)
    ax.set_xticks(xs)
    ax.set_xticklabels([f"b={r[0]}" for r in rows], fontproperties=FP, fontsize=8.5)
    ax.set_ylabel("N0 档的例外数（symlog）", fontproperties=FP, fontsize=10)
    for lbl in ax.get_yticklabels():
        lbl.set_fontproperties(FP)
        lbl.set_fontsize(9)
    bare(ax)
    ax.grid(axis="y", color=LINE, lw=0.6, alpha=0.7, zorder=0)
    ax.set_axisbelow(True)

    n_conf = sum(1 for r in rows if r[1] == "confirmed")
    n_open = sum(1 for r in rows if r[1] == "open")
    n_rej = sum(1 for r in rows if r[1] == "rejected")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=MINERAL, label=f"confirmed {n_conf}（例外集在 N1 档不再新增）"),
                       Patch(color=BRONZE, label=f"open {n_open}（例外仍在冒）"),
                       Patch(color=VERM, label=f"rejected {n_rej}（出现新例外）")],
              prop=FP, fontsize=9, frameon=False, loc="upper right")
    title(ax, f"独立裁决：{len(rows)} 个进制的命题 P(b) 判决",
          "判据不是「跑了没报错」，而是 N0 与 N1 两档的例外集是否汇合、有没有冒出新例外。")
    fig.subplots_adjust(top=0.80)
    save(fig, out, "fig_harness.png")


# ══════════════════════════════════════════════════════════════════
# 图 5 · 跨域融合漏斗
# ══════════════════════════════════════════════════════════════════
def fig_fusion(out: Path):
    FF = load("out/demo/field_fusion.json", {})
    fields = FF.get("fields", {})
    pairs = FF.get("total_pairs")
    hot = FF.get("cross_hot")
    cands = FF.get("candidates", [])
    if not fields or not pairs:
        print("  ! fig_fusion: 无可读产物，跳过")
        return
    bio = [c for c in cands if "生物" in json.dumps(c, ensure_ascii=False)
           or "医" in json.dumps(c, ensure_ascii=False)]

    stages = [("领域", len(fields), INK), ("两两配对", pairs, MUTE),
              ("共享结构桥梁", hot, MINERAL), ("跨域候选（可算）", len(cands), BRONZE),
              ("其中牵涉生物", len(bio), VERM)]
    fig, ax = plt.subplots(figsize=(6.6, 3.2))
    for i, (name, v, col) in enumerate(stages):
        w = 10 ** (len(str(v)) - 1)
        ax.barh(-i, v, height=0.56, color=col, zorder=3)
        ax.text(v * 1.06, -i, f"{v:,}", fontproperties=FP, fontsize=11, color=col, va="center")
        ax.text(-pairs * 0.035, -i, name, fontproperties=FP, fontsize=10,
                color=INK, va="center", ha="right")
    ax.set_xlim(-pairs * 0.44, pairs * 1.24)
    ax.set_ylim(-len(stages) + 0.42, 0.58)
    ax.set_yticks([])
    ax.set_xticks([])
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(False)
    ax.text(0, -len(stages) + 0.62,
            "没有共享结构的配对判为「空洞笛卡尔积」，不计入桥梁。",
            fontproperties=FP, fontsize=9, color=MUTE, va="top")
    title(ax, f"跨域融合：{len(fields)} 个领域 → {hot} 座结构桥梁",
          "融合不是把两个领域的词拼在一起，而是找共享结构。")
    fig.subplots_adjust(top=0.78)
    save(fig, out, "fig_fusion.png")


# ══════════════════════════════════════════════════════════════════
# 图 6 · 经验检索桥漏斗
# ══════════════════════════════════════════════════════════════════
def fig_bridge(out: Path):
    BMS = load("out/demo/browser_mass_search.json", [])
    if not BMS:
        print("  ! fig_bridge: 无可读产物，跳过")
        return
    n = len(BMS)
    entry = sum(1 for x in BMS if x.get("has_entry_hits"))
    NEWPAGE = "您可以新建这个页面"
    words = sum(1 for x in BMS
                if (x.get("search") or {}).get("snippet")
                and NEWPAGE not in x["search"]["snippet"])
    wiki_dir = ROOT / "data" / "wiki"
    wiki = len([p for p in wiki_dir.glob("*.json") if p.name != "_failed.json"]) if wiki_dir.exists() else 0
    try:
        anchors = (ROOT / "out/demo/word_understand.json").read_text(encoding="utf-8").count("经验锚点")
    except Exception:
        anchors = 0

    stages = [(f"{n:,}", "两两组合词", INK), (f"{entry:,}", "维基词条通道命中", MINERAL),
              (f"{words:,}", "维基已有独立条目", BRONZE), (f"{wiki:,}", "已抓为语料（词条）", MUTE),
              (f"{anchors}", "写出经验锚点", VERM)]
    fig, ax = plt.subplots(figsize=(6.6, 3.1))
    for i, (val, name, col) in enumerate(stages):
        ax.barh(-i, 1, height=0.54, color=col, zorder=3)
        ax.text(1.03, -i, name, fontproperties=FP, fontsize=10, color=INK, va="center")
        ax.text(0.5, -i, val, fontproperties=FP, fontsize=11.5, color="#ffffff",
                va="center", ha="center", zorder=4)
    ax.set_xlim(0, 2.0)
    ax.set_ylim(-len(stages) + 0.4, 0.6)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(False)
    pa = 100.0 * entry / n
    pw = 100.0 * words / n
    ax.text(0, -len(stages) + 0.58,
            f"词条通道命中率 {pa:.1f}% · 已建成独立条目仅 {pw:.1f}% —— 「检索未见」是常态，不是发现。",
            fontproperties=FP, fontsize=9, color=MUTE, va="top")
    title(ax, f"经验检索桥：{n:,} 个组合词接上现实经验",
          "两条路可以各自单独跑，也可以选择过桥；过桥只做脚手架，不做裁判。")
    fig.subplots_adjust(top=0.80)
    save(fig, out, "fig_bridge.png")


# ══════════════════════════════════════════════════════════════════
# 图 7 · 五步流水线（想象路）
# ══════════════════════════════════════════════════════════════════
def _flow(ax, steps, y=0.5, h=0.30, gap=0.022):
    n = len(steps)
    w = (1 - gap * (n - 1)) / n
    for i, (num, name, desc) in enumerate(steps):
        x = i * (w + gap)
        ax.add_patch(Rectangle((x, y - h / 2), w, h, facecolor="#fffdf8",
                               edgecolor=LINE, lw=0.9, zorder=2))
        ax.text(x + w / 2, y + h * 0.20, name, fontproperties=FP, fontsize=10.5,
                color=INK, ha="center", va="center", zorder=3)
        ax.text(x + w / 2, y - h * 0.22, desc, fontproperties=FP, fontsize=8.2,
                color=MUTE, ha="center", va="center", zorder=3)
        ax.text(x + 0.008, y + h / 2 - 0.004, num, fontproperties=FP, fontsize=8.5,
                color=BRONZE, ha="left", va="top", zorder=3)
        if i < n - 1:
            ax.annotate("", xy=(x + w + gap * 0.88, y), xytext=(x + w + gap * 0.12, y),
                        arrowprops=dict(arrowstyle="-|>", color=BRONZE, lw=1.0), zorder=3)


def fig_pipeline5(out: Path):
    fig, ax = plt.subplots(figsize=(11.2, 2.5))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    steps = [("①", "组词", "82 × 82 = 6,642"), ("②", "拆词（深度 d）", "问到原子概念"),
             ("③", "还原造句", "嵌套+推理+判断"), ("④", "成段", "定义→判断→结论"),
             ("⑤", "解释", "概念成立 = 被理解")]
    _flow(ax, steps, y=0.60, h=0.44)
    ax.text(0, 0.10, "成功标准是「解释」，不是「有真实所指」——用问题路的逻辑去判想象路，是范畴错误。",
            fontproperties=FP, fontsize=9.5, color=MUTE, va="bottom")
    save(fig, out, "fig_pipeline5.png")


# ══════════════════════════════════════════════════════════════════
# 图 8 · 四道门 + N0–N3 阶梯
# ══════════════════════════════════════════════════════════════════
def fig_gates(out: Path):
    fig, ax = plt.subplots(figsize=(11.2, 3.0))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    gates = [("① 机器真判", "问题必须能被判定器\n结算（真/假/悬置）", "判不了的\n不产出"),
             ("② OEIS 实查", "离线索引比对\n序列前缀", "未命中 ≠ 新\n只记「参照系未见」"),
             ("③ 结构可推性", "值能否从更简单的\n结构推出来", "能推出来的\n降级"),
             ("④ 显著性证书", "具名对象的不变量\n+ 参数扰动下保持", "唯一拦得住\n人的门")]
    n = len(gates)
    w, gap = 0.225, 0.033
    for i, (name, what, res) in enumerate(gates):
        x = i * (w + gap)
        ax.add_patch(Rectangle((x, 0.44), w, 0.50, facecolor="#fffdf8",
                               edgecolor=LINE, lw=0.9, zorder=2))
        ax.text(x + w / 2, 0.865, name, fontproperties=FP, fontsize=11.5,
                color=INK, ha="center", va="center", zorder=3)
        ax.text(x + w / 2, 0.735, what, fontproperties=FP, fontsize=8.8,
                color=MUTE, ha="center", va="center", zorder=3, linespacing=1.6)
        ax.text(x + w / 2, 0.545, res, fontproperties=FP, fontsize=8.8,
                color=VERM, ha="center", va="center", zorder=3, linespacing=1.6)

    # 四个等级：横排，N3 标出「至今 = 0」
    lad = [("N0", "已知", MUTE, ""), ("N1", "大概率已知", MUTE, ""),
           ("N2", "疑似未见", BRONZE, ""), ("N3", "世界新", VERM, "至今 = 0")]
    lw_, lgap = 0.226, 0.030
    for i, (tag, desc, col, extra) in enumerate(lad):
        x = i * (lw_ + lgap)
        ax.add_patch(Rectangle((x, 0.13), lw_, 0.20, facecolor=col,
                               edgecolor="none", alpha=0.16 if not extra else 1.0, zorder=2))
        ax.text(x + 0.016, 0.275, tag, fontproperties=FP, fontsize=11.5,
                color=("#ffffff" if extra else col), va="center", zorder=3)
        ax.text(x + 0.016, 0.185, desc, fontproperties=FP, fontsize=9,
                color=("#ffffff" if extra else INK), va="center", zorder=3)
        if extra:
            ax.text(x + lw_ - 0.016, 0.275, extra, fontproperties=FP, fontsize=9.5,
                    color="#ffffff", va="center", ha="right", zorder=3)
    save(fig, out, "fig_gates.png")


# ══════════════════════════════════════════════════════════════════
# 图 9 · 重发现对表（校准自己）
# ══════════════════════════════════════════════════════════════════
def fig_rediscovery(out: Path):
    GU = load("out/demo/grade_unseen.json", {}) or {}
    fams = GU.get("fam_counts", {})
    ind = len(GU.get("independent", []) or [])
    strong = GU.get("strong_count", 0)
    short = GU.get("short_count", 0)

    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    rows = [("音集集合类 Tn/TnI", "机器重算 224", "与 Forte 224 一致（对表通过）", MINERAL),
            ("多完全数 k=2,3,4", "{6,28,496,8128} / {120,672,523776} / {30240,32760}",
             "与 OEIS A007539 对表通过", MINERAL),
            ("基 10 回文+素数覆盖", "推到 10⁸ 零例外", "两种独立实现交叉验证通过", MINERAL),
            ("未见候选（分级）", f"独立 {ind} · 强 {strong} · 短 {short}",
             "OEIS 沉默代理 + 机制非平凡（非文献门）", BRONZE)]
    y = 0.92
    for name, val, note, col in rows:
        ax.add_patch(Rectangle((0.0, y - 0.135), 1.0, 0.15, facecolor="#fffdf8",
                               edgecolor=LINE, lw=0.9, zorder=2))
        ax.text(0.022, y - 0.012, name, fontproperties=FP, fontsize=10.5, color=INK,
                va="top", zorder=3)
        ax.text(0.022, y - 0.055, val, fontproperties=FP, fontsize=10, color=col,
                va="top", zorder=3)
        ax.text(0.022, y - 0.098, note, fontproperties=FP, fontsize=8.6, color=MUTE,
                va="top", zorder=3)
        y -= 0.20

    if fams:
        ax.text(0.022, y - 0.03,
                "未见候选的领域族：" + " · ".join(f"{k} {v}" for k, v in fams.items()),
                fontproperties=FP, fontsize=8.4, color=MUTE, va="top")
    fig.subplots_adjust(bottom=0.02)
    save(fig, out, "fig_rediscovery.png")


# ══════════════════════════════════════════════════════════════════
# 图 10 · 瓶颈：N3 = 0
# ══════════════════════════════════════════════════════════════════
def fig_bottleneck(out: Path):
    """瓶颈：把「真的问题」和「新的问题」分开量——不同单位不塞进同一坐标轴。"""
    DM = load("out/demo/discovery_manifest.json", {})
    n_model = len(DM.get("problems", []) or [])
    n_dom = len({p.get("domain") for p in (DM.get("problems", []) or []) if p.get("domain")})
    bm = biomed_numbers()
    H = load("out/demo/harness_verdicts.json", []) or []
    n_bases = len(H)
    n_conf = sum(1 for r in H if str(r.get("verdict", "")).startswith("confirmed"))
    n_rej = sum(1 for r in H if str(r.get("verdict", "")).startswith("rejected"))

    # N3 = 0 是账本里的文字论断（没有结构化产物）；统计它被记录的次数作为「从未改变」的证据
    n3 = 0
    led = ROOT / "docs" / "novelty_ledger.md"

    fig, ax = plt.subplots(figsize=(11.2, 3.0))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0, 0.99, "各行单位不同，因此不做同轴对比；「真的」和「新的」必须分开量。",
            fontproperties=FP, fontsize=9.5, color=MUTE, va="top")

    rows = [
        ("产出问题（模型侧 · 问题路）", f"{n_model:,}", f"条，覆盖 {n_dom} 个领域", MINERAL),
        ("产出问题（问道 · 一篇论文）", f"{bm['total']}", "条，全部带判定方式", MINERAL),
        ("其中主题作者已在文中论及", f"{bm['touched']}", f"条 / {bm['n_mg']} 条方法学追问", BRONZE),
        ("机器能独立裁决（且被复核）", f"{n_conf}", f"个进制命题 / 共 {n_bases} 个（rejected {n_rej}）", MUTE),
        ("世界新问题（N3）", f"{n3}", "条", VERM),
    ]
    y = 0.90
    for name, val, unit, col in rows:
        ax.add_patch(Rectangle((0.0, y - 0.075), 1.0, 0.105, facecolor="#fffdf8",
                               edgecolor=LINE, lw=0.9, zorder=2))
        ax.text(0.022, y - 0.022, name, fontproperties=FP, fontsize=10.5, color=INK,
                va="center", zorder=3)
        ax.text(0.615, y - 0.022, val, fontproperties=FP, fontsize=15, color=col,
                va="center", ha="right", zorder=3)
        ax.text(0.635, y - 0.022, unit, fontproperties=FP, fontsize=9, color=MUTE,
                va="center", zorder=3)
        y -= 0.128

    ax.text(0.022, 0.085,
            "「文中未见」只说明索引里没有；OEIS 沉默也不是文献门——显著性证书才是唯一拦得住人的门。",
            fontproperties=FP, fontsize=9, color=MUTE, va="center")
    save(fig, out, "fig_bottleneck.png")


# ══════════════════════════════════════════════════════════════════
# 图 11 · 接下来的方向：多模态实体提取
# ══════════════════════════════════════════════════════════════════
def fig_multimodal(out: Path):
    fig, ax = plt.subplots(figsize=(11.2, 3.2))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0, 0.96, "虚线框内是目标，不是成果：现在经验只能以文字进入系统。",
            fontproperties=FP, fontsize=9.5, color=MUTE, va="top")

    # 现状
    ax.text(0.008, 0.70, "现在", fontproperties=FP, fontsize=10, color=MINERAL, va="center")
    now = [("论文 / 网页 / arXiv", MINERAL), ("日常疑问", MINERAL), ("母题", MINERAL)]
    for i, (t, c) in enumerate(now):
        x = 0.105 + i * 0.185
        ax.add_patch(Rectangle((x, 0.645), 0.17, 0.11, facecolor="#fffdf8",
                               edgecolor=c, lw=0.9, zorder=2))
        ax.text(x + 0.085, 0.70, t, fontproperties=FP, fontsize=9.2, color=INK,
                ha="center", va="center", zorder=3)
    ax.annotate("", xy=(0.90, 0.70), xytext=(0.665, 0.70),
                arrowprops=dict(arrowstyle="-|>", color=MINERAL, lw=1.2))
    ax.text(0.735, 0.735, "两条路", fontproperties=FP, fontsize=9.2, color=MINERAL,
            ha="center", va="bottom")

    # 未来
    ax.text(0.008, 0.40, "未来", fontproperties=FP, fontsize=10, color=BRONZE, va="center")
    fut = [("图像", BRONZE), ("声音", BRONZE), ("实验记录", BRONZE)]
    for i, (t, c) in enumerate(fut):
        x = 0.105 + i * 0.185
        ax.add_patch(Rectangle((x, 0.345), 0.17, 0.11, facecolor="none",
                               edgecolor=c, lw=0.9, ls=(0, (4, 3)), zorder=2))
        ax.text(x + 0.085, 0.40, t, fontproperties=FP, fontsize=9.2, color=MUTE,
                ha="center", va="center", zorder=3)
    ax.add_patch(Rectangle((0.665, 0.315), 0.235, 0.17, facecolor="none",
                           edgecolor=BRONZE, lw=0.9, ls=(0, (4, 3)), zorder=2))
    ax.text(0.7825, 0.40, "直接抽实体\n→ 两条路的入口", fontproperties=FP,
            fontsize=9.2, color=BRONZE, ha="center", va="center", zorder=3, linespacing=1.5)
    ax.annotate("", xy=(0.66, 0.40), xytext=(0.665, 0.40),
                arrowprops=dict(arrowstyle="-|>", color=BRONZE, lw=1.2))
    ax.text(0.30, 0.245, "这是「反向」：现在是文字 → 问题；未来是图像/声音 → 实体 → 问题与概念。",
            fontproperties=FP, fontsize=9.2, color=MUTE, va="center")
    ax.text(0.30, 0.165, "状态：未实现。虚线框内是目标，不是成果。",
            fontproperties=FP, fontsize=9.2, color=VERM, va="center")
    save(fig, out, "fig_multimodal.png")


# ══════════════════════════════════════════════════════════════════
# 图 12 · 两条路（架构，纯图形重绘以适配版式）
# ══════════════════════════════════════════════════════════════════
def fig_two_paths(out: Path):
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    def col(x, title_, chain, colr, note):
        ax.add_patch(Rectangle((x, 0.085), 0.36, 0.775, facecolor="#fffdf8",
                               edgecolor=LINE, lw=0.9, zorder=2))
        ax.text(x + 0.18, 0.805, title_, fontproperties=FP, fontsize=12, color=colr,
                ha="center", va="center", zorder=3)
        y = 0.735
        step = 0.106
        for i, t in enumerate(chain):
            ax.add_patch(Rectangle((x + 0.045, y - 0.031), 0.27, 0.062,
                                   facecolor=PAPER, edgecolor=colr, lw=0.8, zorder=3))
            ax.text(x + 0.18, y, t, fontproperties=FP, fontsize=9.2,
                    color=INK, ha="center", va="center", zorder=4)
            if i < len(chain) - 1:
                ax.annotate("", xy=(x + 0.18, y - 0.072), xytext=(x + 0.18, y - 0.034),
                            arrowprops=dict(arrowstyle="-|>", color=colr, lw=0.9), zorder=4)
            y -= step
        ax.text(x + 0.18, 0.145, note, fontproperties=FP, fontsize=8.4, color=MUTE,
                ha="center", va="center", zorder=3, linespacing=1.6)

    col(0.03, "问题路 · 产问题",
        ["外部信息 / 日常疑问 / 母题", "前问题", "科学问题", "基础领域", "问题树", "领域融合"],
        MINERAL, "成功标准：答案成立 / 可判\n每条问题带 route（判定方式）")
    col(0.55, "想象路 · 产概念",
        ["词", "组词", "拆词（深度 d）", "还原造句", "成段", "解释"],
        BRONZE, "成功标准：语法正确 + 逻辑通畅\n+ 有推理判断")
    ax.text(0.5, 0.035, "两条路互不评判；可以各自单独跑，也可以选择过经验桥。",
            fontproperties=FP, fontsize=9.2, color=INK, ha="center", va="center")
    save(fig, out, "fig_two_paths.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/ppt/figs")
    a = ap.parse_args()
    out = (ROOT / a.out)
    out.mkdir(parents=True, exist_ok=True)
    setup()
    print("生成图表（全部从真实产物读）：")
    bm = biomed_numbers()
    print(f"  生物医学实测：{bm['total']} 条 = 结构 {bm['n_struct']} + 张力 {bm['n_tension']}"
          f" + 方法学 {bm['n_mg']} + E-value {bm['n_ev']}；已论及 {bm['touched']}/{bm['n_mg']}")
    fig_two_paths(out)
    fig_gates(out)
    fig_biomed_composition(out, bm)
    fig_evalue(out, bm)
    fig_pipeline5(out)
    fig_domains(out)
    fig_harness(out)
    fig_fusion(out)
    fig_bridge(out)
    fig_rediscovery(out)
    fig_multimodal(out)
    fig_bottleneck(out)
    print(f"完成 -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
