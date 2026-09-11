# -*- coding: utf-8 -*-
"""domains_biomed.py — 生物医学领域包：把论文里的**方法学缺口**变成可判问题。

设计原则（诚实优先）：
  1. 每条问题都**不主张「世界新」**——它是「把文中某个方法学缺口写成可判形式」。
  2. 区分两种来源：
       author_touched = True  —— 作者已在局限/讨论里碰到（机器只做形式化，不算机器提出）
       author_touched = False —— 文中没提，机器提出（仍需人工核对是否已有文献）
  3. 每条都必须带 route：一个可执行/可查证的判定方式（E-value、滞后分析、剂量梯度、
     回归校准…），否则就是空担心，不产出。

规则字段: code / name / 触发信号 / 追问 / 判定路由
"""
from __future__ import annotations

import re

# 作者已触及的口吻（出现在同一句里 → 记为 author_touched）
AUTHOR_TOUCHED = [
    r"limitation", r"cannot be excluded", r"residual confound", r"unmeasured confound",
    r"we acknowledge", r"should be interpreted with caution", r"not establish caus",
    r"reverse caus", r"remains? (uncertain|unclear)", r"may be subject to",
    r"局限", r"不能排除", r"有待", r"尚不明确", r"谨慎解释",
]

BIOMED_RULES = [
    {
        "code": "BM_CAUSAL",
        "name": "因果方向",
        "patterns": [
            r"associated with", r"association between", r"increased risk of", r"linked to",
            r"predicts? (the )?(risk|incidence|outcome)", r"contributed to",
            r"与.{0,12}(相关|有关)", r"增加.{0,8}风险",
        ],
        "question": ("文中给出的是关联，但设计默认了 X→Y 的方向：反向因果"
                     "（结局或早期病变改变了暴露）能否解释该效应？用可检验的形式说："
                     "把随访前 k 年发生的事件剔除（lag 分析），效应量随 k 如何变化？"
                     "若 k≥2 年就衰减到 1，说明什么？"),
        "route": "滞后/剔除分析（lag analysis）+ 反向孟德尔随机化",
    },
    {
        "code": "BM_CONFOUND",
        "name": "残余混杂强度",
        "patterns": [
            r"propensity score", r"adjusted for", r"fully adjusted", r"confound\w*",
            r"cox (regression|model)", r"multivariable", r"covariat",
            r"校正", r"混杂",
        ],
        "question": ("该效应是「已调整」之后剩下的：残余混杂要多强才能把它解释掉？"
                     "把它写成可算的形式：给定效应量与置信区间，算 E-value"
                     "（未测混杂与暴露、结局的关联强度各自要达到多少，才能把效应推到无效），"
                     "并给出最小混杂强度数值。"),
        "route": "E-value / 敏感性分析（可精确计算）",
    },
    {
        "code": "BM_DOSE",
        "name": "剂量—反应形状",
        "patterns": [
            r"dose[- ]response", r"quartile", r"tertile", r"categor\w+ of (intake|exposure)",
            r"per (1|one) (sd|serving|unit)", r"highest vs\.? (the )?lowest",
            r"剂量", r"四分位",
        ],
        "require": [r"intake", r"consumption", r"exposure", r"\bdose", r"serving",
                    r"g/day", r"dietary", r"摄入", r"暴露"],
        "question": ("文中把暴露分组比较，但没有给出函数形状：单调、阈值，还是非单调"
                     "（低剂量有益、高剂量有害）？写成可判形式：在连续暴露上拟合样条"
                     "/分段模型，检验非线性（P-nonlinear），给出拐点位置与其置信区间。"),
        "route": "限制立方样条 + 非线性检验（拐点估计）",
    },
    {
        "code": "BM_EXTRAPOLATE",
        "name": "人群外推边界",
        "patterns": [
            r"uk biobank", r"participants? (were|from|of)", r"cohort of \d",
            r"european ancestry", r"volunteer", r"single[- ]cent(er|re)", r"nationwide",
            r"队列", r"人群",
        ],
        "question": ("该效应量是在特定人群里测出来的：换人群（不同族裔、不同基线风险、"
                     "志愿者偏健康的「健康志愿者效应」）后，是效应量缩放，还是方向都可能翻转？"
                     "写成可判形式：给出该效应在不同基线风险下的绝对风险差，"
                     "并说明在什么基线风险下绝对危害为零。"),
        "route": "绝对风险重算（基线风险 × HR）+ 跨队列复现",
    },
    {
        "code": "BM_EFFECTSIZE",
        "name": "效应量 vs 判定阈值",
        "patterns": [
            r"\bHR\b", r"hazard ratio", r"odds ratio", r"\bOR\b", r"95%\s*CI",
            r"risk ratio", r"effect size", r"相对风险",
        ],
        "question": ("由 HR 与 95% CI 直接给出：这个效应量有没有超过事先设定的"
                     "决策阈值（临床/公共卫生意义上的）？换算成绝对尺度"
                     "（每千人年多/少多少事件）、以及使结论翻转所需的最小偏倚或最小随访时间。"),
        "route": "绝对风险差 / NNH 计算 + 阈值敏感性",
    },
    {
        "code": "BM_MEASURE",
        "name": "测量误差方向",
        "patterns": [
            r"24[- ]h (dietary )?recall", r"self[- ]report", r"questionnaire",
            r"food frequency", r"measurement error", r"assay", r"batch effect",
            r"inter[- ]?observer", r"自报", r"问卷", r"测量误差",
        ],
        "question": ("暴露/结局是自报或单次测量的：这类误差是**非差异性**（把效应推向无效、低估）"
                     "还是**差异性**（可能制造假阳性）？写成可判形式：用重复测量做回归校准，"
                     "报告校准系数与校准后的效应量；若校准后效应变大，说明原结论被低估。"),
        "route": "回归校准（regression calibration）+ 重复测量子样本",
    },
    {
        "code": "BM_SUBSTITUTION",
        "name": "替代分析的反事实",
        "patterns": [
            r"substitution", r"replacing .{0,20} with", r"instead of", r"iso[- ]?caloric",
            r"替代", r"换成",
        ],
        "question": ("替代模型的结论依赖「对照是什么」：把 A 换成 B，与「把 A 拿掉」、"
                     "「A 换成 C」是两个不同的反事实，效应量不可互换。"
                     "写成可判形式：明确反事实集，并检验结论在该反事实集内是否稳健"
                     "（不同替代物之间的排序是否一致）。"),
        "route": "反事实定义显式化 + 替代物排序稳健性检验",
    },
    {
        "code": "BM_INTERACTION",
        "name": "交互尺度与多重比较",
        "patterns": [
            r"interaction", r"polygenic risk score", r"joint effect", r"synerg\w+",
            r"stratified by", r"modif\w+ (the )?effect", r"交互", r"效应修饰",
        ],
        "require": [r"interaction", r"\bjoint\b", r"synerg\w+", r"combined effect",
                    r"effect modif", r"P-interaction", r"交互"],
        "require2": [r"\brisk\b", r"effect", r"associat", r"\bHR\b", r"\bOR\b",
                     r"hazard", r"odds", r"exposure", r"incidence"],
        "question": ("联合暴露的「最高风险组」是相加还是相乘？写成可判形式："
                     "在**加性与乘性两种尺度**上分别检验交互，报告 RERI / 交互 HR "
                     "及 P-interaction；并说明该交互是否通过了多重比较校正"
                     "（未校正的亚组交互是最常见的假阳性来源）。"),
        "route": "加性/乘性交互分解（RERI）+ 多重比较校正",
    },
    {
        "code": "BM_MULTIPLICITY",
        "name": "多重比较与假发现",
        "patterns": [
            r"sensitivity analys", r"subgroup", r"secondary (outcome|analysis)",
            r"exploratory", r"multiple (comparisons|testing)", r"false discovery|FDR",
            r"敏感性分析", r"亚组",
        ],
        "question": ("文中做了多少个亚组/敏感性/次要结局检验？写成可判形式："
                     "报告检验总数与假发现率曲线，给出「FDR=5% 下仍然成立」的结论清单；"
                     "若某一敏感性分析翻转结论，说明翻转阈值在哪里。"),
        "route": "多重比较清单化 + FDR 曲线 + 翻转阈值",
    },
    {
        "code": "BM_MECHANISM",
        "name": "机制的必要性/充分性",
        "patterns": [
            r"mechanis\w+", r"pathway", r"signaling", r"inflammat\w+", r"oxidative stress",
            r"microbiom\w+", r"upregulat\w+", r"downregulat\w+",
            r"\bmediat(e|es|ed|ing|ion|ions|or|ors)\b",
            r"机制", r"通路", r"介导",
        ],
        "question": ("文中提到机制但不区分**必要性**与**充分性**：敲掉该通路，效应是否消失"
                     "（必要）？单独激活该通路，是否足以复制效应（充分）？"
                     "写成可判形式：给出两问各自的实验设计（KO + rescue / 激活剂），"
                     "以及在人样本上可观察的中间量。"),
        "route": "必要性与充分性实验设计（KO+rescue）+ 中介分析",
    },
]

# 概念词（不是触发词）：作者真的讨论了那件事才会出现 → 那些主题机器不主张首先提出
TOUCHED_CONCEPTS = {
    "BM_CAUSAL": [r"reverse caus", r"bidirectional", r"temporal (order|sequence|relationship)",
                  r"preclinical", r"latent disease", r"反向因果"],
    "BM_CONFOUND": [r"residual confound", r"unmeasured confound", r"confounding by",
                    r"\bE-value\b", r"cannot be excluded", r"unmeasured covariates",
                    r"残余混杂"],
    "BM_DOSE": [r"dose[- ]response", r"non[- ]?linear", r"spline", r"threshold effect",
                r"restricted cubic", r"剂量"],
    "BM_EXTRAPOLATE": [r"generalizab", r"generalisab", r"external validity",
                       r"other populations", r"different ancestr", r"extrapolat"],
    "BM_EFFECTSIZE": [r"absolute risk", r"number needed", r"clinical significance",
                      r"minimal(ly)? (clinically )?important", r"public health impact"],
    "BM_MEASURE": [r"measurement error", r"misclassif", r"regression calibration",
                   r"validity of the (questionnaire|recall|measure)", r"measurement error"],
    "BM_SUBSTITUTION": [r"substitution (model|analysis)", r"iso[- ]?caloric",
                        r"replacing .{0,30} with", r"substituting"],
    "BM_INTERACTION": [r"interaction", r"effect modif", r"P-interaction", r"\bRERI\b",
                       r"additive scale", r"multiplicative scale"],
    "BM_MULTIPLICITY": [r"multiple (comparisons|testing)", r"false discovery", r"\bFDR\b",
                        r"bonferroni", r"subgroup analys", r"sensitivity analys"],
    "BM_MECHANISM": [r"mechanis", r"pathway", r"oxidative stress", r"inflammat",
                     r"microbiom", r"中介"],
}

_COMPILED = [(r, [re.compile(p, re.I) for p in r["patterns"]],
              [re.compile(p, re.I) for p in r.get("require", [])],
              [re.compile(p, re.I) for p in r.get("require2", [])],
              [re.compile(p, re.I) for p in AUTHOR_TOUCHED]) for r in BIOMED_RULES]

# ── ⑤ 机器算：从论文自报的效应量直接算残余混杂强度（E-value）────────
# 公式（Ding & VanderWeele 2016）：E = RR + sqrt(RR·(RR−1))，RR≥1；RR<1 取倒数。
# 诚实前提：以 HR/OR 近似 RR，要求结局不常见；不满足时 E-value 会偏大（更保守）。
_EFFECT = re.compile(
    r"\b(HR|hazard ratio|OR|odds ratio|RR|risk ratio|relative risk)\b"
    r"[^.;()]{0,40}?(\d+\.\d+)\s*[,(]?\s*(?:95%\s*CI|CI)[:\s]*"
    r"(\d+\.\d+)\s*[−–—\-]\s*(\d+\.\d+)", re.I)


def evalue(rr: float) -> float:
    """E-value：残余混杂需同时与暴露、结局达到的关联强度。"""
    r = rr if rr >= 1 else 1.0 / rr
    return r + (r * (r - 1.0)) ** 0.5


def evalue_items(text: str, source: str, max_items: int = 3) -> list[dict]:
    out, seen = [], set()
    for m in _EFFECT.finditer(text):
        if len(out) >= max_items:
            break
        kind, point, lo, hi = m.group(1), float(m.group(2)), float(m.group(3)), float(m.group(4))
        if not (0 < lo < point < hi) or point <= 1:
            continue
        key = (kind.upper(), point)
        if key in seen:
            continue
        seen.add(key)
        e_pt, e_ci = evalue(point), evalue(lo)        # CI 界更接近 1 的一侧 → 更小、更关键
        sent = re.sub(r"\s+", " ", m.group(0))
        if "(" in sent and ")" not in sent:
            sent += ")"
        ctx = text[max(0, m.start() - 180):m.end() + 60]
        ctx = re.sub(r"\s+", " ", ctx)[:200]
        out.append({
            "id": f"BM_EV{len(out)+1:02d}",
            "source": source,
            "domain": "生物医学",
            "type": "④方法学追问·残余混杂强度（机器算出）",
            "is_author_stated": False,
            "author_touched": False,
            "signal": "BM_EVALUE",
            "evidence": f"文中数值：{sent}　← 上下文：…{ctx}…",
            "computed": {"effect_type": kind, "point": point, "ci": [lo, hi],
                         "evalue_point": round(e_pt, 2), "evalue_ci_bound": round(e_ci, 2),
                         "formula": "E = RR + sqrt(RR(RR-1))，RR 用 HR/OR 近似（结局须不常见）"},
            "statement": (f"机器算出：文中 {kind}={point}（95% CI {lo}–{hi}）要被称为残余混杂解释掉，"
                          f"未测混杂必须与暴露、结局各自达到 RR≈{e_pt:.2f} 的关联"
                          f"（按置信区间下界则是 RR≈{e_ci:.2f}）。"
                          f"→ 追问：在这份数据里，能否找出关联强度达到该量级的未测混杂候选？"
                          f"用阴性对照结局（negative control outcome）能否把该量级排除？"),
            "route": "E-value 门槛 + 阴性对照结局 + 已测协变量关联强度排行（可精确复核）",
            "status": "机器算出（数值可复核）",
            "novelty_note": ("不主张世界新：这是对论文自报数字的算术换算（E-value 敏感性分析），"
                             "数值可被任何人复核；它给出的是一个门槛，不是一个发现"),
        })
    return out

_VOCAB = [r"\bpatients?\b", r"\bcohort\b", r"\bclinical", r"biomarker", r"\bHR\b",
          r"hazard ratio", r"odds ratio", r"randomi[sz]ed", r"placebo", r"\btrial\b",
          r"\bassay\b", r"\bgenes?\b", r"\bproteins?\b", r"\bcells?\b", r"\bmice\b",
          r"\bin vitro\b", r"\bserum\b", r"\bplasma\b", r"\bdisease\b", r"\bmortality\b",
          r"\bincidence\b", r"\bexposure\b", r"\brisk of\b", r"\bdietary\b"]
_VOCAB_C = [re.compile(p, re.I) for p in _VOCAB]


def detect_vocab(text: str) -> int:
    """生物医学词表命中数（用于自动判领域）。"""
    return sum(len(p.findall(text)) for p in _VOCAB_C)


def touched_codes(text: str) -> set[str]:
    """作者是否已在文中论及该**主题概念**（不只是触发词）。

    判据用「概念词」而不是规则的触发词：触发词（如 associated with）到处都是，
    用它会几乎全部命中；概念词（如 reverse causality / RERI / regression calibration）
    只会在作者真的讨论了那件事时出现。
    命中 → 机器**不主张该主题是它首先提出的**，只主张"把它写成了可判形式"。
    """
    hit = set()
    for code, pats in TOUCHED_CONCEPTS.items():
        if any(re.search(p, text, re.I) for p in pats):
            hit.add(code)
    return hit


def mine(text: str, source: str, sentence_iter, max_per_rule: int = 3) -> list[dict]:
    """对论文文本套生物医学方法学追问；sentence_iter 由调用方传入（共享分句逻辑）。"""
    out: list[dict] = evalue_items(text, source)
    touched_area = touched_codes(text)
    seen = set()
    counters: dict[str, int] = {}
    for sent in sentence_iter:
        for rule, pats, requires, requires2, touched_pats in _COMPILED:
            if counters.get(rule["code"], 0) >= max_per_rule:
                continue
            if not any(p.search(sent) for p in pats):
                continue
            if requires and not any(p.search(sent) for p in requires):
                continue
            if requires2 and not any(p.search(sent) for p in requires2):
                continue
            touched = any(p.search(sent) for p in touched_pats)
            area = rule["code"] in touched_area
            key = (rule["code"], sent[:70])
            if key in seen:
                break
            seen.add(key)
            counters[rule["code"]] = counters.get(rule["code"], 0) + 1
            if area and not touched:
                note = ("不主张该主题为机器首先提出：作者已在文中论及该概念；"
                        "机器贡献的是把它**写成可判形式**（见 route），而不是这个话题本身")
            elif touched:
                note = "不主张该主题为机器首先提出：作者同句已触及；机器把形式加强为可判问题"
            else:
                note = "不主张世界新：文中未见该主题，机器提出；仍需人工核对是否已有文献"
            out.append({
                "id": f"{rule['code']}{counters[rule['code']]:02d}",
                "source": source,
                "domain": "生物医学",
                "type": f"④方法学追问·{rule['name']}",
                "is_author_stated": False,
                "author_touched": bool(touched or area),
                "signal": rule["code"],
                "evidence": sent,
                "statement": f"【{rule['name']}】{rule['question']}",
                "route": rule["route"],
                "status": "待实验/待数据（可判）",
                "novelty_note": note,
            })
            break
    return out
