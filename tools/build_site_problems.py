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


def clean(text):
    """展示清洗：把生成器塞进陈述里的原始数据摘掉，只留问题/命题本身。
    例：'…共 6 个, 最大者 108(前几个: [6, 12, 28])。**是什么刻画了这个例外集**?'
      → '…共 6 个，最大者 108。是什么刻画了这个例外集？'
    """
    import re
    s = str(text or "")
    s = re.sub(r"[（(]\s*前几个[:：][^）)]*[）)]", "", s)          # 摘掉"前几个: [...]"
    s = re.sub(r"[（(]\s*(?:例外前|seq|examples?)[^）)]*[）)]", "", s, flags=re.I)
    s = s.replace("**", "").replace("  ", " ").strip()
    s = s.replace(", ", "，").replace("; ", "；")   # 只换"逗号+空格"，别动区间里的 6,40000
    s = re.sub(r"\s*([?？])", r"\1", s)
    s = s.replace("?", "？").replace("。？", "？")
    return s


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
            items.append({
                "tier": "K1", "domain": DOMAIN_CN.get(dom, dom), "id": p.get("id"),
                "claim": stmt, "display": clean(stmt),
                "evidence": _evidence_of(p),
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
                    "claim": r.get("statement", ""),
                    "status": "待人类裁决", "cls": "open",
                    "route": "张力探测 → 形式化缺口",
                    "edge": f"H={r.get('H')}", "src": "method3_unique.json"})
    t1 = load("tensions_v1.json") or []
    tw = load("tensions_west.json") or []
    if t1:
        out.append({"tier": "K1", "domain": "语料张力", "id": "中哲",
                    "claim": f"中哲语料里 {len(t1)} 处文本张力（取「{t1[0].get('topic')}」等）"
                             f"——两派交锋引文是否指向同一未形式化的问题？",
                    "status": "候选", "cls": "open", "route": "对峙/同文并存检测",
                    "edge": t1[0].get("topic", ""), "src": "tensions_v1.json"})
    if tw:
        out.append({"tier": "K1", "domain": "语料张力", "id": "西哲",
                    "claim": f"西方哲学语料 {len(tw)} 处张力（如「{tw[0].get('topic')}」）"
                             f"→ 逐条映射到当代形式化缺口",
                    "status": "候选", "cls": "open", "route": "张力 → 缺口映射",
                    "edge": tw[0].get("topic", ""), "src": "tensions_west.json"})
    return out


def collect_scihist():
    """科学史挖出的真未解（人类已知未解，机器只是挖出来——必须在文案里说清）。"""
    d = load("scihist_open.json") or {}
    A = d.get("A") or []
    samples, seen = [], set()
    for r in A:
        sig = (r.get("signal") or "").strip()
        if sig in seen:
            continue
        seen.add(sig)
        ctx = (r.get("context") or "").strip()
        samples.append({"tier": "K1", "domain": "科学史未解", "id": sig or "未解",
                        "claim": ctx[:120] + ("…" if len(ctx) > 120 else ""),
                        "status": "人类已知未解", "cls": "open",
                        "route": "科学史语料挖掘（A 级自我承认的未知）",
                        "edge": r.get("level", ""), "src": "scihist_open.json"})
        if len(samples) >= 4:
            break
    return samples, len(A)


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


def collect_cross():
    """跨域融合：母题 × 母题（真实 parents + 共享框架）。"""
    dm = load("derived_motifs.json") or []
    cross = [r for r in dm if r.get("cross")]
    items = []
    for r in cross[:4]:
        pa = r["parents"][0].split("::")[-1]
        pb = r["parents"][1].split("::")[-1]
        items.append({
            "tier": "X", "domain": "跨域融合", "id": r.get("id"),
            "claim": f"「{pa}」与「{pb}」共享框架 {r.get('frame')} —— 能否由此问出"
                     f"一个两边都不曾单独问过的问题？",
            "status": "派生母题（待判）", "cls": "open",
            "route": f"母题交叉 → 框架匹配（route={r.get('route')}）",
            "edge": r.get("derived", ""), "src": "derived_motifs.json"})
    return items, len(cross)


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
    x, cross_total = collect_cross()
    check = collect_checks()
    neg = collect_negative()

    total_k1 = sum(dom_counts.values())
    all_items = k1 + k2 + k3 + im + x + check + neg
    for it in all_items:                       # 统一补展示字段
        it.setdefault("display", clean(it.get("claim", "")))
        it.setdefault("evidence", "")
    data = {
        "note": "全部条目取自机器实际产出的记录；状态与判定路由来自数据，不由展示层改写。",
        "counts": {"k1_domain_total": total_k1, "domains": dom_counts,
                   "scihist_total": sci_total, "cross_total": cross_total,
                   "k2": len(k2), "k3": len(k3), "imagination": len(im),
                   "checks": len(check), "negative": len(neg)},
        "tiers": [
            {"key": "K1", "name": "K1 · 提出的问题", "en": "NEW PROBLEMS",
             "desc": "把困惑/数据改造成可判的问题——这是新知识的第一步。每条都带判定路由。"},
            {"key": "K2", "name": "K2 · 证据边界推进", "en": "EVIDENCE FRONTIER",
             "desc": "对已有问题给出更强证据、更大边界。目前唯一称得上「新知识」的一类。"},
            {"key": "K3", "name": "K3 · 归纳的规律", "en": "INDUCED LAWS",
             "desc": "从数据归纳出的普遍律。机器只做到「数值汇合 + 待证明」。"},
            {"key": "IM", "name": "想象路 · 概念", "en": "IMAGINATION PATH",
             "desc": "产概念，不是产答案。标准是「解释」：语法正确 + 逻辑通畅 + 有推理判断。"},
            {"key": "X", "name": "跨域融合 · 观点", "en": "CROSS-DOMAIN",
             "desc": "母题 × 母题：只有共享结构桥梁的配对才值得问。"},
            {"key": "R", "name": "复核性结果", "en": "REPRODUCTION",
             "desc": "机器重发现已知——不是新知，是可信度基线。"},
            {"key": "N", "name": "负结果", "en": "NEGATIVE RESULTS",
             "desc": "机器自己否掉的、产不出问题的——与正结果同等重要。"},
        ],
        "items": all_items,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    c = Counter(i["tier"] for i in data["items"])
    print(f"wrote {OUT} ({OUT.stat().st_size/1024:.0f}KB)")
    print("分级计数:", dict(c))
    print("各域问题总数:", total_k1, "| 科学史未解:", sci_total, "| 跨域:", cross_total)
    # 便于人工检查：把正文写一份 UTF-8 文本
    report = ROOT / "out" / "curated_preview.txt"
    lines = [f"[{i['tier']}] {i['domain']} / {i['id']} · {i['status']} · {i['route']}\n"
             f"    {i.get('display') or i['claim']}\n    edge: {i['edge']}\n    src: {i['src']}"
             for i in data["items"]]
    report.write_text("\n\n".join(lines), encoding="utf-8")
    print("预览:", report)


if __name__ == "__main__":
    main()
