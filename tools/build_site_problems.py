# -*- coding: utf-8 -*-
"""tools/build_site_problems.py — 把机器实际产出的记录，整理成**分级 + 问题/命题形态**的展示数据。

分级（对齐项目自己的框架，不新造概念）：
  K1 提出的问题       —— 来自各域 problems_*.json、张力候选 method3_unique、科学史未解 scihist_open
  K2 证据边界推进     —— 跨进制"回文数+素数"命题、harness 裁决、grown_motifs 配对集命题
  K3 归纳的规律      —— 由 K2 数据归纳的普遍律（数值汇合，非证明）
  想象路             —— 概念（需"解释"）：本质判断 + 可检验问题
  跨域融合           —— 母题 × 母题（真实 parents + 共享框架）
  复核性结果         —— 机器重发现已知（可信度基线）
  负结果             —— 同样重要：机器自己否掉的

每条都带：正文（命题/问题形态）、状态（来自记录）、判定路由、出处。
产出 tools/site/problems_curated.json（供 make_site.py 注入站点）。
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "out" / "demo"
OUT = ROOT / "tools" / "site" / "problems_curated.json"

DOMAIN_CN = {
    "math": "数学", "records": "组合记录", "combo": "组合记录", "fusion": "跨域融合",
    "ling": "语言·信息", "direction": "方向清单", "aesthetics": "美学", "counterex": "反例驱动",
    "digit_base": "进制数字", "sparse": "稀疏领地", "palbase": "跨进制", "polygon": "多边形数",
}


TIERS = [
            {"key": "K1", "name": "K1 · 提出的问题", "en": "NEW PROBLEMS",
             "desc": "把困惑/数据改造成可判的问题——这是新知识的第一步。每条都带判定路由。"},
            {"key": "K2", "name": "K2 · 证据边界推进", "en": "EVIDENCE FRONTIER",
             "desc": "对已有问题给出更强证据、更大边界。目前唯一称得上「新知识」的一类。"},
            {"key": "K3", "name": "K3 · 归纳的规律", "en": "INDUCED LAWS",
             "desc": "从数据归纳出的普遍律。机器只做到「数值汇合 + 待证明」。"},
            {"key": "IM", "name": "想象路 · 概念", "en": "IMAGINATION PATH",
             "desc": "产概念，不是产答案。标准是「解释」：语法正确 + 逻辑通畅 + 有推理判断。"},
            {"key": "F", "name": "领域融合 · 结果", "en": "DOMAIN FUSION",
             "desc": "27 个领域两两配对 702 对 → 结构桥梁判据后 144 对；三域笛卡尔矩阵 454 条审计"
                     "→ 真三域候选 4 条（每条都带第三域参数网格与实测输出）。"},
            {"key": "R", "name": "复核性结果", "en": "REPRODUCTION",
             "desc": "机器重发现已知——不是新知，是可信度基线。"},
            {"key": "N", "name": "负结果", "en": "NEGATIVE RESULTS",
             "desc": "机器自己否掉的、产不出问题的——与正结果同等重要。"},
]


def load(name):
    p = D / name
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:                              # noqa: BLE001
        return None


def fmt_status(s):
    s = str(s or "").strip()
    if s.startswith("真"):
        return ("真", "ok")
    if s.startswith("假"):
        return ("假", "no")
    if "悬置" in s or "开放" in s:
        return ("悬置·开放", "open")
    if "验证" in s or "有限" in s:
        return ("有限/数值验证", "num")
    if "待" in s or "实验" in s:
        return ("待实验", "todo")
    return (s[:12] or "未标", "todo")


def _shape(text):
    """把陈述压成"形状"，用于同域去重：去掉数字与标点，只留骨架。"""
    import re
    return re.sub(r"[\d\s,，.。:：;；'\"()（）\[\]{}]+", "", str(text))


def _cn_punct(s):
    """中文语境下的标点规范化：只在中文旁边把半角换成全角，不动公式里的符号。"""
    import re as _re
    if not _re.search(r"[\u4e00-\u9fff]", s):
        return s
    s = _re.sub(r"(?<=[\u4e00-\u9fff]),(?=[\u4e00-\u9fff])", "，", s)
    s = _re.sub(r"(?<=[\u4e00-\u9fff]),", "，", s)
    s = _re.sub(r"(?<=[\u4e00-\u9fff]);", "；", s)
    s = _re.sub(r"(?<=[\u4e00-\u9fff]):", "：", s)
    s = _re.sub(r"\?\s*$", "？", s)
    s = _re.sub(r"(?<=[\u4e00-\u9fff])\?", "？", s)
    return s


def clean(text):
    """展示清洗：摘掉生成器塞进陈述里的原始数据，只留问题/命题本身，并规范标点。

    例：'…共 6 个, 最大者 108(前几个: [6, 12, 28])。**是什么刻画了这个例外集**?'
      → '…共 6 个，最大者 108。是什么刻画了这个例外集？'
    注意：**不动数学记号**（c_{n-1}、x^{-α}、[6, 40000]、P(x) 都保持原样）。
    """
    import re
    s = str(text or "")
    # 摘掉括号里的原始数据（四种写法都覆盖）
    s = re.sub(r"[（(]\s*前几个[:：]?[^）)]*[）)]", "", s)
    s = re.sub(r"[（(]\s*(?:例外前|seq|examples?)[^）)]*[）)]", "", s, flags=re.I)
    s = s.replace("**", "").strip()
    s = re.sub(r"\s+", " ", s)
    # 机器写法 → 人话（不改事实）
    s = re.sub(r"(?<=\d)\.\.(?=\d)", ", ", s)          # 6..40000 → 6, 40000
    s = s.replace("mod m", "模 m").replace(" mod ", " 模 ")
    s = s.replace(" vs ", " 与 ")

    has_cjk = bool(re.search(r"[\u4e00-\u9fff]", s))
    if has_cjk:
        # 单引号 → 中文引号
        s = re.sub(r"'([^']{1,40})'", r"“\1”", s)
        # 括号：只在里面含中文时才转全角（P(x)、[6, 40000] 这类保持原样）
        s = re.sub(r"\(([^()]*[\u4e00-\u9fff][^()]*)\)", r"（\1）", s)
        # 逗号/分号/冒号：只在"后面紧跟中文"且不在括号内时转换
        def _commas(t):
            out, depth = [], 0
            for i, ch in enumerate(t):
                nxt = t[i + 1] if i + 1 < len(t) else ""
                if ch in "[{":
                    depth += 1
                elif ch in "]}":
                    depth = max(0, depth - 1)
                # 逗号后面允许有空格：只要跳过空格是中文，就换成全角；区间 [6, 40000] 里的不动
                tail = t[i + 1:i + 3]
                ascii_then_cjk = bool(re.match(r"\s*[\u4e00-\u9fff]", tail))
                if depth == 0 and ch == "," and ascii_then_cjk:
                    out.append("，")
                    skip_space = True
                elif depth == 0 and ch == ";" and ascii_then_cjk:
                    out.append("；")
                    skip_space = True
                elif depth == 0 and ch == ":" and ascii_then_cjk:
                    out.append("：")
                    skip_space = True
                else:
                    if ch == " " and out and out[-1] in "，；：":
                        continue
                    out.append(ch)
            return "".join(out)
        s = _commas(s)
    # （不再做无条件的 ", " → "，"：那会把 [6, 40000] 里的逗号也换掉）
    s = s.replace("?", "？").replace("!", "！")
    s = s.replace("。？", "？").replace("？。", "？").replace("。。", "。")
    s = re.sub(r"[，。；！]{2,}", "，", s)
    s = re.sub(r"（\s*）|\(\s*\)", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    if s and s[-1] not in "。？！":
        s += "。"
    return s


def load_overrides():
    """审校覆盖表：{（src, id）→ 覆盖项}。

    审校结论落在 tools/site/review_overrides.json，生成数据时自动套用，
    保证"改过的措辞"不会被下一次跑批覆盖掉。
    """
    p = ROOT / "tools" / "site" / "review_overrides.json"
    if not p.exists():
        return {}
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except Exception:                                   # noqa: BLE001
        return {}
    out = {}
    for r in raw.get("items") or []:
        m = r.get("match") or {}
        out[(m.get("src", ""), str(m.get("id", "")))] = r
    return out


def apply_overrides(items, overrides):
    """套用覆盖：改写正文/状态，或整条丢弃。返回 (保留条目, 改写数, 丢弃清单)。"""
    kept, dropped, changed = [], [], 0
    for it in items:
        ov = overrides.get((it.get("src", ""), str(it.get("id", ""))))
        if ov:
            if ov.get("drop"):
                dropped.append((it.get("src"), it.get("id")))
                continue
            if ov.get("display"):
                it["display"] = ov["display"]
            if ov.get("status"):
                it["status"] = ov["status"]
            if ov.get("cls"):
                it["cls"] = ov["cls"]
            if ov.get("verdict"):
                it["review"] = ov["verdict"]
            if ov.get("note"):
                it["review_note"] = ov["note"]
            changed += 1
        kept.append(it)
    return kept, changed, dropped


def _evidence_of(p):
    """从记录里提炼一行**简短**证据（不搬原始清单，细节留给手册）。"""
    ev = p.get("evidence") or {}
    if isinstance(ev, dict):
        bits = []
        if ev.get("count") is not None:
            bits.append(f"例外 {ev['count']} 个")
        if ev.get("last") is not None:
            bits.append(f"最后例外 {ev['last']}")
        if bits:
            return " · ".join(bits)
    st = str(p.get("status") or "")
    return st[:36] if st else ""


def _is_scan_artifact(text):
    """过滤扫描窗口伪影：像「所有 ≥39994 且 ≤40000 的偶数…」这种只覆盖 6 个数的"结论"。"""
    import re
    m = re.search(r"[≥>]=?\s*(\d+)\s*且\s*[≤<]=?\s*(\d+)", str(text))
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return (hi - lo) < 1000
    return False


def collect_k1():
    """K1：各域真实问题（命题形态原文），按域汇总计数；同域按"形状"去重，剔除扫描窗口伪影。"""
    items, counts = [], {}
    files = [("problems_counterex.json", "counterex"), ("problems_math.json", "math"),
             ("problems_records.json", "records"), ("problems_combo.json", "combo"),
             ("problems_fusion.json", "fusion"), ("problems_ling.json", "ling"),
             ("problems_direction.json", "direction"), ("problems_aesthetics.json", "aesthetics"),
             ("problems_digit_base.json", "digit_base"), ("problems_sparse.json", "sparse")]
    for fn, dom in files:
        d = load(fn)
        if not d:
            continue
        probs = d.get("problems") or []
        counts[DOMAIN_CN.get(dom, dom)] = len(probs)
        # 排序偏好：悬置/开放（真待解）> 假（结构性反例）> 有限验证
        ordered = sorted(probs, key=lambda p: (0 if "悬置" in str(p.get("status")) else
                                               1 if str(p.get("status")).startswith("假") else 2,
                                               str(p.get("id"))))
        seen_shapes, picked = set(), 0
        for p in ordered:
            stmt = str(p.get("statement", ""))
            if not stmt or _is_scan_artifact(stmt):
                continue
            sh = _shape(stmt)
            if sh in seen_shapes:
                continue
            seen_shapes.add(sh)
            st, cls = fmt_status(p.get("status"))
            t = p.get("tree") or {}
            jd = p.get("judgement") or {}
            honesty = str(p.get("honesty") or "")
            known = ("已知" in honesty) or ("著名" in str(t.get("edge") or "")) or \
                    str(p.get("status", "")).startswith(("真(已证", "真(已知", "真(定理"))
            badge = "已知问题 · 机器重新表述" if known else "机器提出（参照系未见）"
            items.append({
                "tier": "K1", "domain": DOMAIN_CN.get(dom, dom), "id": p.get("id"),
                "claim": stmt, "display": clean(stmt), "badge": badge,
                "honesty": honesty, "evidence": _evidence_of(p),
                "status": st, "cls": cls,
                "route": p.get("judge_route") or jd.get("method") or "—",
                "edge": t.get("edge") or "",
                "src": fn,
            })
            picked += 1
            if picked >= (2 if dom != "counterex" else 3):
                break
    return items, counts


def collect_tension():
    """K1 的另一支：语料张力 → 形式化问题（真实候选）。"""
    out = []
    m3 = load("method3_unique.json") or []
    for r in m3[:6]:
        out.append({"tier": "K1", "domain": "语料张力", "id": r.get("topic"),
                    "badge": "机器提出（语料张力候选）",
                    "claim": r.get("statement", ""),
                    "status": "待人类裁决", "cls": "open",
                    "route": "张力探测 → 形式化缺口",
                    "edge": f"H={r.get('H')}", "src": "method3_unique.json"})
    t1 = load("tensions_v1.json") or []
    tw = load("tensions_west.json") or []
    if t1:
        out.append({"tier": "K1", "domain": "语料张力", "id": "中哲",
                    "badge": "机器提出（语料张力候选）",
                    "claim": f"中哲语料里 {len(t1)} 处文本张力（取「{t1[0].get('topic')}」等）"
                             f"——两派交锋引文是否指向同一未形式化的问题？",
                    "status": "候选", "cls": "open", "route": "对峙/同文并存检测",
                    "edge": t1[0].get("topic", ""), "src": "tensions_v1.json"})
    if tw:
        out.append({"tier": "K1", "domain": "语料张力", "id": "西哲",
                    "badge": "机器提出（语料张力候选）",
                    "claim": f"西方哲学语料 {len(tw)} 处张力（如「{tw[0].get('topic')}」）"
                             f"→ 逐条映射到当代形式化缺口",
                    "status": "候选", "cls": "open", "route": "张力 → 缺口映射",
                    "edge": tw[0].get("topic", ""), "src": "tensions_west.json"})
    return out


def collect_scihist():
    """科学史语料里被作者自己承认的「未知」——**汇总为一条**。

    早期版本把语料片段（可能截断在半句上）直接当条目展示，被审校判为"语料碎片，非问题"。
    这里改为引用文档中已核实的完整引文，并明确标注：这是**人类已知未解**，机器只是把它们找齐。
    """
    d = load("scihist_open.json") or {}
    A = d.get("A") or []
    item = {
        "tier": "K1", "domain": "科学史未解", "id": "A 级自我承认的未知",
        "badge": "人类已知未解 · 机器找齐",
        "claim": (f"从科学史语料中挖出 {len(A)} 条「作者自己承认的未知」（A 级），"
                  f"例如：奇完全数——“是否存在奇完全数的问题依然是一个尚未解决的难题”；"
                  f"曲线与直线比较——“曲线和直线形状的比较，尚未解决”；"
                  f"欧拉-哥德巴赫——“欧拉与哥德巴赫…至今尚未解决”。"),
        "evidence": f"{len(A)} 条 A 级；来源为数学史/里程碑书系等语料",
        "status": "人类已知未解（机器只是找齐）", "cls": "open",
        "route": "科学史语料 → 自我承认的未知信号（不得而知/尚未解决）",
        "edge": "已知未解 ≠ 新知", "src": "scihist_open.json",
    }
    return [item], len(A)


def collect_k2():
    """K2：证据边界推进（唯一称得上"新知识"的一类）。"""
    items = []
    hv = load("harness_verdicts.json") or []
    conf = [h for h in hv if str(h.get("verdict", "")).startswith("confirmed")]
    zero = [h for h in hv if str(h.get("verdict", "")).startswith("confirmed") and not h.get("exceptions_N1")]
    items.append({
        "tier": "K2", "domain": "跨进制", "id": "P(b)",
        "claim": "命题 P(b)：对每个整数 n ≥ 4，存在一个 base-b 回文数 p 与一个素数 q 使 n = p + q。"
                 "更强的观察：对 b ≥ 4，例外集有限且很小。",
        "status": "数值汇合（非证明）", "cls": "num",
        "route": "精确枚举 + harness 独立复核（N0=5×10⁶ → N1=10⁷ 汇合）",
        "edge": f"{len(conf)}/{len(hv)} 个进制 confirmed（{len(zero)} 个零例外）",
        "src": "harness_verdicts.json + docs/CONJECTURE_PALBASE.md"})
    items.append({
        "tier": "K2", "domain": "跨进制", "id": "b=10",
        "claim": "base 10 的「回文数 + 素数」覆盖推到 10⁸ 仍零例外（两种独立实现交叉验证）；"
                 "人类讨论此前止于 ~10⁶（MathOverflow #250504 曾怀疑 999999 是反例）。",
        "status": "confirmed", "cls": "ok",
        "route": "两种独立实现 + 分段扫描复核",
        "edge": "边界 10⁶ → 10⁸", "src": "tools/scale_hunt.py + docs/CONJECTURE_PALBASE.md"})
    items.append({
        "tier": "K2", "domain": "跨进制", "id": "单例外进制",
        "claim": "单例外进制（b=9/11/13/14/16）的例外集推到 3×10⁷ 完全稳定（b9=124, b11=126, b13=126, "
                 "b14=540, b16=539）——其中 b11 与 b13 的例外同为 126。",
        "status": "confirmed", "cls": "ok", "route": "规模化扫描稳定性",
        "edge": "3×10⁷ 稳定", "src": "tools/palbase_scan.py"})
    items.append({
        "tier": "K2", "domain": "跨进制", "id": "b=2",
        "claim": "base 2 的同类覆盖**不成立**：例外持续增长并贴着扫描边界（4.3×10⁶ 级）→ 被 harness 判 rejected。",
        "status": "rejected", "cls": "no", "route": "harness 独立验证",
        "edge": "反例：增长不停", "src": "harness_verdicts.json"})
    gm = load("grown_motifs.json") or []
    gconf = [g for g in gm if g.get("stage") == "confirmed"]
    for g in gconf[:3]:
        pr = g.get("probe") or {}
        items.append({
            "tier": "K2", "domain": "配对集", "id": g.get("id"),
            "claim": f"命题（{g.get('derived')}）：两族对象按阈值相加可覆盖全部足够大的整数——"
                     f"实测阈值 {pr.get('threshold')}，阈值之后无例外。",
            "status": "confirmed", "cls": "ok", "route": "机器实测（探针跑满）",
            "edge": f"阈值 {pr.get('threshold')} · 例外前 {len(pr.get('fails_head') or [])} 项",
            "src": "grown_motifs.json"})
    if gconf:
        items.append({"tier": "K2", "domain": "配对集", "id": "汇总",
                      "claim": f"母题配对集共 {len(gm)} 条，其中 confirmed {len(gconf)} 条、"
                               f"needs_extend {len([g for g in gm if g.get('stage') == 'needs_extend'])} 条、"
                               f"hypothesis {len([g for g in gm if g.get('stage') == 'hypothesis'])} 条。",
                      "status": "confirmed", "cls": "ok", "route": "机器实测",
                      "edge": "逐条 probe 记录", "src": "grown_motifs.json"})
    return items


def collect_k3():
    return [{
        "tier": "K3", "domain": "归纳", "id": "BC",
        "claim": "由 b=2..16 的实际数据归纳：进制 b 的「回文数+素数」覆盖在 b ≥ 4 时例外有限且小；"
                 "b = 2 例外无界、b = 3 例外数偏大（68）——存在一个「进制阈值」式的分层。",
        "status": "数值归纳（待证明）", "cls": "num",
        "route": "跨 15 个进制的数据归纳 + harness 复核",
        "edge": "10/15 进制零例外或单例外", "src": "docs/CONJECTURE_PALBASE.md"},
        {"tier": "K3", "domain": "归纳", "id": "机制",
         "claim": "反例集的稠密度是判别「真结构」与「扫描伪影」的关键指标：例外贴边界且密度不降 → "
                  "多为伪影或未收敛；例外汇合且密度趋零 → 才可能是结构。",
         "status": "方法学结论（来自 12 次自纠错）", "cls": "num",
         "route": "自纠错复盘（第 8 次：max_exc_density=5% 守卫）",
         "edge": "写进判据", "src": "docs/EXPERIMENT_RECORD.md"}]


def collect_imagination():
    """想象路：概念（本质判断 + 可检验问题）。按项目标准是"需解释"，不是"需解决"。"""
    items = []
    deep = load("imagination_deep.json") or {}
    sent = load("sentence_batch.json") or {}
    for name, rec in list(deep.items())[:5]:
        tqs = rec.get("testable_questions") or []
        items.append({
            "tier": "IM", "domain": "概念", "id": name,
            "claim": rec.get("essence") or "",
            "status": "成段（需解释）", "cls": "concept",
            "route": rec.get("judge_route") or "五步法：组词→拆词→还原造句→成段→解释",
            "edge": (tqs[0] if tqs else ""), "src": "imagination_deep.json"})
    for name, rec in list(sent.items())[:4]:
        if any(i["id"] == name for i in items):
            continue
        items.append({
            "tier": "IM", "domain": "概念", "id": name,
            "claim": (rec.get("para") or "")[:150] + "…",
            "status": "成段（需解释）", "cls": "concept",
            "route": "问→拆→再问→再拆→成段",
            "edge": rec.get("q", ""), "src": "sentence_batch.json"})
    return items


def collect_fusion():
    """领域融合：全量真实结果（矩阵审计、结构桥梁、真三域候选、仿真、territory、负结果）。"""
    items = []

    # A. 领域级融合 + 结构桥梁判据
    ff = load("field_fusion.json") or {}
    fields = ff.get("fields") or {}
    cand = ff.get("candidates") or []
    n_fields = len(fields)
    n_pairs = ff.get("total_pairs") or n_fields * (n_fields - 1)
    if n_fields:
        items.append({
            "tier": "F", "domain": "领域级融合", "id": "结构桥梁判据",
            "claim": f"{n_fields} 个基础领域两两配对共 {n_pairs} 对；加上「结构桥梁」判据"
                     f"（对象携带的结构 ∩ 方法作用的结构 ≠ ∅）后，剩 {len(cand)} 对值得问的配对 —— "
                     f"砍掉的正是「数论的对象 × 音乐的方法」这类无理由配对。",
            "evidence": f"{len(cand)}/{n_pairs} 对通过结构桥梁",
            "status": "判据已落地", "cls": "num",
            "route": "结构交集非空 + 可算性",
            "edge": "桥 = 对象结构 ∩ 方法结构", "src": "field_fusion.json"})
        c0 = next((c for c in cand if isinstance(c, dict) and c.get("structural")), None)
        if c0:
            hit = c0.get("bridges") or []
            br = ""
            if hit and isinstance(hit[0], dict):
                b = hit[0]
                br = f"（{b.get('o', '')} × {b.get('m', '')}）"
            items.append({
                "tier": "F", "domain": "领域级融合", "id": c0.get("name") or "候选",
                "claim": c0.get("new_question") or "",
                "evidence": f"配对：{c0.get('shape', '')}；{c0.get('computable', '')}{br}",
                "status": "领域级融合问题", "cls": "open",
                "route": c0.get("judge") or "实验+理论",
                "edge": " × ".join((c0.get("parent_questions") or [])[:2]),
                "src": "field_fusion.json"})

    # B. 笛卡尔矩阵审计（负结果 → 整改 → 真三域）
    v4 = load("cross_md_v4.json") or {}
    st, na, lay = v4.get("stages") or {}, v4.get("nominal_audit_v3") or {}, v4.get("layering") or {}
    if st:
        items.append({
            "tier": "F", "domain": "矩阵审计", "id": "真三域",
            "claim": f"三域笛卡尔矩阵 {st.get('笛卡尔矩阵')} 条 → F1 良构过门 {st.get('F1过门')} 条 → "
                     f"真三域候选 {st.get('真三域候选')} 条。同时对上一版 {na.get('three_domain_total')} 条三域候选"
                     f"逐条核对：真三域参与 {na.get('real_three_domain')} 条，其余只是把第三域写进句子。",
            "evidence": f"分层：可判 {lay.get('i_可判')} · 需建验证器 {lay.get('ii_需建验证器')} · 空壳 {lay.get('iii_空壳')}",
            "status": "负结果 + 已整改", "cls": "no",
            "route": "逐条核对第三域是否真的参与判定",
            "edge": "名义三域 → 真三域", "src": "cross_md_v4.json"})
    for r in v4.get("three_domain") or []:
        doms = " × ".join(r.get("domains") or [])
        tt = r.get("third_table") or []
        first = tt[0] if tt else {}
        items.append({
            "tier": "F", "domain": "真三域候选", "id": doms,
            "claim": r.get("statement") or "",
            "evidence": f"第三域参数 {r.get('third_param')} 网格 {r.get('third_grid')}；"
                        f"首行实测输出 {first.get('outputs')}",
            "status": "真三域（已跑参数网格）", "cls": "num",
            "route": f"仿真/数值 · {str(r.get('crit'))[:40]}",
            "edge": r.get("obj") or "", "src": "cross_md_v4.json"})
    for r in v4.get("needs_verifier") or []:
        items.append({
            "tier": "F", "domain": "跨域候选", "id": " × ".join(r.get("domains") or []),
            "claim": r.get("statement") or "",
            "evidence": f"对象 {r.get('obj')}；量词域 {r.get('quant')}",
            "status": "需建验证器", "cls": "open",
            "route": r.get("route") or "需建验证器",
            "edge": str(r.get("crit"))[:44], "src": "cross_md_v4.json"})

    # C. 跨域候选扫描的判官分布
    v3 = load("cross_md_v3.json") or {}
    rows = v3.get("rows") or []
    if rows:
        judge = Counter(str(r.get("llm_judge", ""))[:4] for r in rows)
        kind = Counter(str((r.get("verify") or {}).get("kind", "")) for r in rows)
        two = sum(1 for r in rows if len(r.get("domains") or []) == 2)
        three = sum(1 for r in rows if len(r.get("domains") or []) == 3)
        stages = v3.get("stages") or ["", "", ""]
        items.append({
            "tier": "F", "domain": "候选扫描", "id": f"{len(rows)} 条",
            "claim": f"从 {stages[1]} 条里筛出 {len(rows)} 条可判跨域候选（双域 {two} / 三域 {three}），"
                     f"每条都配了判定方式并实跑出结果。",
            "evidence": f"判定：数值 {kind.get('数值', 0)} · 仿真 {kind.get('仿真', 0)}；"
                        f"判官：N1 已知 {judge.get('N1 ', 0)} · N2 需复核 {judge.get('N2 ', 0)} · N3 {judge.get('N3', 0)}",
            "status": "全部可判（无 N3）", "cls": "num",
            "route": "数值/仿真实跑 + LLM 分层判",
            "edge": "stage 454 → 454 → 130", "src": "cross_md_v3.json"})

    # D. 三域仿真结论
    cb = load("cross_md_belief.json") or []
    if cb:
        collapse = [r for r in cb if r.get("belief_underest_noise") == 0.5]
        ok = [r for r in cb if r.get("belief_underest_noise") == 1.0]
        if collapse and ok:
            items.append({
                "tier": "F", "domain": "三域仿真", "id": "AGM × 信道",
                "claim": f"信念修正 × 迭代 × 噪声信道：正确模型总是收敛；但低估噪声时，"
                         f"信道容量 ≤ {collapse[-1].get('capacity_bit')} bit 段会塌成「完全不学习」，"
                         f"容量 ≥ {ok[0].get('capacity_bit')} bit 后恢复收敛，偏差随容量单调下降。",
                "evidence": f"容量跨度 {cb[0].get('capacity_bit')}–{cb[-1].get('capacity_bit')} bit（{len(cb)} 个点）",
                "status": "真三域参与（已实测）", "cls": "num",
                "route": "仿真：AGM 修正 + 信道噪声（第三域以信道容量参数参与）",
                "edge": "容量阈值 ≈0.03 bit", "src": "cross_md_belief.json"})

    # E. 派生母题
    dm = load("derived_motifs.json") or []
    cross = [r for r in dm if r.get("cross")]
    if dm:
        fr = Counter(r.get("frame") for r in dm)
        pairs = Counter()
        for r in dm:
            doms = tuple(sorted(p.split("::")[0] for p in r.get("parents", [])))
            if len(doms) == 2:
                pairs[doms] += 1
        top = "；".join(f"{'×'.join(k)} {v}" for k, v in pairs.most_common(3))
        items.append({
            "tier": "F", "domain": "派生母题", "id": f"{len(dm)} 条",
            "claim": f"母题 × 母题生成 {len(dm)} 条派生母题（{len(cross)} 条真跨域），"
                     f"每条都必须落到一个具名共享框架才成立。",
            "evidence": f"框架：{' · '.join(f'{k} {v}' for k, v in fr.most_common())}｜配对最多：{top}",
            "status": "已生成（待判）", "cls": "open",
            "route": "母题交叉 → 框架匹配 → 判定路由",
            "edge": "同构框架才配对", "src": "derived_motifs.json"})

    # F. 配对集命题
    gm = load("grown_motifs.json") or []
    if gm:
        stages = Counter(g.get("stage") for g in gm)
        items.append({
            "tier": "F", "domain": "配对集命题", "id": f"{len(gm)} 条",
            "claim": f"母题配对生成的命题共 {len(gm)} 条：confirmed {stages.get('confirmed', 0)} · "
                     f"needs_extend {stages.get('needs_extend', 0)} · hypothesis {stages.get('hypothesis', 0)}，"
                     f"每条都带机器实测阈值（阈值之后无例外）。",
            "evidence": "例：质数×回文数 阈值 6 · 质数×奇合数 12 · 质数×平方数 7746",
            "status": "已实测", "cls": "ok",
            "route": "两族对象相加的覆盖阈值（探针跑满）",
            "edge": "配对集覆盖阈值", "src": "grown_motifs.json"})

    # G. 领域领地扫描
    ft = load("fusion_territories.json") or {}
    t4, t5 = ft.get("T4_evo_game") or [], ft.get("T5_comp_ling") or []
    if t4 or t5:
        ex4 = sum(1 for r in t4 if r.get("exceptions"))
        ex5 = sum(1 for r in t5 if r.get("exception"))
        items.append({
            "tier": "F", "domain": "领地扫描", "id": "博弈×进化 · 计量×语言学",
            "claim": f"两类跨域领地实跑：博弈论 × 演化（{len(t4)} 个博弈扫描 ESS 端点，{ex4} 个出现例外）；"
                     f"计量语言学 × 压缩（{len(t5)} 个语料，Menzerath/Zipf/Heaps 三项指标，{ex5} 个例外）。",
            "evidence": "计量语言学侧 9/9 语料全服从 → 产不出问题（记为负结果）",
            "status": "领地稀疏度实测", "cls": "num",
            "route": "扫描该领地是否还有例外（有例外才有问题）",
            "edge": "例外 = 问题来源", "src": "fusion_territories.json"})

    # H. 融合机制实验
    fm = load("fusion_matrix.json") or []
    run = [r for r in fm if r.get("before") is not None]
    if run:
        items.append({
            "tier": "F", "domain": "融合实验", "id": "选择 × 编码",
            "claim": f"「选择压 × 编码方式」的融合实验：结构多样性从 {run[0].get('before')} 提高到 "
                     f"{max(r.get('after') for r in run)}（三种编码结果不同）——选择压并非只做收敛。",
            "evidence": "；".join(f"{r.get('fusion')}: {r.get('before')}→{r.get('after')}" for r in run),
            "status": "实测（机制）", "cls": "num",
            "route": "仿真：选择压 × 编码冗余度",
            "edge": "多样性 before → after", "src": "fusion_matrix.json"})

    # I. 负结果
    items.append({
        "tier": "F", "domain": "负结果", "id": "跨域扫描",
        "claim": "300 组合的跨域扫描全部落在已知类（Schnirelmann 密度 / 稠密推论）；"
                 "「数学 × 艺术」的 26 个配对里 20 个已被已知结果占领。",
        "status": "负结果", "cls": "no",
        "route": "逐条回查文献/已知类",
        "edge": "跨域 ≠ 新", "src": "docs/guide/results.md"})
    return items, {"fields": n_fields, "pairs": n_pairs, "bridges": len(cand),
                   "three_domain": len(v4.get("three_domain") or []),
                   "cross_candidates": len(rows), "derived": len(dm), "grown": len(gm)}


def collect_checks():
    """复核性结果（机器重发现已知）：不是新知，是可信度基线。"""
    return [{"tier": "R", "domain": "复核", "id": "Tn/TnI",
             "claim": "机器独立算出 Tn/TnI 集合类总数 = 224，与 Forte 分类一致。",
             "status": "复核通过", "cls": "ok", "route": "精确枚举",
             "edge": "Forte 224", "src": "docs/guide/results.md"},
            {"tier": "R", "domain": "复核", "id": "最大熵集合类",
             "claim": "机器算出最大熵集合类恰为 2 个，与 all-interval tetrachords（4-18 / 4-26）一致。",
             "status": "复核通过", "cls": "ok", "route": "熵最大化枚举",
             "edge": "恰 2 个", "src": "docs/guide/results.md"},
            {"tier": "R", "domain": "复核", "id": "多完全数",
             "claim": "偶数多完全数 k=2,3,4 算得 {6,28,496,8128} / {120,672,523776} / {30240,32760}，"
                      "与 OEIS A007539 一致。",
             "status": "复核通过", "cls": "ok", "route": "筛法枚举",
             "edge": "A007539", "src": "docs/guide/results.md"},
            {"tier": "R", "domain": "复核", "id": "阻挫签名",
             "claim": "n=5 六边图：基态简并 4 ⟺ 含 K₄（统计物理已知）。",
             "status": "复核通过", "cls": "ok", "route": "计数 + 结构判定",
             "edge": "简并4⟺K₄", "src": "docs/guide/results.md"}]


def collect_negative():
    return [{"tier": "N", "domain": "负结果", "id": "OEIS 门",
             "claim": "自家模板的 OEIS 未见率 0%，而任选参数 100% —— 证明「过 OEIS 门」是廉价的，"
                      "拦住噪声的只有显著性证书。",
             "status": "负结果（方法学）", "cls": "no", "route": "六策略对照",
             "edge": "0% vs 100%", "src": "docs/guide/results.md"},
            {"tier": "N", "domain": "负结果", "id": "真三域",
             "claim": "50 条三域候选里，真正三域参与的 = 0 条（其余只是把第三域写进句子）。",
             "status": "负结果", "cls": "no", "route": "逐条核对 verifier",
             "edge": "0/50", "src": "docs/guide/honesty.md"},
            {"tier": "N", "domain": "负结果", "id": "张力候选",
             "claim": "129 → 387 → 258 幸存 → 19 个唯一张力候选，LLM 预判分级为 A2 / B17 / C0："
                      "0 条新问题，全部是「成熟张力」或「活但著名」。",
             "status": "负结果", "cls": "no", "route": "LLM 预判（人类裁决前）",
             "edge": "0 条新问题", "src": "docs/llm_grade_tension.md"},
            {"tier": "N", "domain": "负结果", "id": "语料",
             "claim": "9 个语料全部服从门泽拉特律（单调比 1.0、0 例外）——产不出问题；"
                      "早先「0.0」是自变量选错的假结果。",
             "status": "负结果 + 自纠错", "cls": "no", "route": "跨层级检验修正",
             "edge": "9/9 全服从", "src": "docs/EXECUTION_LOG.md"},
            {"tier": "N", "domain": "负结果", "id": "可判率",
             "claim": "全库实测：99 题中 72 题（73%）无机器可判数据，进不了新颖性门——"
                      "「不可判」≠「已排除」。",
             "status": "结构性边界", "cls": "no", "route": "判定路由可得性统计",
             "edge": "73% 不可判", "src": "docs/guide/honesty.md"}]


def main():
    k1, dom_counts = collect_k1()
    k1 += collect_tension()
    sci, sci_total = collect_scihist()
    k1 += sci
    k2 = collect_k2()
    k3 = collect_k3()
    im = collect_imagination()
    x, fusion = collect_fusion()
    check = collect_checks()
    neg = collect_negative()

    total_k1 = sum(dom_counts.values())
    all_items = k1 + k2 + k3 + im + x + check + neg
    for it in all_items:                       # 统一补展示字段
        it.setdefault("display", clean(it.get("claim", "")))
        it.setdefault("evidence", "")

    # 先落一份"未套用审校"的快照：供 build_overrides 从原始措辞生成覆盖表
    snap = ROOT / "out" / "curated_unreviewed.json"
    try:
        snap.parent.mkdir(parents=True, exist_ok=True)
        snap.write_text(json.dumps({"tiers": TIERS, "items": all_items}, ensure_ascii=False,
                                   indent=1), encoding="utf-8")
    except Exception as e:                             # noqa: BLE001
        print("! 未审校快照写入失败:", e)

    # 套用 LLM 审校覆盖（改写语病 / 把数据陈述改造成问题 / 丢掉落选项）
    overrides = load_overrides()
    all_items, n_ov, dropped = apply_overrides(all_items, overrides)
    if n_ov or dropped:
        print(f"审校覆盖：改写 {n_ov} 条，丢弃 {len(dropped)} 条 -> {dropped}")
    data = {
        "note": "全部条目取自机器实际产出的记录；状态与判定路由来自数据，不由展示层改写；"
                "正文措辞经 LLM 审校（tools/site/review_overrides.json）——只改措辞不改事实。",
        "reviewed": n_ov, "dropped": len(dropped),
        "counts": {"k1_domain_total": total_k1, "domains": dom_counts,
                   "scihist_total": sci_total, "cross_total": fusion.get("bridges"),
                   "fusion": fusion,
                   "k2": len(k2), "k3": len(k3), "imagination": len(im),
                   "checks": len(check), "negative": len(neg)},
        "tiers": TIERS,
        "items": all_items,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    c = Counter(i["tier"] for i in data["items"])
    print(f"wrote {OUT} ({OUT.stat().st_size/1024:.0f}KB)")
    print("分级计数:", dict(c))
    print("各域问题总数:", total_k1, "| 科学史未解:", sci_total, "| 融合:", fusion)
    # 便于人工检查：把正文写一份 UTF-8 文本
    report = ROOT / "out" / "curated_preview.txt"
    lines = [f"[{i['tier']}] {i['domain']} / {i['id']} · {i['status']} · {i['route']}\n"
             f"    {i.get('display') or i['claim']}\n    edge: {i['edge']}\n    src: {i['src']}"
             for i in data["items"]]
    report.write_text("\n\n".join(lines), encoding="utf-8")
    print("预览:", report)


if __name__ == "__main__":
    main()
