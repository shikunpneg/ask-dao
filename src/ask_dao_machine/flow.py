# -*- coding: utf-8 -*-
"""flow.py — 统一入口：一个输入 → 选流程 → 选终止点。

用户口径：
  我给你输入一个东西（paper / 图像 / 母题 / 词），选择流程（问题路、想象路），
  问题路到哪一步终止（科学问题 / 跑完 AI4S），
  想象路只能输入初始的词（可被组合的词），进来后可以选择过不过桥。

问题路五站（每站都在上一站产出上做**真实**的推进，不假装）：
  1 前问题     把证据句良构成问句（还没有判定方式）
  2 科学问题   加基础领域候选 + 判定路由 → 可判
  3 基础领域   明确归类，按领域分组
  4 问题树     分 L0–L5 并建族（同领域+同追问形式 = 一族）
  5 AI4S       尝试机器结算；算得出的给判定，算不出的**诚实标「机器无法结算」**

想象路：
  只能输入**词表里的词**（82 个可组合词）。给 1 个词 → 与全表组合；
  给多个词 → 两两组合。可选是否过经验桥（过桥只做脚手架，不做裁判）。

两条路互不评判：问题路问「真不真」，想象路问「能不能被理解」。
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent


# ── 基础领域关键词表（粗分，够用；命中最多者胜，平手按声明顺序） ──────
FIELDS: list[tuple[str, list[str]]] = [
    ("数学", ["定理", "证明", "序列", "素数", "回文", "收敛", "单调", "界", "枚举", "反例",
              "组合", "概率", "分布", "统计", "同余", "群", "拓扑", "度量", "收敛", "数值"]),
    ("物理", ["能量", "熵", "相变", "临界", "对称", "守恒", "量子", "场", "波动", "温度", "噪声"]),
    ("生物医学", ["cohort", "ckd", "hr ", "hazard", "odds", "peptide", "protein", "cancer",
                 "tumor", "tumour", "clinical", "patient", "trial", "biomarker", "receptor",
                 "kidney", "renal", "dose", "exposure", "outcome", "confound", "genetic",
                 "gene", "cell", "immune", "mortality", "incident", "risk of", "polygenic",
                 "蛋白", "肽", "临床", "患者", "队列", "剂量", "暴露", "结局", "混杂",
                 "肾", "癌", "细胞", "基因", "免疫", "生物", "随访", "效应量"]),
    ("化学", ["分子", "反应", "催化", "键", "晶体", "合成", "异构体", "烷烃"]),
    ("心理", ["认知", "记忆", "情绪", "动机", "学习", "意识", "注意", "决策"]),
    ("经济", ["市场", "资本", "增长", "稀缺", "分配", "效率", "激励", "博弈", "均衡"]),
    ("信息", ["编码", "信道", "压缩", "冗余", "反馈", "信息", "算法", "复杂度", "计算"]),
    ("语言", ["语法", "语义", "语用", "隐喻", "转喻", "话语", "语言", "词汇"]),
    ("音乐", ["和声", "对位", "旋律", "调性", "节奏", "音集", "集合类"]),
    ("艺术美学", ["美学", "风格", "形式", "再现", "表现", "审美", "艺术"]),
    ("伦理", ["责任", "规范", "正义", "善", "价值", "应当", "道德"]),
    ("哲学", ["本体", "本质", "认识", "现象", "自由", "公设", "范畴"]),
    ("逻辑", ["可判定", "一致", "完备", "形式系统", "公理", "推理", "蕴含"]),
    ("工程", ["模块", "维护", "标准化", "自动化", "工业化", "接口", "部署"]),
    ("天文", ["星系", "恒星", "宇宙", "黑洞", "天文"]),
    ("人工智能", ["模型", "训练", "生成", "神经网络", "学习", "AI", "机器"]),
]

# 问题树分层（按"走到了哪一步"定层，不做假层级）
LAYERS = {
    0: "L0 观测（原文证据）",
    1: "L1 前问题（良构问句）",
    2: "L2 科学问题（带判定路由）",
    3: "L3 基础领域（跨域同构）",
    4: "L4 问题树（成族）",
    5: "L5 已裁决（机器结算过）",
}

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
TEXT_EXTS = {".md", ".txt", ".text", ".markdown", ".pdf", ".docx", ".epub"}


def _load_tool(name: str):
    """从仓库 tools/ 里加载一个脚本模块（tools 不是包）。"""
    p = REPO / "tools" / f"{name}.py"
    if not p.exists():
        return None
    spec = importlib.util.spec_from_file_location(f"_ad_{name}", p)
    mod = importlib.util.module_from_spec(spec)
    try:
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
    except Exception as e:                                     # noqa: BLE001
        print(f"[warn] 加载 tools/{name}.py 失败: {type(e).__name__} {e}", file=sys.stderr)
        return None
    return mod


def word_list() -> list[str]:
    """可被组合的词（82 个）。"""
    m = _load_tool("word_understand")
    return sorted(getattr(m, "WORDS", {}) or {}) if m else []


def classify_field(text: str, default: str = "未分类") -> str:
    """粗分基础领域：命中关键词最多者胜（平手时长的关键词更具体者胜）。"""
    low = (text or "").lower()
    best, score, blen = default, 0, 0
    for name, kws in FIELDS:
        hits = [k for k in kws if k.lower() in low]
        s = len(hits)
        if s == 0:
            continue
        longest = max(len(k) for k in hits)
        if s > score or (s == score and longest > blen):
            best, score, blen = name, s, longest
    return best


def _slug(text: str, maxlen: int = 64) -> str:
    s = re.sub(r"[^\w\u4e00-\u9fff\u3400-\u4dbf\-]+", "-", (text or "").strip())
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return (s[:maxlen].rstrip("-")) or "run"


def _plan_dir(base: Path, slug: str, overwrite: bool = False) -> tuple[Path, int]:
    base.mkdir(parents=True, exist_ok=True)
    if overwrite:
        d = base / slug
        d.mkdir(parents=True, exist_ok=True)
        return d, 1
    d = base / slug
    if not (d / "flow.json").exists():
        d.mkdir(parents=True, exist_ok=True)
        return d, 1
    v = 2
    while (base / f"{slug}-v{v}").exists():
        v += 1
    d = base / f"{slug}-v{v}"
    d.mkdir(parents=True, exist_ok=True)
    return d, v


# ══════════════════════════════════════════════════════════════════
# 问题路：五站
# ══════════════════════════════════════════════════════════════════
def _to_prequestion(p: dict) -> str:
    """把证据句良构成一个问句（还没有判定方式）。"""
    ev = re.sub(r"\s+", " ", (p.get("evidence") or "")).strip()
    kind = p.get("type") or ""
    if "①" in kind:
        return f"作者自陈的未解点是什么、边界在哪？　（出处：{ev[:110]}）"
    if "②" in kind:
        sig = p.get("signal") or "分歧"
        return f"文中「{sig}」处的两侧能否在某个前提下统一？冲突落在哪一层？　（出处：{ev[:110]}）"
    if "③" in kind:
        name = kind.split("·")[-1] if "·" in kind else "结构"
        return f"该结论的{name}是什么？　（出处：{ev[:110]}）"
    if "④" in kind:
        name = kind.split("·")[-1] if "·" in kind else "方法学"
        return f"这条{name}缺口能否写成可判形式？　（出处：{ev[:110]}）"
    return f"这条结论该被追问什么？　（出处：{ev[:110]}）"


def _stage_problem(problems: list[dict], stop: str) -> list[dict]:
    """按终止点给每条问题补齐它该有的字段（真实推进，不编内容）。"""
    order = ["prequestion", "scientific", "domain", "tree", "ai4s"]
    upto = order.index(stop) if stop in order else 1

    # L1 前问题：总是有
    for p in problems:
        p["prequestion"] = _to_prequestion(p)
        p["layer"] = 1

    # L2 科学问题：带判定路由（paper.mine 已给出 route）
    if upto >= 1:
        for p in problems:
            p["scientific_question"] = p.get("statement")
            p["judge_route"] = p.get("route") or "开放(机器无法结算)"
            p["judgeable"] = bool(p.get("route")) and "开放" not in str(p.get("route"))
            p["layer"] = 2

    # L3 基础领域：先用**证据句原文**分类（statement 里含模板词，会把领域带偏）；
    # 证据句本身没有领域信号时，继承整篇的领域，并标明是继承来的。
    if upto >= 2:
        doc_field = classify_field(" ".join((p.get("evidence") or "") for p in problems))
        for p in problems:
            f = classify_field(p.get("evidence") or "", default="")
            if f:
                p["field"] = f
                p["field_source"] = "evidence"
            else:
                p["field"] = doc_field
                p["field_source"] = "document"
            p["layer"] = 3

    # L4 问题树成族（同领域 + 同追问形式 = 一族）
    if upto >= 3:
        fam: dict[tuple, list[int]] = {}
        for i, p in enumerate(problems):
            fam.setdefault((p.get("field"), (p.get("type") or "")[:6]), []).append(i)
        for (field, form), idxs in fam.items():
            fid = f"{field}/{form}" if form else field
            for i in idxs:
                problems[i]["family"] = fid
                problems[i]["family_size"] = len(idxs)
                if len(idxs) >= 2:
                    problems[i]["layer"] = 4

    # L5 AI4S：尝试机器结算。能算的（带 computed）标已裁决；其余诚实标无法结算
    if upto >= 4:
        for p in problems:
            c = p.get("computed")
            if c:
                p["ai4s"] = {"verdict": "settled(数值可复核)",
                             "detail": json.dumps(c, ensure_ascii=False)[:200]}
                p["layer"] = 5
            elif p.get("judgeable"):
                p["ai4s"] = {"verdict": "unsolved(需实验/需数据)",
                             "detail": f"判定方式：{p.get('judge_route')}"}
            else:
                p["ai4s"] = {"verdict": "unsolved(机器无法结算)",
                             "detail": "机器没有能落地的判定器；不假装算过"}
    return problems


def run_problem(inputs: list[Path], stop: str, out_root: Path, **kw) -> dict:
    """问题路：复用 paper.run（它已做输出版本化），再加五站字段。"""
    from . import paper as paper_mod

    payload = paper_mod.run([str(p) for p in inputs], out_dir=str(out_root),
                            max_per_type=kw.get("per_type", 8), quiet=kw.get("quiet", False),
                            domain=kw.get("domain", "auto"),
                            n_followups=kw.get("n_followups", 4),
                            max_total=kw.get("max_total", 0),
                            overwrite=kw.get("overwrite", False))
    problems = payload.get("problems") or []
    if not problems:
        return payload
    out = Path(payload.get("out_dir") or out_root)
    _stage_problem(problems, stop)

    by_field: dict[str, int] = {}
    by_layer: dict[str, int] = {}
    for p in problems:
        by_field[p.get("field", "未分类")] = by_field.get(p.get("field", "未分类"), 0) + 1
        by_layer[p.get("layer")] = by_layer.get(p["layer"], 0) + 1

    payload["path"] = "problem"
    payload["stop"] = stop
    payload["stages_done"] = ["prequestion", "scientific", "domain", "tree", "ai4s"][
        : ["prequestion", "scientific", "domain", "tree", "ai4s"].index(stop) + 1]
    payload["by_field"] = dict(sorted(by_field.items(), key=lambda x: -x[1]))
    payload["by_layer"] = {LAYERS.get(k, str(k)): v for k, v in sorted(by_layer.items())}
    (out / "problems_paper.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return payload


# ══════════════════════════════════════════════════════════════════
# 想象路
# ══════════════════════════════════════════════════════════════════
def run_imagination(words: list[str], out_root: Path, bridge: bool = False,
                    overwrite: bool = False, quiet: bool = False) -> dict:
    """想象路：只能输入词表里的词；给 1 个与全表组合，给多个两两组合。"""
    wu = _load_tool("word_understand")
    if wu is None:
        print("想象路需要仓库里的 tools/word_understand.py（用源码运行或 pip install -e .）。",
              file=sys.stderr)
        return {"error": "tools missing", "items": []}
    table = getattr(wu, "WORDS", {}) or {}
    bad = [w for w in words if w not in table]
    if bad:
        print(f"这些词不在可组合词表里：{bad}", file=sys.stderr)
        print(f"词表共 {len(table)} 个，例：{'、'.join(sorted(table)[:20])} …", file=sys.stderr)
        return {"error": "unknown words", "unknown": bad, "items": []}

    pairs = ([(words[0], b) for b in sorted(table) if b != words[0]]
             if len(words) == 1
             else [(a, b) for a in words for b in words if a != b])

    retrieve = None
    if bridge:
        rb = _load_tool("retrieve_browser")
        if rb is not None:
            # 先探一下 selenium 能不能真的起来（缺 urllib3 / 没装驱动时只提示一次，
            # 不要让每个组合都刷一行 [browser] 失败）
            usable = True
            try:
                import importlib.util as _iu
                if _iu.find_spec("selenium") is None:
                    usable = False
                else:
                    import urllib3  # noqa: F401
                    import selenium.webdriver  # noqa: F401
            except Exception:                                   # noqa: BLE001
                usable = False
            if usable:
                retrieve = rb.retrieve_cached
            else:
                print("（提示：本环境 selenium 起不来（缺 urllib3/驱动）→ 经验桥只走词条通道，"
                      "组合词搜索通道跳过。装的命令：pip install urllib3）")
            print(f"（过经验桥：{len(pairs)} 个组合都会先检索现实经验；失败即退化为无锚点）")

    items = []
    for a, b in pairs:
        ctx = None
        if retrieve is not None:
            try:
                r = retrieve(a, b)
                ctx = (r or {}).get("hits")
            except Exception:                                   # noqa: BLE001
                ctx = None
        items.append({
            "term": a + b, "a": a, "b": b,
            "understandings": wu.understand(a, b, table[a], table[b], ctx),
            "context_hits": len(ctx or []),
            "question": wu.question(a, b),
        })

    title = "×".join(words) if words else "imagination"
    out, ver = _plan_dir(out_root, _slug(f"想象路-{title}"), overwrite)
    payload = {
        "path": "imagination", "words": words, "count": len(items),
        "bridge": bool(bridge), "title": title, "version": ver, "out_dir": str(out),
        "note": "想象路的成功标准是「被理解」（语法正确 + 逻辑通畅 + 有推理判断），"
                "不是「有真实所指」；过桥只做脚手架，不做裁判。",
        "items": items,
    }
    if not quiet:
        for x in items[:3]:
            print(f"\n▶ 「{x['term']}」")
            for m in x["understandings"][:3]:
                print(f"    · {m[:96]}")
            if x["context_hits"]:
                print(f"    （经验锚点 {x['context_hits']} 条）")
        if len(items) > 3:
            print(f"\n… 还有 {len(items)-3} 个组合")
    dst = out / "flow.json"
    dst.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    if not quiet:
        print(f"\n合计 {len(items)} 个组合 → {dst}")
    return payload


# ══════════════════════════════════════════════════════════════════
# 统一入口
# ══════════════════════════════════════════════════════════════════
def detect_input(paths: list[str]) -> tuple[str, list[Path]]:
    """识别输入类型：image / paper。"""
    fs: list[Path] = []
    for p in paths:
        q = Path(p)
        if q.is_dir():
            for f in sorted(q.rglob("*")):
                if f.is_file() and (f.suffix.lower() in IMAGE_EXTS | TEXT_EXTS):
                    fs.append(f)
        elif q.exists():
            fs.append(q)
    if not fs:
        return "none", []
    if all(f.suffix.lower() in IMAGE_EXTS for f in fs):
        return "image", fs
    return "paper", fs


def main(argv=None, out_dir="out/runs") -> int:
    from . import _console
    _console.setup()
    argv = list(sys.argv[1:] if argv is None else argv)

    import argparse
    ap = argparse.ArgumentParser(
        prog="ask-dao-machine run",
        description="统一入口：给一个输入 → 选流程 → 选终止点",
        epilog=(
            "问题路终止点（--stop）：\n"
            "  prequestion  只到前问题（良构问句，还没有判定方式）\n"
            "  scientific   到科学问题（加基础领域候选 + 判定路由）——默认\n"
            "  domain       到基础领域（明确归类并分组）\n"
            "  tree         到问题树（分 L0–L5 并成族）\n"
            "  ai4s         跑完 AI4S（算得出的给判定，算不出的诚实标「机器无法结算」）\n"
            "\n例子：\n"
            "  ask-dao-machine run paper.pdf                          # 默认：问题路到科学问题\n"
            "  ask-dao-machine run paper.pdf --stop ai4s              # 一路跑到底\n"
            "  ask-dao-machine run paper.pdf --stop prequestion --max-total 20\n"
            "  ask-dao-machine run photo.png --stop tree              # 图像输入\n"
            "  ask-dao-machine run --words 熵                      # 想象路：1 个词与全表组合\n"
            "  ask-dao-machine run --words 熵,记忆 --bridge        # 想象路：两两组合 + 过桥\n"
            "  ask-dao-machine run --words 熵,记忆 --path both     # 两条路都跑（互不评判）\n"
            "\n输入类型自动识别：图片 → 感知入口；.pdf/.md/.docx/.epub/目录 → 论文入口。\n"),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="输入：论文文件/目录、图片文件/目录")
    ap.add_argument("--path", choices=["problem", "imagination", "both"], default=None,
                    help="走哪条路（默认：给 --words 走想象路，给文件走问题路）")
    ap.add_argument("--stop", choices=["prequestion", "scientific", "domain", "tree", "ai4s"],
                    default="scientific", help="问题路终止点（默认 scientific）")
    ap.add_argument("--words", default=None,
                    help="想象路初始词，逗号分隔（必须在可组合词表里）")
    ap.add_argument("--bridge", dest="bridge", action="store_true", default=None,
                    help="想象路：过经验桥（检索现实经验作脚手架）")
    ap.add_argument("--no-bridge", dest="bridge", action="store_false",
                    help="想象路：不过桥（默认）")
    ap.add_argument("--out", default=out_dir, help="输出根目录（默认 out/runs）")
    ap.add_argument("--depth", choices=["shallow", "normal", "deep"], default="normal",
                    help="问题深度档（shallow 3 / normal 8 / deep 20 条每类）")
    ap.add_argument("--per-type", type=int, default=None, help="覆盖 depth 的每类条数")
    ap.add_argument("--max-total", type=int, default=0, help="总条数上限（0 = 不限）")
    ap.add_argument("--domain", choices=["auto", "biomed", "none"], default="auto",
                    help="领域包（仅问题路）")
    ap.add_argument("--overwrite", action="store_true", help="同标题重跑覆盖，不递增 -v2/-v3")
    a = ap.parse_args(argv)

    words = [w.strip() for w in (a.words or "").replace("，", ",").split(",") if w.strip()]
    path = a.path or ("imagination" if words and not a.paths else "problem")
    out_root = Path(a.out)

    DEPTHS = {"shallow": (3, 2), "normal": (8, 4), "deep": (20, 4)}
    d_per, d_fol = DEPTHS[a.depth]
    per_type = a.per_type if a.per_type is not None else d_per

    from . import paper as paper_mod

    results = {}
    # ── 想象路 ──
    if path in ("imagination", "both"):
        if not words:
            ap.error("想象路需要 --words（例：--words 熵,记忆）")
        results["imagination"] = run_imagination(
            words, out_root, bridge=bool(a.bridge), overwrite=a.overwrite)

    # ── 问题路 ──
    if path in ("problem", "both"):
        if not a.paths:
            if path == "problem":
                ap.error("问题路需要一个输入（论文/图片/目录）")
        else:
            kind, files = detect_input(a.paths)
            if kind == "none":
                print("没找到可读入的文件。", file=sys.stderr)
                return 2
            print(f"输入类型：{kind}（{len(files)} 个文件）　路：问题路　终止点：{a.stop}")
            if kind == "image":
                try:
                    from . import perceive as perceive_mod
                except ModuleNotFoundError as e:
                    print(f"图像输入需要 numpy 与 pillow（当前缺：{e.name}）。", file=sys.stderr)
                    print('  装：pip install numpy pillow', file=sys.stderr)
                    return 2
                pp = perceive_mod.run([str(f) for f in files],
                                      out_dir=str(out_root / "perceive"),
                                      quiet=True)
                plist = pp.get("problems") or []
                _stage_problem(plist, a.stop)
                outd = out_root / "perceive"
                outd.mkdir(parents=True, exist_ok=True)
                order = ["prequestion", "scientific", "domain", "tree", "ai4s"]
                pp["path"] = "problem"
                pp["stop"] = a.stop
                pp["input_kind"] = "image"
                pp["stages_done"] = order[:order.index(a.stop) + 1]
                bf, bl = {}, {}
                for p in plist:
                    bf[p.get("field", "未分类")] = bf.get(p.get("field", "未分类"), 0) + 1
                    bl[p.get("layer")] = bl.get(p.get("layer"), 0) + 1
                pp["by_field"] = dict(sorted(bf.items(), key=lambda x: -x[1]))
                pp["by_layer"] = {LAYERS.get(k, str(k)): v for k, v in sorted(bl.items())}
                (outd / "problems_perceive.json").write_text(
                    json.dumps(pp, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"图像 → {len(plist)} 条问题 → {outd}")
                _print_problem_summary(pp, a.stop)
                results["problem"] = pp
            else:
                payload = run_problem(files, a.stop, out_root / "paper",
                                      per_type=per_type, n_followups=d_fol,
                                      max_total=a.max_total, domain=a.domain,
                                      overwrite=a.overwrite)
                results["problem"] = payload
                _print_problem_summary(payload, a.stop)

    if not results:
        return 2
    return 0


def _print_problem_summary(payload: dict, stop: str) -> None:
    print()
    print(f"终止点：{stop}　已走完：{' → '.join(payload.get('stages_done') or [])}")
    probs = payload.get("problems") or []
    print(f"合计 {len(probs)} 条")
    order = ["prequestion", "scientific", "domain", "tree", "ai4s"]
    up = order.index(stop) if stop in order else 1
    if up >= 2:                       # 走到「基础领域」这一站才有 field
        bf = payload.get("by_field") or {}
        if bf:
            print("按基础领域：" + " · ".join(f"{k} {v}" for k, v in list(bf.items())[:8]))
            inherited = sum(1 for p in probs if p.get("field_source") == "document")
            if inherited:
                print(f"（其中 {inherited} 条的证据句本身没有领域信号，"
                      f"按整篇论文的领域归类——已标 field_source=document）")
    if up >= 3:
        bl = payload.get("by_layer") or {}
        if bl:
            print("按问题树分层：")
            for k, v in bl.items():
                print(f"    {k}：{v} 条")
    if stop == "ai4s":
        settled = sum(1 for p in probs
                      if str((p.get("ai4s") or {}).get("verdict", "")).startswith("settled"))
        print(f"AI4S 站：机器结算 {settled} 条 · 无法结算/待实验 {len(probs)-settled} 条"
              f"（不假装算过）")


if __name__ == "__main__":
    raise SystemExit(main())
