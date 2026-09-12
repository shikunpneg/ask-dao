# -*- coding: utf-8 -*-
"""make_deck.py — 把 deck_spec 渲成两样东西：可编辑的 .pptx 与线上 HTML/PDF。

OJO 视觉 DNA（先立规矩，再产出）：
  完成度 粗粝（纸面噪点 3.5%，不做工业级平滑）· 密度 极疏（大留白）· 重量 克制 · 严肃度 学术
  色彩语义：宣纸底 #f6f2e9 · 墨 #16191d · 石青 #2f6b6b（已实测/可复用）·
            朱砂 #b03a2e（机器算出 / 需注意）· 青铜 #9a7b3f（编号与标签）
  材质：1px 细线 rgba(22,25,29,.14)、0–2px 圆角、无发光、无渐变、无中性灰蓝
  排版：中文标题用宋体，正文无衬线；比例 1.333；每页一个主张，证据在其下
用法：python tools/make_deck.py [--no-pptx] [--no-png] [--no-pdf]
"""
from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deck_spec import SLIDES  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "ppt"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
W, H = 1280, 720
INK, PAPER, MINERAL, VERM, BRONZE = "#16191d", "#f6f2e9", "#2f6b6b", "#b03a2e", "#9a7b3f"
LINE = "rgba(22,25,29,.14)"


# ── 文本标记：**粗** 与 `code` ────────────────────────────────────────
def inline(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s.replace("\n", "<br>")


def plain(s: str) -> str:
    return s.replace("**", "").replace("`", "")


# ── HTML 版 ──────────────────────────────────────────────────────────
CSS = f"""
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;background:#e9e4da;}}
.slide{{position:relative;width:{W}px;height:{H}px;background:{PAPER};overflow:hidden;
  font-family:"Microsoft YaHei","PingFang SC",system-ui,sans-serif;color:{INK};
  padding:64px 76px 58px;margin:0 auto;page-break-after:always;}}
.slide:before{{content:"";position:absolute;inset:0;pointer-events:none;opacity:.035;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3'/></filter><rect width='120' height='120' filter='url(%23n)'/></svg>");}}
.kicker{{font-size:12.5px;letter-spacing:.22em;color:{BRONZE};font-weight:700;margin-bottom:14px;}}
h1{{font-family:"Source Han Serif SC","Songti SC",SimSun,serif;font-size:46px;line-height:1.28;
  margin:0 0 18px;letter-spacing:.02em;white-space:pre-line;}}
h2{{font-family:"Source Han Serif SC","Songti SC",SimSun,serif;font-size:34px;line-height:1.3;
  margin:0 0 16px;letter-spacing:.02em;}}
.lead{{font-size:15.5px;line-height:1.95;color:#4a4f57;max-width:1010px;margin:0 0 26px;}}
.lead strong{{color:{MINERAL};}}
ul{{margin:0;padding:0;list-style:none;}}
li{{margin:0 0 15px;padding-left:20px;position:relative;font-size:15px;line-height:1.85;}}
li:before{{content:"";position:absolute;left:0;top:11px;width:9px;height:1px;background:{BRONZE};}}
li b{{font-family:"Source Han Serif SC","Songti SC",SimSun,serif;font-size:16px;
  display:block;margin-bottom:3px;letter-spacing:.03em;}}
code{{font-family:Consolas,monospace;font-size:13.5px;background:rgba(22,25,29,.05);
  padding:1px 5px;border-radius:2px;}}
strong{{color:{INK};}}
table{{width:100%;border-collapse:collapse;font-size:13.5px;}}
th,td{{text-align:left;padding:9px 12px;border-bottom:1px solid {LINE};vertical-align:top;line-height:1.7;}}
th{{font-size:12.5px;letter-spacing:.08em;color:{BRONZE};border-bottom:1px solid rgba(22,25,29,.28);
  background:rgba(255,255,255,.5);}}
td:first-child{{color:{INK};}}
.num{{font-variant-numeric:tabular-nums;}}
.note{{position:absolute;left:76px;right:76px;bottom:52px;font-size:12.5px;line-height:1.75;
  color:#6b7078;border-top:1px solid {LINE};padding-top:12px;}}
.note strong{{color:{VERM};}}
.pnum{{position:absolute;right:76px;bottom:22px;font-size:11.5px;color:{BRONZE};letter-spacing:.1em;}}
.cover{{padding-top:150px;}}
.cover h1{{font-size:56px;}}
.cover .logo{{position:absolute;right:76px;top:104px;width:158px;opacity:.92;}}
.cover .foot{{position:absolute;left:76px;bottom:60px;font-size:14px;color:{MINERAL};
  font-family:"Source Han Serif SC",SimSun,serif;letter-spacing:.04em;}}
.steps{{display:grid;grid-template-columns:1fr 1fr;gap:16px 34px;}}
.step{{border-left:1px solid {LINE};padding-left:16px;}}
.step h4{{margin:0 0 6px;font-size:12.5px;letter-spacing:.16em;color:{BRONZE};font-weight:700;}}
.step p{{margin:0;font-size:13.5px;line-height:1.8;color:#3b4046;}}
.links{{columns:2;column-gap:44px;font-size:14px;line-height:2.1;}}
.links a{{color:{MINERAL};text-decoration:none;border-bottom:1px solid rgba(47,107,107,.35);}}
.links b{{font-family:SimSun,serif;color:{INK};display:inline-block;min-width:150px;}}
/* ── 图片优先版式：汇报以「图 + 解释」为主 ── */
.figrow{{display:flex;gap:32px;align-items:flex-start;}}
.figrow>figure{{margin:0;flex:0 0 53%;}}
.figrow>figure img{{width:100%;max-height:372px;object-fit:contain;display:block;border:1px solid {LINE};background:#fffdf8;}}
.figrow>figure figcaption{{font-size:11.5px;color:#6b7078;margin-top:9px;line-height:1.65;}}
.figrow>ul{{flex:1 1 auto;}}
.figgrid{{display:grid;gap:20px;}}
.figgrid.g2{{grid-template-columns:1fr 1fr;}}
.figgrid.g4{{grid-template-columns:repeat(4,1fr);}}
.figgrid figure{{margin:0;}}
.figgrid img{{width:100%;max-height:250px;object-fit:contain;display:block;border:1px solid {LINE};background:#fffdf8;}}
.figgrid figcaption{{font-size:11px;color:#6b7078;margin-top:7px;line-height:1.55;}}
.figfull{{margin:0;}}
.figfull img{{width:100%;max-height:376px;object-fit:contain;display:block;}}
.figfull figcaption{{font-size:11.5px;color:#6b7078;margin-top:9px;line-height:1.65;}}
/* ── 结果展示：原句清单（一页尽量多放真实产出） ── */
.qlist{{columns:2;column-gap:38px;margin:0;padding:0;list-style:none;}}
.qlist li{{break-inside:avoid;margin:0 0 10px;padding-left:0;font-size:11px;line-height:1.66;
  color:#2b3036;}}
.qlist li .tag{{display:inline-block;font-size:9.5px;font-weight:700;color:{VERM};
  letter-spacing:.04em;margin-right:6px;vertical-align:1px;}}
.qlist li .src{{display:block;font-size:9.5px;color:#8a8f96;margin-top:2px;line-height:1.5;}}
/* ── 结果展示：数字榜 ── */
.statrow{{display:flex;gap:26px;margin:0 0 24px;}}
.stat{{flex:1;border-top:2px solid {BRONZE};padding-top:10px;}}
.stat b{{display:block;font-family:"Source Han Serif SC",SimSun,serif;font-size:30px;
  line-height:1.1;color:{MINERAL};letter-spacing:.01em;}}
.stat span{{display:block;font-size:11.5px;color:#6b7078;margin-top:5px;line-height:1.6;}}
.stat.verm b{{color:{VERM};}}
@media print{{@page{{size:{W}px {H}px;margin:0}}html,body{{background:{PAPER}}}
  .slide{{margin:0;box-shadow:none}}
  .slide:before{{content:none}}   /* 噪点滤镜打印时会被逐页栅格化，PDF 会爆到几十 MB */}}
"""


def slide_html(s: dict, idx: int, total: int) -> str:
    kind = s["kind"]
    body = [f'<div class="kicker">{html.escape(s.get("kicker", ""))}</div>']
    tag = "h1" if kind == "cover" else "h2"
    body.append(f'<{tag}>{html.escape(s["title"])}</{tag}>')
    if s.get("lead"):
        body.append(f'<p class="lead">{inline(s["lead"])}</p>')

    if kind == "bullets":
        items = "".join(f'<li><b>{html.escape(k)}</b>{inline(v)}</li>' for k, v in s["bullets"])
        body.append(f"<ul>{items}</ul>")
    elif kind == "table":
        t = s["table"]
        head = "".join(f"<th>{html.escape(h)}</th>" for h in t["head"])
        rows = "".join("<tr>" + "".join(
            f'<td class="{"num" if i and len(c) < 8 else ""}">{inline(c)}</td>'
            for i, c in enumerate(r)) + "</tr>" for r in t["rows"])
        body.append(f"<table><tr>{head}</tr>{rows}</table>")
    elif kind == "chain":
        steps = "".join(f'<div class="step"><h4>{html.escape(k)}</h4><p>{inline(v)}</p></div>'
                        for k, v in s["steps"])
        body.append(f'<div class="steps">{steps}</div>')
    elif kind == "figure":
        f = s["figure"]
        cap = f'<figcaption>{inline(f["caption"])}</figcaption>' if f.get("caption") else ""
        side = ""
        if s.get("bullets"):
            items = "".join(f'<li><b>{html.escape(k)}</b>{inline(v)}</li>' for k, v in s["bullets"])
            side = f"<ul>{items}</ul>"
        body.append(f'<div class="figrow"><figure><img src="{html.escape(f["src"])}" alt="">'
                    f'{cap}</figure>{side}</div>')
    elif kind == "figfull":
        f = s["figure"]
        cap = f'<figcaption>{inline(f["caption"])}</figcaption>' if f.get("caption") else ""
        body.append(f'<figure class="figfull"><img src="{html.escape(f["src"])}" alt="">'
                    f'{cap}</figure>')
    elif kind == "figgrid":
        cols = s.get("cols", 4)
        figs = "".join(
            f'<figure><img src="{html.escape(g["src"])}" alt="">'
            f'<figcaption>{inline(g.get("caption", ""))}</figcaption></figure>'
            for g in s["figures"])
        body.append(f'<div class="figgrid g{cols}">{figs}</div>')
    elif kind == "qlist":
        items = "".join(
            f'<li><span class="tag">{html.escape(t)}</span>{inline(txt)}'
            + (f'<span class="src">{inline(src)}</span>' if src else "")
            + "</li>"
            for t, txt, src in s["items"])
        body.append(f'<ul class="qlist">{items}</ul>')
    elif kind == "stats":
        stats = "".join(
            f'<div class="stat{" verm" if v else ""}"><b>{html.escape(str(n))}</b>'
            f'<span>{inline(lbl)}</span></div>'
            for n, lbl, v in s["stats"])
        body.append(f'<div class="statrow">{stats}</div>')
        if s.get("bullets"):
            items = "".join(f'<li><b>{html.escape(k)}</b>{inline(v)}</li>' for k, v in s["bullets"])
            body.append(f"<ul>{items}</ul>")
        if s.get("figure"):
            f = s["figure"]
            cap = f'<figcaption>{inline(f["caption"])}</figcaption>' if f.get("caption") else ""
            body.append(f'<figure class="figfull"><img src="{html.escape(f["src"])}" alt="">'
                        f'{cap}</figure>')
    elif kind == "cover":
        if s.get("figure"):
            body.append(f'<img class="logo" src="{html.escape(s["figure"]["src"])}" alt="">')
        body.append(f'<div class="foot">{html.escape(s.get("foot", ""))}</div>')
    elif kind == "end":
        links = "".join(f'<div><b>{html.escape(k)}</b><a href="{html.escape(v)}">{html.escape(v)}</a></div>'
                        for k, v in s["links"])
        body.append(f'<div class="links">{links}</div>')
        body.append(f'<div class="foot">{html.escape(s.get("foot", ""))}</div>')

    if s.get("note"):
        body.append(f'<div class="note">{inline(s["note"])}</div>')
    cls = "slide cover" if kind in ("cover", "end") else "slide"
    return f'<section class="{cls}">' + "".join(body) + \
           f'<div class="pnum">{idx:02d} / {total:02d}</div></section>'


def build_html() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    n = len(SLIDES)
    doc = (f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
           f'<title>问道知识发现系统 · 生物医学领域的发现</title>'
           f'<style>{CSS}</style></head><body>'
           + "".join(slide_html(s, i + 1, n) for i, s in enumerate(SLIDES))
           + "</body></html>")
    p = OUT / "index.html"
    p.write_text(doc, encoding="utf-8")
    print(f"  HTML: {p.relative_to(ROOT)}  {len(doc):,} 字符  {n} 页")
    return p


def edge(args: list[str], timeout=420):
    return subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
                           "--hide-scrollbars", "--force-device-scale-factor=1", *args],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout)


def build_slides_png() -> None:
    """逐页截图（每页单独隐藏其它页，避免超长窗口不稳）。"""
    import numpy as np
    from PIL import Image
    page = OUT / "index.html"
    src = page.read_text(encoding="utf-8")
    n = len(SLIDES)
    for i in range(n):
        inj = (f'<style>.slide{{display:none}}.slide:nth-of-type({i+1}){{display:block;margin:0}}</style>')
        tmp = OUT / f"_p{i+1}.html"
        tmp.write_text(src.replace("</head>", inj + "</head>"), encoding="utf-8")
        png = OUT / f"slide-{i+1:02d}.png"
        edge([f"--window-size={W},{H}", f"--screenshot={png}", tmp.as_uri()])
        tmp.unlink(missing_ok=True)
        a = np.asarray(Image.open(png).convert("L"), dtype=np.int16)
        if a.shape[1] != W or a.shape[0] < H - 4:
            print(f"    ⚠ slide-{i+1:02d}.png 尺寸 {a.shape[1]}x{a.shape[0]}（期望 {W}x{H}）")
    print(f"  PNG: {n} 页 -> {OUT.relative_to(ROOT)}/slide-XX.png")


def build_pdf(name: str = "ask-dao-biomed-deck") -> None:
    pdf = OUT / f"{name}.pdf"
    edge([f"--print-to-pdf={pdf}", "--no-pdf-header-footer", (OUT / "index.html").as_uri()])
    size = pdf.stat().st_size if pdf.exists() else 0
    print(f"  PDF: {pdf.relative_to(ROOT)}  {size:,} 字节")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-pptx", action="store_true")
    ap.add_argument("--no-png", action="store_true")
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("--name", default="ask-dao-biomed-deck",
                    help="输出文件名（不含扩展名）；被 PowerPoint 占用时可换名构建")
    a = ap.parse_args()
    print("生成：")
    build_html()
    if not a.no_png:
        build_slides_png()
    if not a.no_pdf:
        build_pdf(name=a.name)
    if not a.no_pptx:
        from make_pptx import build_pptx
        build_pptx(SLIDES, OUT / f"{a.name}.pptx")
