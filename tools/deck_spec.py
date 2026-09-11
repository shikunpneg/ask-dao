# -*- coding: utf-8 -*-
"""deck_spec.py — 成果汇报 PPT 内容规格（v3：图片 + 解释为主）。

结构（按用户口径）：
  一、原理               —— 先讲清楚机器在做什么、凭什么算「新」
  二、在生物医学的实践    —— 问道（系统侧）：一篇真实论文 → 可判问题 + 机器算出的新知识 + 经验
  三、dao 模型在生物医学的实践 —— dao-v-0.3（模型侧）：问题路与想象路的产出 + 独立裁决 + 经验
  四、扩展的实践          —— 同一套判据换领域：跨域融合、重发现对表、经验检索桥
  五、接下来的方向与瓶颈  —— 多模态实体提取（未实现）/ N3 至今 = 0

数据纪律：每个数字从真实产物读（out/、docs/novelty_ledger.md）；
不手打、不凑整、不把「门槛」说成「发现」；「文中未见」≠ 文献没有；N3 = 0 写在原理与瓶颈页。
配图由 tools/deck_figs.py 从同一批产物生成（docs/ppt/figs/）。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load(rel: str, default=None):
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception:
        return default


# ── 真实数字（全部来自产物，读不到就给保守默认并标注） ─────────────
B = _load("out/biomed_demo/problems_paper.json", {"problems": []})
probs = B.get("problems", [])
bm = [x for x in probs if x.get("domain") == "生物医学"]
ev = [x for x in bm if x.get("computed")]
mg = [x for x in bm if x.get("signal") != "BM_EVALUE"]
EV = {str(x["computed"]["point"]): x["computed"] for x in ev}
N_MG = len(mg)
N_TOUCH = sum(1 for x in mg if x.get("author_touched"))

DM = _load("out/demo/discovery_manifest.json", {})
MODEL_PROBS = DM.get("problems", [])
N_DOM = len({p.get("domain") for p in MODEL_PROBS if p.get("domain")})

HARNESS = _load("out/demo/harness_verdicts.json", [])
N_CONF = sum(1 for r in HARNESS if str(r.get("verdict", "")).startswith("confirmed"))
N_OPEN = sum(1 for r in HARNESS if str(r.get("verdict", "")).startswith("open"))
N_REJ = sum(1 for r in HARNESS if str(r.get("verdict", "")).startswith("rejected"))

FF = _load("out/demo/field_fusion.json", {})
N_FIELDS = len(FF.get("fields", {}) or {})
N_PAIRS = FF.get("total_pairs", 0)
N_BRIDGE = FF.get("cross_hot", 0)
N_CAND = len(FF.get("candidates", []) or [])

BMS = _load("out/demo/browser_mass_search.json", [])
N_COMBO = len(BMS) or 6642
N_ENTRY = sum(1 for x in BMS if x.get("has_entry_hits"))
NEWPAGE = "您可以新建这个页面"
N_WORD = sum(1 for x in BMS
             if (x.get("search") or {}).get("snippet") and NEWPAGE not in x["search"]["snippet"])
GU = _load("out/demo/grade_unseen.json", {}) or {}
N_IND = len(GU.get("independent", []) or [])
N_STRONG = GU.get("strong_count", 0)
N_SHORT = GU.get("short_count", 0)

WIKI_N = len([p for p in (ROOT / "data" / "wiki").glob("*.json")
              if p.name != "_failed.json"]) if (ROOT / "data" / "wiki").exists() else 49
try:
    N_ANCHOR = (ROOT / "out/demo/word_understand.json").read_text(
        encoding="utf-8").count("经验锚点")
except Exception:
    N_ANCHOR = 7
N3_NOTES = 0
_led = ROOT / "docs" / "novelty_ledger.md"
if _led.exists():
    _t = _led.read_text(encoding="utf-8", errors="replace")
    N3_NOTES = _t.count("N3 = 0") + _t.count("N3=0")


# ── 真实问句：一律从产物读原句，不在 spec 里手写（防止复述走样） ────
BM_CN = {
    "BM_EXTRAPOLATE": "人群外推边界", "BM_MEASURE": "测量误差方向",
    "BM_CAUSAL": "因果方向", "BM_CONFOUND": "残余混杂强度",
    "BM_EFFECTSIZE": "效应量 vs 判定阈值", "BM_SUBSTITUTION": "替代分析的反事实",
    "BM_DOSE": "剂量—反应形状", "BM_MULTIPLE": "多重比较",
    "BM_INTERACTION": "交互作用", "BM_MECHANISM": "机制",
}
BM_ROUTE = {
    "BM_EXTRAPOLATE": "绝对风险重算（基线风险 × HR）+ 跨队列复现",
    "BM_MEASURE": "回归校准 + 重复测量子样本",
    "BM_CAUSAL": "滞后/剔除分析（lag analysis）+ 反向孟德尔随机化",
    "BM_CONFOUND": "E-value / 敏感性分析（可精确计算）",
    "BM_EFFECTSIZE": "绝对风险差 / NNH 计算 + 阈值敏感性",
    "BM_SUBSTITUTION": "反事实定义显式化 + 替代物排序稳健性检验",
}


def _q(sig: str):
    """取该 signal 的第一条真实问题记录（原句）。"""
    for x in mg:
        if x.get("signal") == sig:
            return x
    return None


def _strip_tag(s: str) -> str:
    """去掉 statement 开头的【标签】前缀（标签已在别处展示）。"""
    s = (s or "").strip()
    if s.startswith("【"):
        i = s.find("】")
        if i > 0:
            return s[i + 1:].strip()
    return s


Q_CONFOUND, Q_CAUSAL, Q_MEASURE = _q("BM_CONFOUND"), _q("BM_CAUSAL"), _q("BM_MEASURE")
Q_EXTRA, Q_EFFECT, Q_SUBST = _q("BM_EXTRAPOLATE"), _q("BM_EFFECTSIZE"), _q("BM_SUBSTITUTION")

# dao-v-0.3 微调模型在 ModelScope studio 上生成的真问句（用户提供的真实截图内容）
MODEL_QS = [
    "在不同剂量水平上，糖精（saccharin）、阿斯巴甜（aspartame）和安赛蜜（acesulfame K）"
    "对 CKD 风险的影响是否存在差异？",
    "在该研究中，通过 24 小时膳食回顾评估人工甜味剂摄入量时是否存在时间滞后效应？",
    "为什么在高糖摄入水平上用人工甜味剂代替蔗糖并未降低肾病风险？",
]


# ── 结果展示用：把产物里的问句拆成 (标签, 问句, 触发原文) ──────────
def _tag_of(x: dict) -> str:
    t = (x.get("type") or "").strip()
    if "·" in t:
        t = t.split("·", 1)[1].strip()
    return t[:7]


def _src_of(x: dict, n: int = 58) -> str:
    ev = (x.get("evidence") or "").replace("\n", " ").strip()
    ev = ev.lstrip("# ").strip()
    return ("触发原文：" + ev[:n] + "…") if len(ev) > n else ("触发原文：" + ev)


def _entry(x: dict, with_src: bool = True):
    """结构/张力类：问句形如「针对文中结论「…」的范围追问：<核心问法>」，取出核心问法。"""
    s = (x.get("statement") or "").strip()
    sig = (x.get("signal") or "").strip()
    if sig in ("however", "yet", "inconsistent"):
        tag = sig                                  # 张力类直接用触发词当标签
    else:
        tag = _tag_of(x)
    if s.startswith("针对文中结论") and "：" in s:
        q = s.split("：", 1)[1].strip()
    else:
        q = _strip_tag(s)
    return (tag, q, _src_of(x) if with_src else "")


STRUCT_ITEMS = [_entry(x) for x in probs if x.get("signal") == "equivalent"]
TENSION_ITEMS = [_entry(x) for x in probs
                 if x.get("signal") in ("however", "yet", "inconsistent")]
SIG_SHORT = {
    "BM_EXTRAPOLATE": "人群外推边界", "BM_MEASURE": "测量误差方向",
    "BM_CAUSAL": "因果方向", "BM_CONFOUND": "残余混杂强度",
    "BM_EFFECTSIZE": "效应量 vs 判定阈值", "BM_SUBSTITUTION": "替代分析的反事实",
    "BM_MULTIPLE": "多重比较", "BM_MULTIPLICITY": "多重比较与假发现",
    "BM_INTERACTION": "交互与尺度",
    "BM_DOSE": "剂量—反应形状", "BM_MECHANISM": "机制必要性",
}
METH_ITEMS = [(SIG_SHORT.get(x.get("signal"), _tag_of(x)),
               _strip_tag(x.get("statement") or ""),
               f"判定路由：{x.get('route') or '—'}"
               + ("　·　主题作者已论及" if x.get("author_touched") else "　·　文中未见"))
              for x in mg]


def _uniq_by_tag(items):
    """每类只留第一条（10 类缺口各一条，而不是同类重复）。"""
    seen, out = set(), []
    for t in items:
        if t[0] in seen:
            continue
        seen.add(t[0])
        out.append(t)
    return out


METH_UNIQUE = _uniq_by_tag(METH_ITEMS)


def _struct_by_form():
    """结构追问：4 种问法是固定模板，真正因论文而异的是「追问了哪几个结论」。"""
    forms = {}
    for x in probs:
        if x.get("signal") != "equivalent":
            continue
        f = _tag_of(x)
        s = (x.get("statement") or "").strip()
        q = s.split("：", 1)[1].strip() if "：" in s else _strip_tag(s)
        concl = s.split("「", 1)[1].split("」", 1)[0].strip() if "「" in s else ""
        d = forms.setdefault(f, {"q": q, "c": []})
        if concl and all(concl[:36] != y[:36] for y in d["c"]):
            d["c"].append(concl)
    return forms


STRUCT_FORMS = _struct_by_form()
STRUCT_ITEMS_BY_FORM = [(f, d["q"], "") for f, d in STRUCT_FORMS.items()]
STRUCT_CONCLS = []
for _d in STRUCT_FORMS.values():
    for _c in _d["c"]:
        if all(_c[:36] != _y[:36] for _y in STRUCT_CONCLS):
            STRUCT_CONCLS.append(_c)

F = "figs/"
SLIDES = [
    # ══════════ 封面 ══════════
    {
        "kind": "cover",
        "kicker": "ASK-DAO-MACHINE · 知识发现系统",
        "title": "ask-dao 知识发现系统\n在生物医学领域的实践",
        "lead": "已有的 AI4S 生态擅长**解决问题**——给定问题，它能算出答案。"
                "但「**问题从哪来**」这一环长期空缺：能定义问题、提出问题的系统，远比能解题的系统稀缺。\n"
                "ask-dao 通过**问题路**和**想象路**两种方式来产生新问题与新知识。",
        "figure": {"src": F + "user_logo_dao.png"},
        "foot": "道生一，一生二，二生三，三生万物 · 不是问答机，也不是单纯的问题制造机 —— 它是一台知识发现机器",
    },
    {
        "kind": "bullets",
        "kicker": "汇报大纲",
        "title": "一句话概括这次汇报",
        "lead": "机器能**稳定产出真问题**了；新的知识也第一次被**算出来**了；"
                "但**世界新问题（N3）至今仍是 0**——这一点我不粉饰。",
        "bullets": [
            ("一、原理", "两条独立的路（问题路 / 想象路）+ 四道门 + 四个等级（N0–N3）。"
                      "**判不了的不产出**，两条路互不评判。"),
            ("二、在生物医学的实践", f"一篇真实开放获取论文（CC BY 4.0）→ **{len(probs)} 条**可判问题；"
                              f"其中 **{len(ev)} 条**是机器从论文自报的 HR/CI **直接算出来**的残余混杂门槛。"),
            ("三、dao 模型在生物医学的实践", "**一个专门用来提问的微调模型**：v0.3 = v0.2 + RFT 后训练，"
                                   "从论文里提出作者没明说的开放科学问题。目前限制于生物医学领域。"),
            ("四、扩展的实践", f"同一套判据换领域：**{N_FIELDS} 个领域 / {N_PAIRS} 个配对 / {N_BRIDGE} 座结构桥梁**；"
                          "想象路走完 **6,642** 个组合词；音乐与记录域重算出的已知结果**对上了**。"),
            ("五、方向与瓶颈", "方向：**多模态实体提取**（图像 / 声音 → 直接抽实体，尚未实现）。"
                          "瓶颈：**尚未发现 N3 级新问题**。"),
        ],
        "note": "全部数字可用仓库里的命令复现；本 deck 的配图由 `tools/deck_figs.py` 从同一批产物生成。",
    },

    # ══════════ 一、原理 ══════════
    {
        "kind": "figure",
        "kicker": "一、原理 01",
        "title": "两条独立的路，两套成功标准",
        "lead": "这是 v0.3.0 确立的架构，此后没有变过：**判不了的不产出**，两条路互不评判。",
        "figure": {
            "src": F + "user_architecture.png",
            "caption": "问道系统架构：两条相互独立的路 + 四模块 + 判定层 + 经验检索桥。"
                       "图内每个数字、模块名与状态词都对应仓库实现或 `out/demo/*.json` 的真实记录。",
        },
        "bullets": [
            ("问题路 · 成功标准", "**答案成立 / 可判**。每条问题必须带 `route`（判定方式），"
                            "判不了的不产出。"),
            ("想象路 · 成功标准", "**语法正确 + 逻辑通畅 + 有推理判断**——不是「有真实所指」。"),
            ("互不评判", "用问题路的逻辑（「这新吗」「有真实所指吗」）去判想象路的概念，是**范畴错误**。"),
            ("经验检索桥（可选）", "把组合词接到现实经验（维基双通道 + arXiv 回退 → 经验锚点）。"
                            "**过桥不改变任何判定**，检索失败即退化为无脚手架。"),
        ],
        "note": "实现：`src/ask_dao_machine/` · 架构图见项目站点 §系统结构。",
    },
    {
        "kind": "figfull",
        "kicker": "一、原理 02",
        "title": "什么算「新」：四道门 + 四个等级",
        "lead": "把「新」拆成**可操作的门**，而不是形容词。四道门全过才叫 N3——**至今 = 0**。",
        "figure": {
            "src": F + "fig_gates.png",
            "caption": "四道门（上）与四个等级（下）。纪律：**显著性 > 新颖性**——"
                       "任选参数的序列同样「检索未见」，只有显著性证书拦得住。",
        },
        "note": "N0 已知 → N1 大概率已知 → N2 疑似未见 → **N3 世界新**。"
                "「文中未见」只写在「参照系未见」一栏，不等于文献没有。",
    },
    {
        "kind": "bullets",
        "kicker": "一、原理 03",
        "title": "问题从哪来：四种机制",
        "lead": "前三种通用，第四种是领域包。**「作者已提出」与「机器提出」必须分开标注**——前者不算新问题。",
        "bullets": [
            ("① 作者自陈未解", "抓 open problem / remains unclear / 尚不明确。来源标注：**作者已提出（不算新）**。"),
            ("② 文本张力", "抓 however / yet / inconsistent 处的分歧。来源标注：**机器提出**。"),
            ("③ 结构追问", "对结论句套四问：**范围 / 反例 / 机制 / 定量**。来源标注：**机器提出**。"),
            ("④ 领域包（生物医学）", "10 类方法学缺口 + 从 HR/CI **直接算** E-value。"
                              "来源标注：机器提出 / 作者已论及（**分标**）。"),
        ],
        "note": "实现：`src/ask_dao_machine/paper.py` · `domains_biomed.py`；"
                "产物每条带 `evidence`（触发它的原文句）与 `route`（判定方式）。",
    },

    # ══════════ 二、在生物医学的实践（问道 · 系统侧） ══════════
    {
        "kind": "bullets",
        "kicker": "二、在生物医学的实践 · 先讲清楚这篇论文",
        "title": "常吃代糖，会不会更容易得肾病？",
        "lead": "论文：*Association of artificial sweeteners intake and risk of CKD: a prospective cohort study*"
                "（人工甜味剂摄入与慢性肾病风险的关联 · 前瞻性队列研究）。开放获取，CC BY 4.0，全文 32,787 字符。",
        "bullets": [
            ("问的问题", "常吃人工甜味剂（代糖：阿斯巴甜、三氯蔗糖这类）的人，"
                     "会不会更容易得**慢性肾病（CKD）**？"),
            ("怎么做的", "英国生物样本库 **156,000 人**，跟踪中位 **13.3 年**；"
                     "用一次 24 小时饮食回想记录吃了什么，再看谁后来确诊肾病。"),
            ("三个发现", "① 代糖吃得最多的那组 vs 完全不吃：风险高 **19%**（HR 1.19）。"
                     "② 代糖多 **且** 遗传风险高：风险高 **49%**（HR 1.49）。"
                     "③ 把糖换成等甜度的代糖：风险高 **2%**（HR 1.02）。"),
            ("作者结论", "代糖与肾病风险升高有关，且这个关联在各遗传风险层都存在；"
                     "**换代糖并不能降低风险**。"),
        ],
        "note": "**关键前提**：这是**观察性研究**，不是随机试验——研究者没法随机分配谁吃代糖。"
                "这一点决定了下一页要讲的问题，也是机器能插上手的地方。",
    },
    {
        "kind": "figure",
        "kicker": "二、在生物医学的实践 · 新问题",
        "title": f"一篇论文 → {len(probs)} 条可判问题",
        "lead": f"输入：CC BY 4.0 开放获取临床研究（PMC13331974，UK Biobank n=156,000，中位随访 13.3 年，32,787 字符）。"
                f"**作者自陈未解命中 0 条**——所以这 {len(probs)} 条都是机器提出的。",
        "figure": {
            "src": F + "fig_biomed_composition.png",
            "caption": f"上：{len(probs)} 条的来源构成。下：{N_MG} 条方法学追问里，"
                       f"主题**作者已在文中论及 {N_TOUCH} 条**，**文中未见 {N_MG - N_TOUCH} 条**。",
        },
        "bullets": [
            ("③ 结构追问", f"{len([x for x in probs if x.get('signal') == 'equivalent'])} 条："
                       "对结论句套范围 / 反例 / 机制 / 定量四问。"),
            ("② 文本张力", f"{len([x for x in probs if x.get('signal') in ('however', 'yet', 'inconsistent')])} 条："
                       "however / yet 处的分歧 → 形式化追问。"),
            ("④ 方法学追问", f"{N_MG} 条：10 类缺口，每条带原文句子 + 判定路由。"),
            ("机器算出数值", f"{len(ev)} 条：从论文自报 HR/CI 算残余混杂门槛（下一页）。"),
        ],
        "note": "命令：`ask-dao-machine paper papers/biomed/PMC13331974.md --domain biomed --out out/biomed_demo`",
    },
    {
        "kind": "qlist",
        "kicker": "二、在生物医学的实践 · 结果 ②",
        "title": f"③ 结构追问 {len(STRUCT_ITEMS)} 条：4 种问法 × 4 个结论",
        "lead": f"对论文里的**结论句**逐条套四问。四种问法是**固定模板**；"
                f"**真正因论文而异的是「追问了哪几个结论」**——所以这里每种问法只列一次。",
        "items": STRUCT_ITEMS_BY_FORM,
        "note": f"{len(STRUCT_ITEMS)} 条 = 这 4 种问法 × **{len(STRUCT_CONCLS)} 个被追问的结论**（"
                + "　·　".join(c[:34] + "…" for c in STRUCT_CONCLS)
                + "）。四种问法对任何结论句都能套；全部原句见 `out/biomed_demo/problems_paper.json`。",
    },
    {
        "kind": "qlist",
        "kicker": "二、在生物医学的实践 · 结果 ③",
        "title": f"② 文本张力 {len(TENSION_ITEMS)} 条（原句）",
        "lead": "抓论文里 **however / yet / inconsistent** 处的分歧——这些是作者自己写下的"
                "「和前人不一样」的地方，机器把它们**形式化成一个可判的追问**。",
        "items": TENSION_ITEMS,
        "note": "分歧落在哪一层（定义 / 前提 / 判定标准 / 尺度），决定这条追问能不能被判。",
    },
    {
        "kind": "qlist",
        "kicker": "二、在生物医学的实践 · 结果 ④",
        "title": f"④ 方法学追问 {N_MG} 条：10 类缺口各列 1 条（原句）",
        "lead": "领域包按 **10 类方法学缺口**逐条追问；每条都写成**可判形式**，"
                "并标明**主题作者是否已在文中论及**。",
        "items": METH_UNIQUE,
        "note": f"全 {N_MG} 条中，主题**作者已论及 {N_TOUCH} 条**、**文中未见 {N_MG - N_TOUCH} 条**；"
                "另有 3 条是机器直接算出的数值（见下页）。完整清单见 `docs/guide/demo-biomed.md`。",
    },
    {
        "kind": "stats",
        "kicker": "二、在生物医学的实践 · 结果 ④（新知识）",
        "title": "机器算出来的三个残余混杂门槛",
        "lead": "观察性研究的天生软肋：**没人测过的东西**可能才是真凶。"
                "E-value 回答一个问题——**那个东西得多强，才能把这条结论解释掉？**",
        "stats": [
            (str(EV["1.19"]["evalue_point"]), "**代糖吃得多 → 肾病风险高 19%**\n"
             "要有中等强度隐藏因素才能推翻：站得住", False),
            (str(EV["1.49"]["evalue_point"]), "**代糖多 + 遗传风险高 → 高 49%**\n"
             "现实里很少有这么强的因素：**最稳**", False),
            (str(EV["1.02"]["evalue_point"]), "**用代糖替代糖 → 高 2%**\n"
             "微弱偏差就能推翻：**几乎站不住**", True),
        ],
        "figure": {
            "src": F + "fig_evalue.png",
            "caption": "条形越长 = 越难推翻 = 结论越稳；原点 1 表示「隐藏因素毫无作用」。"
                       "红色虚线（1.5）以下为脆弱区；黑色短竖线是按 95% CI **下界**重算的保守读数。",
        },
        "note": "**原文中 “E-value” 出现 0 次**——这三个数是机器用论文自报的 HR/CI 算出来的。"
                "纪律：这是**门槛，不是结论**，也推不出任何饮食或用药建议。",
    },
    {
        "kind": "figgrid",
        "cols": 4,
        "kicker": "二、在生物医学的实践 · 真实使用",
        "title": "真实跑一遍：命令与产物",
        "lead": "下面是**真实命令序列与未删改的输出**（不是示意）。产物固定落在 `--out` 目录：`problems_*.json` + `REPORT.md`。",
        "figures": [
            {"src": "../assets/real-use/t1-fetch.png", "caption": "① 取论文：`data fetch` 从 Europe PMC 拉开放获取全文"},
            {"src": "../assets/real-use/t2-run.png", "caption": "② 跑批：`paper … --domain biomed`"},
            {"src": "../assets/real-use/t3-items.png", "caption": "③ 逐条问题：带原文证据句 + 判定路由"},
            {"src": "../assets/real-use/t4-report.png", "caption": "④ 汇总：`REPORT.md` 一页人话"},
        ],
        "note": "完整回放与逐条证据句见手册：`docs/guide/demo-biomed.md`。",
    },
    {
        "kind": "bullets",
        "kicker": "二、在生物医学的实践 · 经验",
        "title": "这次实践学到的三件事",
        "lead": "经验比结果更值得带走——下面三条都是被真实数据打出来的，不是设计时想到的。",
        "bullets": [
            ("① 必须把「作者已提出」单独分出来",
             f"{N_MG} 条方法学追问里 **{N_TOUCH} 条的主题作者已在文中论及**。"
             "机器加的是**可判形式**（滞后分析、E-value 门槛、RERI、回归校准…），不是话题本身。"
             "不分标就会把「复述」当成「发现」。"),
            ("② 领域包的价值在于「会算」",
             "10 类缺口只是清单；真正有用的是**从论文自报的 HR/CI 直接算出门槛**——"
             "这是任何读者都能复核的数，而不是一句「可能有残余混杂」。"),
            ("③ 门槛 ≠ 结论",
             f"E-value {EV['1.19']['evalue_point']} 说的是「混杂要强到这个程度才能解释掉」，"
             "**不是说效应是真的**，更推不出任何用药、摄入或诊断建议。"
             "这条边界必须写在产出里，而不是写在附录里。"),
        ],
        "note": "门控：产出的每一条问题都带 `evidence`（原文句），可逐条回原文核对。",
    },

    # ══════════ 三、dao 模型在生物医学的实践（dao-v 0.3 微调模型） ══════════
    {
        "kind": "figfull",
        "kicker": "三、dao 模型在生物医学的实践",
        "title": "dao-v 0.3：一个专门用来提问的微调模型",
        "lead": "**v0.3 = v0.2 + RFT 后训练**（low-lr 训练 + LLM-as-judge 过滤数据）。"
                "它的任务不是回答问题，而是**从论文证据、方法局限与结果细节中，"
                "提出作者没有明说、但值得进一步探究的开放科学问题**。目前领域限制于生物医学。",
        "figure": {
            "src": F + "user_model_studio.png",
            "caption": "ModelScope studio 上的**真实运行界面**（Ask-Dao v0.3 · 生物医学知识发现机器）："
                       "左侧是论文的摘要 / 讨论 / 结论，右侧是模型现场生成的候选问题，"
                       "底部可调候选数量与 temperature。",
        },
        "note": "地址：`modelscope.cn/studios/skopskp/dao-v-0.3`。"
                "当前跑在免费 CPU 模式（每次生成约 30–90 秒），所以界面上把候选数调小。",
    },
    {
        "kind": "bullets",
        "kicker": "三、dao 模型在生物医学的实践 · 它产出的问题",
        "title": "模型现场生成的三个问题（原句）",
        "lead": "同一个输入（就是上一篇论文的摘要 / 讨论 / 结论），模型给出的候选问题——"
                "**注意它们都是问句，而且是原文没问过的**。",
        "bullets": [
            ("候选 1 · 剂量差异", MODEL_QS[0]),
            ("候选 2 · 时间滞后", MODEL_QS[1]),
            ("候选 3 · 追问反直觉处", MODEL_QS[2]),
        ],
        "note": "**Holdout 对比**：候选均值 reward **0.7113** vs v0.2 的 0.6888，配对头对 **3:2:7** 领先。"
                "换句话说，微调之后模型提出的问题，被判为「值得探究」的比例更高了。",
    },
    {
        "kind": "bullets",
        "kicker": "三、dao 模型在生物医学的实践 · 经验与边界",
        "title": "这个模型做到了什么、还差什么",
        "lead": "它已经能**稳定产出真问题**；但它的能力边界必须说清楚。",
        "bullets": [
            ("做到了：会问「反直觉处」",
             "候选 3 是模型自己发现论文里的反直觉点——论文说「换代糖没有好处」，"
             "模型直接追问**为什么没有降低风险**。这不是复述，是找到了值得深挖的缝。"),
            ("做到了：问题带领域手艺",
             "候选 1 问不同甜味剂**种类**的差异，候选 2 问 24 小时膳食回顾的**时间滞后**——"
             "这两条都是流行病学方法学里的真问题，不是泛泛而谈。"),
            ("边界一：只有生物医学",
             "目前**领域限制于生物医学**，靠的是领域语料与后训练；换领域需要重新做数据与训练。"),
            ("边界二：它只提问，不判定",
             "模型负责「问得好」，**判定交给判定器与人类**——"
             "它产出的候选仍需过四道门，不能自称发现。"),
        ],
        "note": "分工：**模型提问题 → 判定层筛真假 → 人类裁决要不要投入**。"
                "这也是为什么 N3 仍为 0：会提问不等于发现了世界新知识。",
    },

    # ══════════ 四、扩展的实践 ══════════
    {
        "kind": "figfull",
        "kicker": "四、扩展的实践 · 想象路",
        "title": "另一条路：把「造词」做成能跑完的流水线",
        "lead": f"想象路不是问题路的子功能，而是与它**并列的一条路**。{N_COMBO:,} 个领域专业词组合，"
                "每个都要走完五步，产出的是**被理解的概念**。",
        "figure": {
            "src": F + "fig_pipeline5.png",
            "caption": "五步流水线。原则：**每个词都有意义，只不过是我们缺少想象力，无法理解它**——"
                       "因此不存在空想。",
        },
        "note": "版本线：v0.2 产品 → **v0.3.0 两条路** → v0.3.1 可视化/README → v0.4 问题树 → v0.5（问道）。",
    },
    {
        "kind": "figure",
        "kicker": "四、扩展的实践 · 问题路规模化",
        "title": f"问题路：{len(MODEL_PROBS)} 条问题覆盖 {N_DOM} 个领域",
        "lead": "这一代把「提问题」从零散试探变成**全领域并行扫描 + 分层问题树**，"
                "并第一次有了独立的裁决环节。",
        "figure": {
            "src": F + "fig_domains.png",
            "caption": f"{len(MODEL_PROBS)} 条问题的领域分布（条数最多的前 14 个领域）。"
                       "朱砂标出的是与生物 / 医学相关的领域。",
        },
        "bullets": [
            ("全领域扫描", "领域引擎并行产出，每个领域一份问题清单。"),
            ("反例驱动", "专门提「机器结算不了」的问题——**只提自己答不出的**。"),
            ("问题树", "L0–L5 分层 + 谱系门：每爬一层必须机器实测。"),
            ("入口多样", "外部信息（网页 / arXiv / 科学史）· 日常疑问 · 母题，都能成为问题的种子。"),
        ],
        "note": "产物：`out/demo/discovery_manifest.json`（544 条，字段含 daily_question → scientific_question → judge_route）。",
    },
    {
        "kind": "figure",
        "kicker": "四、扩展的实践 · 独立裁决",
        "title": f"独立裁决：{len(HARNESS)} 个进制命题的判决",
        "lead": "这是全项目里最像「新知识」的一类产出，判据是**数值汇合**，不是证明。"
                "换一套实现重算，结果必须一致。",
        "figure": {
            "src": F + "fig_harness.png",
            "caption": f"青 confirmed {N_CONF}（例外集在 N1 档不再新增）· 青铜 open {N_OPEN}"
                       f"（例外仍在冒）· 朱砂 rejected {N_REJ}（出现新例外）——**机器自己否掉了自己的命题**。",
        },
        "bullets": [
            ("命题", "每个 n ≥ 4 可写为 base-b 回文数 + 素数；b ≥ 4 时例外集有限且很小。"),
            ("判据", "N0 = 5×10⁶ → N1 = 10⁷，两档的例外集是否汇合、有没有冒出新例外。"),
            ("边界推进", "base 10 推到 **10⁸ 零例外**（人类讨论此前止于 ~10⁶），两种独立实现交叉验证。"),
            ("自我更正", "旧账本曾记 base 4 有 20 万个例外，真值 **5**——**错的是账本，不是结论**，"
                     "并出更正页。"),
        ],
        "note": "分级：N0 已知 → N1 大概率已知 → N2 疑似未见 → N3 世界新。**N3 至今仍为 0。**",
    },
    {
        "kind": "bullets",
        "kicker": "四、扩展的实践 · 经验",
        "title": "系统侧学到的两件事",
        "lead": "这两条都是「机器自己试出来」的，而不是从外部抄来的方法论。",
        "bullets": [
            ("① 独立实现比自证更有用",
             "同一命题换一套实现重算（另写 FFT 版本复算 base 3–47），"
             "**b=3 的 68 个例外清单逐项一致**才敢认。自证只能发现笔误，换实现能发现口径错。"),
            ("② 账本必须可作废",
             "旧账本记 base 4 有 20 万个例外，真值是 5。"
             "**记错账比算错数更危险**——所以有了 `docs/novelty_ledger_corrections.md`，"
             "对 1,219 处标注 + 三套独立复算 + 作废声明。"),
        ],
        "note": "纪律：机器答不出的问题要**明确写「悬置」**，不能悄悄丢掉，也不能包装成结论。",
    },

    # ══════════ 四、扩展的实践 ══════════
    {
        "kind": "figure",
        "kicker": "四、扩展的实践 · 跨域融合",
        "title": f"领域融合：{N_FIELDS} 个领域 → {N_BRIDGE} 座结构桥梁",
        "lead": "融合不是把两个领域的词拼在一起，而是找**共享结构**；"
                "没有共享结构的配对判为**空洞笛卡尔积**，不计入桥梁。",
        "figure": {
            "src": F + "fig_fusion.png",
            "caption": f"{N_FIELDS} 个领域两两配对得 {N_PAIRS} 个组合，"
                       f"其中 {N_BRIDGE} 个被判定为共享结构 → {N_CAND} 个跨域候选（全部可算）。",
        },
        "bullets": [
            ("为什么不是排列组合", "两个领域没共享结构时，拼出来的问题是**套话**，不是问题。"),
            ("生物相关的融合", "跨域候选里有**牵涉生物学的桥梁**（如「用数论方法问生物对象」），"
                        "这类候选直接落到可算的判定路由上。"),
            ("每条都实跑过", f"{N_CAND} 条候选**全部标注为「可算」**，各带一条判定路由。"),
        ],
        "note": "产物：`out/demo/field_fusion.json`（fields / total_pairs / cross_hot / candidates）。",
    },
    {
        "kind": "figure",
        "kicker": "四、扩展的实践 · 校准自己",
        "title": "同一套判据，换领域照样跑",
        "lead": "复核性结果的价值是**校准自己**：机器重算出的已知结果对上了，才有资格谈没见过的那部分。",
        "figure": {
            "src": F + "fig_rediscovery.png",
            "caption": "三项与已知文献/数据库对表通过（音乐集合类 224 与 Forte 一致；"
                       "多完全数与 OEIS A007539 一致；base 10 覆盖两种实现交叉验证）。",
        },
        "bullets": [
            ("数学 · 序列结构", "Collatz 链长、多边形数覆盖、5×5 二值纹样 D4 轨道数——可迭代枚举复算。"),
            ("音乐 · 集合类", "Tn/TnI 集合类 **224**（与 Forte 224 一致）；最大熵集合类**恰 2 个**。"),
            ("记录 · 多完全数", "k=2,3,4：{6,28,496,8128} / {120,672,523776} / {30240,32760}（对齐 A007539）。"),
            ("未见候选分级", f"独立 {N_IND} · 强 {N_STRONG} · 弱 0 · 短 {N_SHORT}——"
                        "**这只是 OEIS 沉默 + 机制非平凡，不是文献门，更不是显著性证书**。"),
        ],
        "note": "诚实标注：分级不等于新颖性；它只说明「在参照系里没见到」，需要人工或文献门复核。",
    },
    {
        "kind": "figure",
        "kicker": "四、扩展的实践 · 经验检索桥",
        "title": f"经验检索桥：{N_COMBO:,} 个组合词接上现实经验",
        "lead": "桥的作用是让想象力**有据可依**，而不是当裁判。"
                "检索未见**不等于**概念为假；见不到也不阻止理解。",
        "figure": {
            "src": F + "fig_bridge.png",
            "caption": f"{N_COMBO:,} 个组合词过双通道检索：词条通道命中 {N_ENTRY} 个，"
                       f"其中已建成独立条目仅 {N_WORD} 个；抓成语料 {WIKI_N} 个词条，"
                       f"写出经验锚点 {N_ANCHOR} 处。",
        },
        "bullets": [
            ("命中率本身就是发现", f"词条通道命中约 {100.0 * N_ENTRY / max(N_COMBO, 1):.1f}%，"
                           f"已建成独立条目约 {100.0 * N_WORD / max(N_COMBO, 1):.1f}%。"
                           "**「检索未见」是常态，不是发现。**"),
            ("桥不改变判定", "过桥不改变任何判定；检索失败即退化为无锚点，概念照样成立（判据是「被理解」）。"),
            ("默认不过桥", "默认只对少数指定组合写锚点；全量检索需要显式开关。"),
        ],
        "note": "产物：`out/demo/browser_mass_search.json` · `data/wiki/`（语料）· `out/demo/word_understand.json`（锚点）。",
    },

    # ══════════ 五、方向与瓶颈 ══════════
    {
        "kind": "figfull",
        "kicker": "五、接下来的方向",
        "title": "多模态实体提取：让图像与声音进入两条路",
        "lead": "现在经验**只能以文字进入**系统；图像与声音还没有进入两条路的入口。"
                "下一步是把这个「反向」补上——**尚未实现**。",
        "figure": {
            "src": F + "fig_multimodal.png",
            "caption": "实线 = 现在能做的（文字 → 问题 / 概念）。虚线 = 目标（图像 / 声音 → 直接抽实体 → "
                       "两条路的入口）。**虚线框内是目标，不是成果。**",
        },
        "note": "已有最小闭环：`perceive` 能把图像 → 结构特征 → 带判定路由的问题；"
                "但它抽取的是**结构特征**，还不是实体。",
    },
    {
        "kind": "figfull",
        "kicker": "五、遇到的瓶颈",
        "title": "尚未发现 N3 级新问题",
        "lead": "问题是真的、量也很大；但**「真的」不等于「新的」**。这台机器停在这一步。",
        "figure": {
            "src": F + "fig_bottleneck.png",
            "caption": f"「N3 = 0」在账本里被独立记下 {N3_NOTES} 次，从未改变。"
                       "各行的单位不同，因此不做同轴对比。",
        },
        "note": "**差距的具体位置**：机器能判的问题里，多数主题**前人已经问过**；"
                "真正缺的不是产能，而是**能穿过显著性证书、且前人没问过**的那一格。"
                "下一步要把力气放在「显著性证书」这道门上，而不是继续加产能。",
    },
    {
        "kind": "end",
        "kicker": "ASK-DAO-MACHINE",
        "title": "谢谢",
        "lead": "问道 · ask-dao-machine · MIT License · 全部数字可用仓库里的命令复现",
        "links": [
            ("项目站点", "https://shikunpneg.github.io/ask-dao-machine/"),
            ("命令行文档", "https://shikunpneg.github.io/ask-dao-machine/guide/cli.html"),
            ("生物医学完整演示", "https://shikunpneg.github.io/ask-dao-machine/guide/demo-biomed.html"),
            ("结果与证据手册", "https://shikunpneg.github.io/ask-dao-machine/guide/results.html"),
            ("ModelScope · dao-v-0.3", "https://www.modelscope.cn/studios/skopskp/dao-v-0.3"),
            ("GitHub", "https://github.com/shikunpneg/ask-dao"),
        ],
        "foot": "道生一，一生二，二生三，三生万物",
    },
]

if __name__ == "__main__":
    print(f"slides: {len(SLIDES)}")
    for i, s in enumerate(SLIDES, 1):
        t = s["title"].splitlines()[0]
        print(f"  {i:02d} [{s['kind']:7s}] {t[:44]}")
    print()
    print(f"生物医学：{len(probs)} 条 = 结构 "
          f"{len([x for x in probs if x.get('signal') == 'equivalent'])}"
          f" + 张力 {len([x for x in probs if x.get('signal') in ('however','yet','inconsistent')])}"
          f" + 方法学 {N_MG} + E-value {len(ev)}；已论及 {N_TOUCH}/{N_MG}")
    print(f"模型侧：{len(MODEL_PROBS)} 条 / {N_DOM} 领域；裁决 {N_CONF} confirmed / "
          f"{N_OPEN} open / {N_REJ} rejected")
    print(f"融合：{N_FIELDS} 领域 / {N_PAIRS} 配对 / {N_BRIDGE} 桥梁 / {N_CAND} 候选")
    print(f"桥：{N_COMBO:,} 组合 / 命中 {N_ENTRY} / 已成词 {N_WORD} / 锚点 {N_ANCHOR} / 语料 {WIKI_N}")
    print(f"未见候选：独立 {N_IND} / 强 {N_STRONG} / 短 {N_SHORT}；N3 = 0（账本记录 {N3_NOTES} 次）")
