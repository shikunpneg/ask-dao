# -*- coding: utf-8 -*-
"""tools/design_ink.py — 墨纸设计系统（供架构图 / 问题生成树共用）

参考 OJO Design Skills（记忆与 E:/ojo 的 theme-guide）：材质隐喻、粗粝不磨平、极疏留白、
0–2px 圆角、无 drop shadow / 无高饱和发光 / 无霓虹渐变、3–5% 纸面噪点、有质感的宋体。
配色全部有理由：宣纸、墨、朱砂（已证）、石青（数值验证）、青铜（悬置/线）。
"""
from pathlib import Path

PAPER = "#f6f2e9"        # 宣纸底
PAPER_2 = "#efe9dc"      # 浅一档（分区）
INK = "#16191d"          # 墨
INK_SOFT = "#454a51"     # 淡墨
DIM = "#7c8188"          # 说明文字
HAIR = "#cdc6b6"         # 细分隔线
VERMILION = "#b03a2e"    # 朱砂：已证 / 假（判定为真或假，都是"落了锤"）
VERMILION_SOFT = "#d9a79f"
TEAL = "#2f6b6b"         # 石青：数值/有限验证
BRONZE = "#9a7b3f"       # 青铜：悬置、开放、操作标签
PAPER_DARK = "#20242a"   # 深色版（网站首屏可能用）

SERIF = '"Songti SC","STSongti-SC","SimSun","Noto Serif CJK SC","Source Han Serif SC",serif'
MONO = '"JetBrains Mono","Cascadia Mono","Consolas",monospace'


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def q(s):
    """属性值：用单引号包裹，内部保留双引号（字体栈里有 "Songti SC" 这种带空格的名字，
    不能塞进无引号属性值，也不能把引号转义成 &quot; 再放进无引号值里——那会是非法的 XML）。"""
    return "'" + str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") + "'"


def svg_open(w, h, bg=PAPER, pad_noise=True):
    """开头: 画布 + 纸面噪点(3.5%) + 极细纹理线。OJO 要求"粗粝", 不要工业级平滑。"""
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" '
         f'height="{h}" font-family={q(SERIF)}>']
    o.append("<defs>")
    o.append('<filter id="paper" x="0" y="0" width="100%" height="100%">'
             '<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" '
             'stitchTiles="stitch" result="n"/>'
             '<feColorMatrix in="n" type="saturate" values="0" result="g"/>'
             '<feComponentTransfer in="g"><feFuncA type="linear" slope="0.055" intercept="0"/>'
             '</feComponentTransfer></filter>')
    o.append('<marker id="tick" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" '
             'markerHeight="6" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="' + DIM + '"/></marker>')
    o.append("</defs>")
    o.append(f'<rect width="{w}" height="{h}" fill="{bg}"/>')
    if pad_noise:
        o.append(f'<rect width="{w}" height="{h}" filter="url(#paper)" opacity="0.5"/>')
    return o


def svg_close(o):
    o.append("</svg>")
    return "\n".join(o)


def title_block(o, x, y, cn_title, en_label, note=None):
    """标题: 宋体大字 + 朱砂小方印 + 细横线（不用加粗黑体，不用图标）。"""
    o.append(f'<rect x="{x}" y="{y - 15}" width="4" height="19" fill="{VERMILION}"/>')
    o.append(f'<text x="{x + 14}" y="{y}" font-size="21" fill="{INK}" letter-spacing="1.5">'
             f'{esc(cn_title)}</text>')
    if en_label:
        o.append(f'<text x="{x + 14}" y="{y + 18}" font-size="10.5" fill="{DIM}" '
                 f'font-family={q(MONO)} letter-spacing="2.6">{esc(en_label.upper())}</text>')
    o.append(f'<line x1="{x}" y1="{y + 30}" x2="{x + 1180}" y2="{y + 30}" stroke="{HAIR}" '
             f'stroke-width="1"/>')
    if note:
        o.append(f'<text x="{x + 1180}" y="{y + 18}" text-anchor="end" font-size="11" '
                 f'fill="{DIM}">{esc(note)}</text>')


def status_style(status):
    """真实 status 文本 → (颜色, 是否虚线)。判定状态只来自数据, 不在这里臆造。"""
    s = str(status)
    if s.startswith("真") or s.startswith("假"):
        return VERMILION, False
    if "有限验证" in s or "数值" in s:
        return TEAL, False
    if "悬置" in s or "开放" in s:
        return BRONZE, True
    return INK_SOFT, False


def wrap_cn(text, per_line, max_lines=2):
    """中文按字数折行（宋体等宽感），超长截断加省略号。"""
    text = str(text)
    lines = [text[i:i + per_line] for i in range(0, len(text), per_line)]
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][:max(1, per_line - 1)] + "…"
    return lines


def node(o, x, y, w, h, sid, statement, status, route=None, root=False):
    """问题节点: 2px 圆角 + 1px 墨线 + 左侧朱砂/石青/青铜色条（状态来自真实数据）。"""
    color, dashed = status_style(status)
    dash = ' stroke-dasharray="4 3"' if dashed else ""
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2" fill="{PAPER}" '
             f'stroke="{INK_SOFT if root else HAIR}" stroke-width="{1.4 if root else 1}"{dash}/>')
    o.append(f'<rect x="{x}" y="{y}" width="3" height="{h}" fill="{color}"/>')
    o.append(f'<text x="{x + 11}" y="{y + 15}" font-size="10.5" fill="{DIM}" '
             f'font-family={q(MONO)} letter-spacing="0.6">{esc(sid)}</text>')
    lines = wrap_cn(statement, 15, 2)
    for i, ln in enumerate(lines):
        o.append(f'<text x="{x + 11}" y="{y + 32 + i * 15}" font-size="12.5" fill="{INK}">'
                 f'{esc(ln)}</text>')
    bl = status if not route else f"{status} · {route}"
    o.append(f'<text x="{x + 11}" y="{y + h - 8}" font-size="10" fill="{color}">'
             f'{esc(str(bl)[:26])}</text>')


def edge(o, x1, y1, x2, y2, label=None, color=BRONZE, dash=None, curve=0.5, label_side="left"):
    """生成关系: 细线 + 小箭头 + 边上写"真实操作"（如 加约束:两数不同）。"""
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    cx = mx + (0 if abs(y2 - y1) > abs(x2 - x1) else 0)
    d = f"M{x1},{y1} C{cx},{y1} {x2},{my} {x2},{y2}"
    da = f' stroke-dasharray="{dash}"' if dash else ""
    o.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1"{da} '
             f'marker-end="url(#tick)"/>')
    if label:
        lx = mx + (6 if label_side == "right" else -6)
        anchor = "start" if label_side == "right" else "end"
        ly = (y1 + y2) / 2
        o.append(f'<text x="{lx}" y="{ly - 4}" text-anchor="{anchor}" font-size="10.5" '
                 f'fill="{color}">{esc(label)}</text>')
    return d


def caption(o, x, y, text, size=10.5, color=DIM, mono=False):
    fam = f' font-family={q(MONO)}' if mono else ""
    o.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}"{fam}>{esc(text)}</text>')


def legend(o, x, y, items):
    """图例: 只用真实状态词, 不发明新类别。"""
    cx = x
    for label, color, dashed in items:
        o.append(f'<line x1="{cx}" y1="{y - 4}" x2="{cx + 18}" y2="{y - 4}" stroke="{color}" '
                 f'stroke-width="3"' + (' stroke-dasharray="4 3"' if dashed else "") + "/>")
        o.append(f'<text x="{cx + 24}" y="{y}" font-size="11" fill="{INK_SOFT}">{esc(label)}</text>')
        cx += 30 + len(label) * 12
    return cx


def save(o, *paths):
    s = svg_close(o)
    for p in paths:
        p = Path(p)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(s, encoding="utf-8")
    return s

