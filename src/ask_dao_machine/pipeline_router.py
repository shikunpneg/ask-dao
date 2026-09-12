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

from . import ui_ux as ux  # noqa: E402  （统一输出根目录 / 下一步提示 / JSON 输出）


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
    """从仓库 tools/ 里加载一个脚本模块（tools 不是包）。

    tools/ 已按功能分到子目录（core/ engines/ build/ maintain/ research/ archive/），
    所以要在根 + 各子目录里找。踩过的坑：原来只找 `tools/{name}.py`，
    分目录后全部找不到，而报错文案还误导（说文件不存在，其实只是换了目录）。
    """
    tdir = REPO / "tools"
    cands = [tdir / f"{name}.py"]
    if tdir.is_dir():
        cands += [d / f"{name}.py" for d in sorted(tdir.iterdir())
                  if d.is_dir() and not d.name.startswith("_")]
    p = next((c for c in cands if c.exists()), None)
    if p is None:
        return None
    spec = importlib.util.spec_from_file_location(f"_ad_{name}", p)
    mod = importlib.util.module_from_spec(spec)
    try:
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
    except Exception as e:                                     # noqa: BLE001
        print(f"[warn] 加载 {p.relative_to(REPO)} 失败: {type(e).__name__} {e}", file=sys.stderr)
        return None
    return mod


def word_list() -> list[str]:
    """可被组合的词（82 个）。"""
    m = _load_tool("word_understand")
    return sorted(getattr(m, "WORDS", {}) or {}) if m else []


_SENT_END = re.compile(r"[。．.!?！？；;]")
WIKI_EXTRA = REPO / "data" / "wiki_extra"

# 「本质」质量闸门：宁可说没取到，也不要给一条自信但错的定义。
# 实测教训：`折叠` 被搜索解析成《北京折叠》（科幻小说），
#          `聚沉` 的首段是 {\displaystyle {\ce {C17H35COONa}}}（LaTeX 公式）。
_MARKUP = re.compile(r"\{\\|\\ce\b|\\displaystyle|\\mathrm|\\text|\\begin\{")
_WORKY = re.compile(r"《|》|事故|事件|电影|电视剧|小说|公司|大学|战争|条约|乐队|专辑|游戏|人物")
_PEOPLEY = re.compile(r"（[^）]{0,20}(生|卒|年)[^）]{0,20}）|中国.*(作家|演员|导演|歌手|运动员)")


def _definition_ok(text: str) -> bool:
    """这条「定义」能不能用：排除 markup、公式、以及"人/作品"式条目。"""
    if not text or len(text) < 6:
        return False
    if _MARKUP.search(text) or _WORKY.search(text) or _PEOPLEY.search(text):
        return False
    letters = sum(c.isalpha() or "\u4e00" <= c <= "\u9fff" for c in text)
    return letters / len(text) >= 0.6


def _definition_from(text: str) -> str:
    """从一段维基正文里抽一条短定义（去掉括号读音，截到第一个句末）。"""
    first = re.sub(r"\s+", " ", text or "").strip()
    first = re.sub(r"（[^）]{0,40}）", "", first)
    first = re.sub(r"\([^)]{0,40}\)", "", first).strip()
    d = _SENT_END.split(first)[0].strip()
    if 4 <= len(d) <= 70:
        return d
    return (first[:70].rstrip() + "…") if len(first) > 70 else first


def _api_get(params: dict, timeout: int = 12) -> dict:
    """MediaWiki API GET（纯 HTTP，不开浏览器）。失败返回空 dict。"""
    import urllib.error
    import urllib.parse
    import urllib.request
    p = dict(params, format="json", formatversion="2")
    url = f"https://zh.wikipedia.org/w/api.php?{urllib.parse.urlencode(p)}"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "ask-dao-machine/0.5 (essence lookup)"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:                                              # noqa: BLE001
        return {}


def _api_extract(title: str) -> tuple[str, list[str]]:
    d = _api_get({"action": "query", "prop": "extracts", "explaintext": "1",
                  "redirects": "1", "exlimit": "1", "titles": title})
    pages = (d.get("query") or {}).get("pages") or []
    if not pages or pages[0].get("missing"):
        return "", []
    t = pages[0].get("title") or title
    paras = [x.strip() for x in (pages[0].get("extract") or "").split("\n") if len(x.strip()) > 15]
    return t, paras


def _essence_via_api(word: str, timeout: int = 12) -> tuple[str, str]:
    """用 MediaWiki API 取定义（同名条目不存在时搜索解析），**过质量闸门**。

    返回 (定义, 实际采用的条目标题)；闸门不过就返回 ("", "")。
    偏好：标题含该词 > 首段含该词 > 搜索排名靠前；排除作品/人物/公式/乱码。
    """
    cands: list[str] = []
    t0, p0 = _api_extract(word)
    if p0:
        cands.append(t0)
    s = _api_get({"action": "query", "list": "search", "srsearch": word,
                  "srlimit": "6", "srnamespace": "0"}, timeout=timeout)
    for h in ((s.get("query") or {}).get("search") or []):
        if h["title"] not in cands:
            cands.append(h["title"])

    best: tuple[int, str, str] = (-99, "", "")
    for rank, title in enumerate(cands):
        if _WORKY.search(title):
            continue
        t, paras = _api_extract(title)
        if not paras:
            continue
        d = _definition_from(paras[0])
        if not _definition_ok(d):
            continue
        sc = 0
        if word in t:
            sc += 3                      # 标题里有这个词 → 更可能是对的那个义项
        if word in paras[0]:
            sc += 2
        sc -= rank                       # 搜索排名越靠前越好
        if sc > best[0]:
            best = (sc, d, t)
    if best[0] < 0:                      # 一条都没过闸门 → 诚实返回空
        return "", ""
    _sc, d, title = best
    try:                        # 缓存，下次秒回；也让桥的词条通道受益
        WIKI_EXTRA.mkdir(parents=True, exist_ok=True)
        (WIKI_EXTRA / f"{word}.json").write_text(json.dumps(
            {"term": word, "title": title, "paragraphs": [_definition_from(d)],
             "source": "mediawiki-api(auto)", "resolved_from": word},
            ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:                                              # noqa: BLE001
        pass
    return d, title


def _essence_for_word(word: str, bridge: bool = False, allow_net: bool = True) -> tuple[str, str]:
    """给词表外的词找「本质」定义。返回 (定义, 来源)。"""
    # 1) 本地语料（82 词表那次抓的 + 自动补抓的）
    for d in (REPO / "data" / "wiki", WIKI_EXTRA):
        p = d / f"{word}.json"
        if not p.exists():
            continue
        try:
            paras = (json.loads(p.read_text(encoding="utf-8")) or {}).get("paragraphs") or []
            if paras:
                return _definition_from(paras[0]), "wiki"
        except Exception:                                          # noqa: BLE001
            pass
    # 2) 纯 HTTP API 现取（快，不开浏览器；同名条目不存在时自动搜索解析）
    if allow_net:
        d, title = _essence_via_api(word)
        if d:
            tgt = f"（解析到条目「{title}」）" if title and title != word else ""
            return d + tgt, "wiki-api"
    # 3) 过桥现抓（要开浏览器；只在 --bridge 时做）
    if bridge:
        rb = _load_tool("retrieve_browser")
        if rb is not None:
            try:
                paras = ((rb.wiki_page(word) or {}).get("paragraphs") or [])
                if paras:
                    return _definition_from(paras[0]), "wiki-browser"
            except Exception:                                      # noqa: BLE001
                pass
    return "", "unknown"


def parse_essences(spec: str | None) -> dict[str, str]:
    """解析 --essence 参数： 折叠="多肽链自发形成三维构象" , 聚沉=蛋白聚集成块 """
    out: dict[str, str] = {}
    for chunk in (spec or "").replace("，", ",").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "=" in chunk:
            k, v = chunk.split("=", 1)
        elif "：" in chunk:
            k, v = chunk.split("：", 1)
        else:
            continue
        k, v = k.strip().strip('"“”'), v.strip().strip('"“”')
        if k and v:
            out[k] = v
    return out


def resolve_essences(words: list[str], user: dict[str, str] | None = None,
                     bridge: bool = False, allow_net: bool = True) -> tuple[dict[str, str], dict[str, str]]:
    """给每个词解析一条「本质」。来源优先级：用户指定 > 82 词表 > 本地维基语料 > 过桥 > 兜底。

    设计依据（不可动摇的原则）：**每个词都有意义**，所以词表外的词不该被拒绝——
    只是它的「本质」得有个来源，并且必须标明来源，不能假装是词表里的定义。
    """
    wu = _load_tool("word_understand")
    table = dict(getattr(wu, "WORDS", {}) or {}) if wu else {}
    user = user or {}
    ess: dict[str, str] = {}
    src: dict[str, str] = {}
    for w in words:
        if w in user:
            ess[w], src[w] = user[w], "user"
        elif w in table:
            ess[w], src[w] = table[w], "table"
        else:
            e, s = _essence_for_word(w, bridge=bridge, allow_net=allow_net)
            if e:
                ess[w], src[w] = e, s
            else:
                # 兜底要短（它会被拼进每个模板），并把决定权交回用户
                ess[w] = "未取到可靠定义"
                src[w] = "unknown"
    return ess, src


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
    from . import input_paper as paper_mod

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
                    overwrite: bool = False, quiet: bool = False,
                    essences: dict[str, str] | None = None) -> dict:
    """想象路：**任意词**都能进来（每个词都有意义）。

    词表 82 词有现成的「本质」定义；词表外的词走解析链拿本质
    （用户 --essence 指定 > 本地维基语料 > 过桥现抓 > 兜底），并标明来源。
    给 1 个词 → 与全表组合；给多个词 → 两两组合。
    """
    wu = _load_tool("word_understand")
    if wu is None:
        print("想象路需要仓库里的 tools/core/word_understand.py（用源码运行或 pip install -e .）。",
              file=sys.stderr)
        return {"error": "tools missing", "items": []}
    table = dict(getattr(wu, "WORDS", {}) or {})
    ess, src = resolve_essences(words, essences, bridge=bridge)

    if not quiet:
        outside = {w: (src[w], ess[w]) for w in words if src[w] != "table"}
        if outside:
            print("词表外的词 ——「本质」来源：")
            for w, (s, e) in outside.items():
                tag = {"user": "你指定", "wiki": "本地语料", "wiki-api": "维基(自动解析)",
                       "wiki-browser": "维基(过桥现抓)", "unknown": "没取到"}.get(s, s)
                print(f"    {w}　[{tag}]　{e}")
            unknown = [w for w, (s, _) in outside.items() if s == "unknown"]
            if unknown:
                names = "、".join(unknown)
                print()
                print(f"  ⚠ {names} 没取到可靠定义。")
                print("     自动解析要么没找到，要么找到的是同名的其它东西"
                      "（实测：`折叠` 会被解析成《北京折叠》那本科幻小说）——"
                      "所以宁可说没取到，也不给一条自信但错的定义。")
                example = "，".join(f'{w}="<一句话定义>"' for w in unknown[:2])
                print(f"     想用它？自己给一句本质：  --essence {example}")

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

    # understand() 内部按 WORDS 取值，所以把词表外的词临时并进去（结束后还原）
    added = [w for w in ess if w not in table]
    for w in added:
        wu.WORDS[w] = ess[w]
    try:
        items = []
        for a, b in pairs:
            ctx = None
            if retrieve is not None:
                try:
                    r = retrieve(a, b)
                    ctx = (r or {}).get("hits")
                except Exception:                               # noqa: BLE001
                    ctx = None
            items.append({
                "term": a + b, "a": a, "b": b,
                "understandings": wu.understand(a, b, ess[a], ess[b], ctx),
                "context_hits": len(ctx or []),
                "question": wu.question(a, b),
                "essence_source": {a: src.get(a), b: src.get(b)},
            })
    finally:
        for w in added:
            wu.WORDS.pop(w, None)

    title = "×".join(words) if words else "imagination"
    out, ver = _plan_dir(out_root, _slug(f"想象路-{title}"), overwrite)
    payload = {
        "path": "imagination", "words": words, "count": len(items),
        "bridge": bool(bridge), "title": title, "version": ver, "out_dir": str(out),
        "essences": ess, "essence_source": src,
        "note": "想象路的成功标准是「被理解」（语法正确 + 逻辑通畅 + 有推理判断），"
                "不是「有真实所指」；过桥只做脚手架，不做裁判。"
                "词表外的词的「本质」来源已在 essence_source 里标明。",
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
# 自己提的疑问 → 问题路（与论文同一条流水线）
# ══════════════════════════════════════════════════════════════════
def run_question(question: str, out_root: Path, stop: str = "scientific",
                 n_followups: int = 4, max_total: int = 0,
                 overwrite: bool = False, quiet: bool = False,
                 domain: str | None = None) -> dict:
    """把用户自己提的疑问当成一次"输入"，走问题路五站。

    以前 `ask` 只吐一条模板句就完事；现在它和 `paper` 一样：
    类型判定 → 判定路由 → 科学问题 → 四类结构追问 → 五站 → 版本化目录 + 报告。
    """
    qr = _load_tool("question_refiner")
    if qr is None:
        print("这条命令需要仓库里的 tools/core/question_refiner.py。", file=sys.stderr)
        return {"error": "tools missing", "problems": []}

    from . import input_paper as paper_mod

    dom = domain or classify_field(question, default="通用")
    r = qr.refine({"daily_question": question, "domain": dom})
    sci = r.get("scientific_question") or question
    route = r.get("judge_route") or "待定"

    problems = [{
        "id": "AQ01", "source": "<cli 自己提的疑问>", "domain": "日常疑问",
        "type": "①日常疑问", "is_author_stated": False,
        "signal": r.get("kind"), "evidence": question,
        "statement": sci, "route": route, "status": "待实验/待评审",
        "kind": r.get("kind"),
    }]
    # 结构追问：给一个疑问以"深度"（范围/反例/机制/定量）
    for name, tmpl, rt in paper_mod.FOLLOWUPS[:max(1, min(n_followups, 4))]:
        problems.append({
            "id": f"AQ{len(problems)+1:02d}", "source": "<cli 自己提的疑问>",
            "domain": "日常疑问", "type": f"③结构追问·{name}", "is_author_stated": False,
            "signal": r.get("kind"), "evidence": question,
            "statement": f"针对「{sci[:110]}」的{name}：{tmpl}",
            "route": rt, "status": "悬置(开放)",
        })
    if max_total and len(problems) > max_total:
        problems = problems[:max_total]

    _stage_problem(problems, stop)

    out, ver = _plan_dir(out_root, _slug(question[:48]), overwrite)
    payload = {
        "domain": "ask", "generator": "ask-dao-machine/pipeline_router.py run_question",
        "path": "problem", "stop": stop, "input_kind": "question",
        "question": question, "title": question[:80], "version": ver, "out_dir": str(out),
        "field": dom,
        "counts": {"total": len(problems), "author_stated": 0,
                   "machine_raised": len(problems)},
        "by_field": {dom: len(problems)},
        "by_layer": {},
        "problems": problems,
    }
    bl: dict = {}
    for p in problems:
        bl[p.get("layer")] = bl.get(p.get("layer"), 0) + 1
    payload["by_layer"] = {LAYERS.get(k, str(k)): v for k, v in sorted(bl.items())}
    order = ["prequestion", "scientific", "domain", "tree", "ai4s"]
    payload["stages_done"] = order[:order.index(stop) + 1] if stop in order else order[:2]

    (out / "problems_ask.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    if not quiet:
        print(f"疑问：{question}")
        print(f"类型：{r.get('kind')}　判定路由：{route}　基础领域：{dom}")
        print(f"科学问题：{sci}")
        _print_problem_summary(payload, stop)
        print(f"\n→ {out / 'problems_ask.json'}")
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
    from . import ui_console as _console
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
                    help="想象路初始词，逗号分隔（**任意词都行**；词表外的词会自动解析「本质」）")
    ap.add_argument("--essence", default=None,
                    help='给词表外的词指定「本质」：--essence 折叠="多肽链自发形成三维构象",聚沉="蛋白聚集成块"')
    ap.add_argument("--question", default=None,
                    help="自己提的疑问：走问题路（同 paper 一样的五站 + 版本化 + 报告）")
    ap.add_argument("--bridge", dest="bridge", action="store_true", default=None,
                    help="想象路：过经验桥（检索现实经验作脚手架）")
    ap.add_argument("--no-bridge", dest="bridge", action="store_false",
                    help="想象路：不过桥（默认）")
    ap.add_argument("--out", default=None,
                    help="输出根目录（默认 <当前目录>/out；所有命令共用同一个根，不再各写各的）")
    ap.add_argument("--json", action="store_true",
                    help="只把结果 JSON 打到 stdout（人看的日志走 stderr，方便接管道）")
    ap.add_argument("--quiet", "-q", action="store_true", help="少说话（只留结果路径）")
    ap.add_argument("--list", action="store_true", help="列出跑过的产物与位置，不跑新的")
    ap.add_argument("--depth", choices=["shallow", "normal", "deep"], default="normal",
                    help="问题深度档（shallow 3 / normal 8 / deep 20 条每类）")
    ap.add_argument("--per-type", type=int, default=None, help="覆盖 depth 的每类条数")
    ap.add_argument("--max-total", type=int, default=0, help="总条数上限（0 = 不限）")
    ap.add_argument("--domain", choices=["auto", "biomed", "none"], default="auto",
                    help="领域包（仅问题路论文输入）")
    ap.add_argument("--field", default=None,
                    help="自己提疑问时手指定基础领域（默认自动判；判不出就不硬拼进句子）")
    ap.add_argument("--overwrite", action="store_true", help="同标题重跑覆盖，不递增 -v2/-v3")
    a = ap.parse_args(argv)

    words = [w.strip() for w in (a.words or "").replace("，", ",").split(",") if w.strip()]
    essences = parse_essences(a.essence)
    has_question = bool(a.question)
    path = a.path or ("imagination" if words and not a.paths and not has_question else "problem")
    out_root = ux.out_root(a.out)
    quiet = a.quiet or a.json

    if getattr(a, "list", False):
        ux.list_runs(out_root, as_json=a.json)
        return 0

    DEPTHS = {"shallow": (3, 2), "normal": (8, 4), "deep": (20, 4)}
    d_per, d_fol = DEPTHS[a.depth]
    per_type = a.per_type if a.per_type is not None else d_per

    results = {}
    # ── 想象路 ──
    if path in ("imagination", "both"):
        if not words:
            ap.error("想象路需要 --words（例：--words 熵,记忆，或自造词 --words 折叠）")
        results["imagination"] = run_imagination(
            words, ux.run_dir(out_root, "words"), bridge=bool(a.bridge),
            overwrite=a.overwrite, quiet=quiet, essences=essences)

    # ── 问题路 ──
    if path in ("problem", "both"):
        if has_question:
            results["problem"] = run_question(
                a.question, ux.run_dir(out_root, "ask"), stop=a.stop, n_followups=d_fol,
                max_total=a.max_total, overwrite=a.overwrite, quiet=quiet, domain=a.field)
        elif not a.paths:
            if path == "problem":
                ap.error("问题路需要一个输入：论文/图片/目录，或用 --question \"你的疑问\"")
        else:
            kind, files = detect_input(a.paths)
            if kind == "none":
                print("没找到可读入的文件。", file=sys.stderr)
                return 2
            if not quiet:
                print(f"输入类型：{kind}（{len(files)} 个文件）　路：问题路　终止点：{a.stop}", file=sys.stderr)
            if kind == "image":
                try:
                    from . import input_image as perceive_mod
                except ModuleNotFoundError as e:
                    print(f"图像输入需要 numpy 与 pillow（当前缺：{e.name}）。", file=sys.stderr)
                    print('  装：pip install numpy pillow', file=sys.stderr)
                    return 2
                outd = ux.run_dir(out_root, "image")
                pp = perceive_mod.run([str(f) for f in files], out_dir=str(outd), quiet=True)
                plist = pp.get("problems") or []
                _stage_problem(plist, a.stop)
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
                print(f"图像 → {len(plist)} 条问题 → {outd}", file=sys.stderr)
                _print_problem_summary(pp, a.stop)
                results["problem"] = pp
            else:
                payload = run_problem(files, a.stop, ux.run_dir(out_root, "paper"),
                                      per_type=per_type, n_followups=d_fol,
                                      max_total=a.max_total, domain=a.domain,
                                      overwrite=a.overwrite, quiet=quiet)
                results["problem"] = payload
                _print_problem_summary(payload, a.stop)

    if not results:
        return 2
    # ── 收尾：JSON 输出 / 下一步提示 ──
    if a.json:
        ux.emit_json(results)
    else:
        kinds = []
        if "problem" in results:
            kinds.append(results["problem"].get("input_kind") or "paper")
        if "imagination" in results:
            kinds.append("words")
        for k in kinds:
            ux.next_steps(out=out_root, kind=k)
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
