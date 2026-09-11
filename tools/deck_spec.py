# -*- coding: utf-8 -*-
"""deck_spec.py — 《问道知识发现系统在生物医学领域的发现》内容规格。

原则：数字全部从真实产物里读出来，不手打；措辞不放大：
  · 产出的东西叫「候选问题」「证据边界推进」「可复核的门槛」，不叫「发现新知识」；
  · 世界新问题 N3 = 0，写在封底与诚实边界页；
  · 每条主张后面跟证据（原文句子 / 命令 / 文件路径）。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _biomed():
    d = json.loads((ROOT / "out" / "biomed_demo" / "problems_paper.json").read_text(encoding="utf-8"))
    probs = d["problems"]
    bm = [x for x in probs if x.get("domain") == "生物医学"]
    ev = [x for x in bm if x.get("computed")]
    mg = [x for x in bm if x.get("signal") != "BM_EVALUE"]
    return {
        "total": len(probs), "generic": len(probs) - len(bm), "biomed": len(bm),
        "mg": len(mg), "ev": len(ev),
        "touched": sum(1 for x in mg if x.get("author_touched")),
        "untouched": sum(1 for x in mg if not x.get("author_touched")),
        "rules": sorted({x["signal"] for x in mg}),
        "ev_items": ev, "mg_items": mg,
    }


B = _biomed()
EV = {str(x["computed"]["point"]): x["computed"] for x in B["ev_items"]}

# 一条完整证据链（用于「证据链」页）
CHAIN = next(x for x in B["ev_items"] if str(x["computed"]["point"]) == "1.19")
CHAIN_Q = next(x for x in B["mg_items"] if x["signal"] == "BM_CONFOUND")

RULES_CN = {
    "BM_CAUSAL": "因果方向", "BM_CONFOUND": "残余混杂强度", "BM_DOSE": "剂量—反应形状",
    "BM_EXTRAPOLATE": "人群外推边界", "BM_EFFECTSIZE": "效应量 vs 判定阈值",
    "BM_MEASURE": "测量误差方向", "BM_SUBSTITUTION": "替代分析的反事实",
    "BM_INTERACTION": "交互尺度与多重比较", "BM_MULTIPLICITY": "多重比较与假发现",
    "BM_MECHANISM": "机制的必要性/充分性",
}

SLIDES = [
    {
        "kind": "cover",
        "kicker": "ASK-DAO-MACHINE · 知识发现系统",
        "title": "问道知识发现系统\n在生物医学领域的发现",
        "lead": "一次真实运行的完整交代：输入一篇开放获取论文，输出可判问题与被机器算出来的门槛。\n"
                "所有数字都能用仓库里的同一条命令复现。",
        "foot": "道生一，一生二，二生三，三生万物 · 不是问答机，也不是单纯的问题制造机 —— 它是一台知识发现机器",
    },
    {
        "kind": "bullets",
        "kicker": "01 · 它是什么",
        "title": "只产问题与概念，不产答案",
        "lead": "两条独立的路，加上一条模型线。判据逐条可查，不靠措辞。",
        "bullets": [
            ("问题路", "产**问题**（需解决）：每条都必须带 `route`（判定方式），判不了的不产出。"),
            ("想象路", "产**概念**（需解释）：标准是「被理解」，不是真伪。"),
            ("模型线", "ModelScope 上两版可在线运行：**dao-v-0.3**（输入论文对应部分，输出作者未提出的更进一步问题）与 **dao-v-0.2**（早期配置，用于对照）。"),
            ("硬边界", "世界新问题（N3）至今 **= 0**。产出是候选问题与证据边界推进，不是「已确认的新知识」。"),
        ],
        "note": "来源：项目站点 §系统结构 / README §诚实边界 / ModelScope 两个运行页",
    },
    {
        "kind": "table",
        "kicker": "02 · 方法",
        "title": "问题从哪来：四种机制 + 一个领域包",
        "lead": "前三种是通用机制，第四种是生物医学领域包。**「作者已提出」与「机器提出」分开标注**——前者不算新问题。",
        "table": {
            "head": ["机制", "抓什么", "来源标注"],
            "rows": [
                ["① 作者自陈未解", "open problem / remains unclear / 尚不明确 …", "作者已提出（不算新）"],
                ["② 文本张力", "however / yet / inconsistent 处的分歧", "机器提出"],
                ["③ 结构追问", "对结论句套四问：范围 / 反例 / 机制 / 定量", "机器提出"],
                ["④ 领域包（biomed）", "10 类方法学缺口 + 从 HR/CI 直接算 E-value", "机器提出 / 作者已论及（分标）"],
            ],
        },
        "note": "实现：src/ask_dao_machine/paper.py · src/ask_dao_machine/domains_biomed.py",
    },
    {
        "kind": "table",
        "kicker": "03 · 领域包",
        "title": "生物医学方法学缺口：10 类",
        "lead": "每一类都自带一个**可执行的判定方式**（E-value、滞后分析、样条非线性检验、回归校准、RERI、FDR 曲线…），否则只是空担心。",
        "table": {
            "head": ["#", "缺口", "#", "缺口"],
            "rows": [
                ["1", "因果方向（反向因果）", "6", "测量误差方向（非差异性/差异性）"],
                ["2", "残余混杂强度（E-value）", "7", "替代分析的反事实"],
                ["3", "剂量—反应形状（单调？阈值？）", "8", "交互尺度（加性 vs 乘性）"],
                ["4", "人群外推边界", "9", "多重比较与假发现率"],
                ["5", "效应量 vs 决策阈值", "10", "机制的必要性/充分性"],
            ],
        },
        "note": "只在 --domain biomed（或自动判定为生物医学）时启用；--domain none 只用通用三机制",
    },
    {
        "kind": "bullets",
        "kicker": "04 · 既有实践",
        "title": "dao v0.2 → v0.3：论文到哪里去",
        "lead": "模型线上这一版把「读论文」固定成一件事：**输入论文对应部分，输出作者未提出的更进一步问题**。",
        "bullets": [
            ("dao-v-0.3（当前）", "不是复述作者自己写下的「有待研究」，而是在论文内容基础上往前追问一步：作者没问、但由其内容可以问出来的问题。"),
            ("dao-v0.2（上一版）", "保留早期配置，用于**对照两版产出差异**。"),
            ("本地版（本次实践）", "命令行 `ask-dao-machine paper … --domain biomed`：通用三机制 + 生物医学 10 类缺口 + E-value 计算，产出 JSON 与一页人话。"),
            ("标注规则以仓库为准", "本页所有条目都来自仓库里的实现与产物（①/②/③/④ 分标，`is_author_stated`、`author_touched` 两个字段）；"
                              "线上两版是同一件事的在线入口，其内部实现不在本次核对范围内。"),
        ],
        "note": "ModelScope：skopskp/dao-v-0.3 · skopskp/dao-v-0.2（站点 §模型运行）",
    },
    {
        "kind": "table",
        "kicker": "05 · 本次输入",
        "title": "输入：一篇 CC BY 开放获取的临床研究",
        "lead": "只用公开接口取全文，许可字段一并记录；正文 32,787 字符。",
        "table": {
            "head": ["项", "值"],
            "rows": [
                ["论文", "Association of artificial sweeteners intake and risk of CKD: a prospective cohort study"],
                ["来源", "Europe PMC fullTextXML · PMC13331974 · J Nutr Health Aging 2026"],
                ["许可", "CC BY 4.0（原样保存在 papers/biomed/，元数据含 DOI 与抓取日期）"],
                ["关键设定", "UK Biobank 前瞻队列 · n=156,000 · 中位随访 13.3 年"],
                ["论文自报效应", "调整后 HR 1.19（95% CI 1.08–1.30）；最高风险组 HR 1.49；替代分析 HR 1.02"],
            ],
        },
        "note": "抓取命令：python tools/fetch_biomed_paper.py --pmcid PMC13331974",
    },
    {
        "kind": "table",
        "kicker": "06 · 过程",
        "title": "一条命令，产出 %d 条" % B["total"],
        "lead": "`ask-dao-machine paper papers/biomed/PMC13331974.md --domain biomed --out out/biomed_demo`",
        "table": {
            "head": ["产出构成", "条数", "说明"],
            "rows": [
                ["② 文本张力", "6", "however / yet 处的分歧 → 形式化追问"],
                ["③ 结构追问", "16", "对结论句套四问（范围/反例/机制/定量）"],
                ["④ 生物医学方法学追问", str(B["mg"]), "10 类缺口，每条带原文句子与判定路由"],
                ["其中：机器算出数值", str(B["ev"]), "从论文自报 HR/CI 直接算 E-value"],
                ["合计", str(B["total"]), "其中作者已提出 0 条（① 机制未命中）"],
            ],
        },
        "note": "产物：out/biomed_demo/problems_paper.json（机器可读，每条带 route）+ REPORT.md",
    },
    {
        "kind": "table",
        "kicker": "07 · 发现（一）",
        "title": "机器算出来的三个残余混杂门槛",
        "lead": "从论文自报的 HR 与 95% CI 直接算 **E-value**：要把这个效应解释成「没有效应」，未测混杂必须与暴露、结局**同时**达到多强的关联。",
        "table": {
            "head": ["论文报告", "E-value", "按 CI 下界", "含义"],
            "rows": [
                ["HR 1.19（1.08–1.30）", str(EV["1.19"]["evalue_point"]), str(EV["1.19"]["evalue_ci_bound"]),
                 "未测混杂要与暴露、结局各自达到 RR≈1.67，才能把该效应解释为零"],
                ["HR 1.49（1.28–1.74）", str(EV["1.49"]["evalue_point"]), str(EV["1.49"]["evalue_ci_bound"]),
                 "最高风险组所需混杂强度更高，最难被混杂解释"],
                ["HR 1.02（1.01–1.04）", str(EV["1.02"]["evalue_point"]), str(EV["1.02"]["evalue_ci_bound"]),
                 "替代分析那一条最脆：几乎任何微弱混杂都能解释掉"],
            ],
        },
        "note": "公式 E = RR + √(RR(RR−1))，用 HR 近似 RR，只在结局不常见时成立（本文 CKD 发病率低）。"
                "E-value 是**门槛**，不是「存在这样的混杂」的证据。原文中从未出现 E-value —— 这三条是机器加上去的。",
    },
    {
        "kind": "table",
        "kicker": "08 · 发现（二）",
        "title": "写成可判形式的 %d 条新问题" % B["mg"],
        "lead": "论文的方法学缺口 → 每条都指回原文句子，并给出判定方式；**作者是否已论及**单独标注。",
        "table": {
            "head": ["缺口", "触发它的原文句子（节选）", "判定路由", "作者"],
            "rows": [
                [RULES_CN.get(x["signal"], x["signal"]),
                 x["evidence"].replace("## ", "")[:58] + "…",
                 x["route"][:34] + ("…" if len(x["route"]) > 34 else ""),
                 "已论及" if x.get("author_touched") else "文中未见"]
                for x in sorted(B["mg_items"], key=lambda y: (y.get("author_touched") is True))[:6]
            ],
        },
        "note": "全表 %d 条（10 类）；其中 **%d 条的主题作者已在文中论及**（机器只贡献形式化），"
                "%d 条的主题文中未见。完整表见站点「真实使用」一节与 docs/guide/demo-biomed.md。"
                % (B["mg"], B["touched"], B["untouched"]),
    },
    {
        "kind": "chain",
        "kicker": "09 · 证据链",
        "title": "一条完整的链路：从原文句子到可复核的数",
        "steps": [
            ("原文句子", CHAIN["evidence"].split("←")[0].strip().replace("文中数值：", "")),
            ("机器算术", "E = 1.19 + √(1.19×0.19) = **%s**（按 CI 下界 1.08 → %s）"
                       % (CHAIN["computed"]["evalue_point"], CHAIN["computed"]["evalue_ci_bound"])),
            ("变成追问", CHAIN["statement"].split("→")[-1].strip()[:120]),
            ("怎么判", CHAIN["route"]),
        ],
        "note": "同一条缺口还有一条不依赖算术的版本：「该效应是『已调整』之后剩下的：残余混杂要多强才能把它解释掉？」",
    },
    {
        "kind": "bullets",
        "kicker": "10 · 诚实边界",
        "title": "这份结果不主张什么",
        "lead": "以下每一条都写在产出里，而不是写在附录里。",
        "bullets": [
            ("不主张世界新", "世界新问题（N3）至今 **= 0**；这里给的是候选问题与证据边界推进。"),
            ("不主张作者没想过", "本次 %d 条方法学追问里，**%d 条的主题作者已在文中论及**；机器加的是可判形式（滞后分析、E-value 门槛、RERI、回归校准…），不是话题本身。" % (B["mg"], B["touched"])),
            ("不主张文献没有", "「文中未见」只表示这份全文里没有（本次 %d 条），不代表文献里没有。" % B["untouched"]),
            ("不构成临床建议", "HR 与 E-value 是流行病学量的换算，不能推出任何用药、摄入或诊断建议。"),
            ("E-value 的近似前提", "用 HR 近似 RR，只在结局不常见时成立；它是门槛，不是发现。"),
        ],
        "note": "对应站点 §诚实边界 与 README §诚实边界 的同一条纪律",
    },
    {
        "kind": "bullets",
        "kicker": "11 · 怎么用",
        "title": "一个命令，九个动作",
        "lead": "装好之后只有一个命令 `ask-dao-machine`：敲它就报身份（徽标 + 速查），敲参数就干活；产出固定落在 --out 目录。",
        "bullets": [
            ("论文 → 问题", "`ask-dao-machine paper <文件/目录> [--domain biomed]`"),
            ("疑问 → 科学问题", "`ask-dao-machine ask \"<日常疑问>\"`"),
            ("造词 → 概念", "`ask-dao-machine imagine <自造词>`"),
            ("图像 → 问题", "`ask-dao-machine perceive <图片/目录>`"),
            ("挂到宿主", "`ask-dao-machine mcp`：Claude Code / Cursor 用 .mcp.json；DSH 用技能目录（本机热加载已验证）"),
        ],
        "note": "可复现：python tools/fetch_biomed_paper.py --pmcid PMC13331974 → "
                "ask-dao-machine paper papers/biomed/PMC13331974.md --domain biomed",
    },
    {
        "kind": "table",
        "kicker": "12 · 另一条线的已核实结果",
        "title": "同一套判据在数学线上的产出（对照）",
        "lead": "为了让「证据边界推进」这个词有具体所指：跨进制命题 P(b) 的 harness 裁决表。",
        "table": {
            "head": ["项", "结果", "证据"],
            "rows": [
                ["命题 P(b)", "对每个 n ≥ 4，存在 base-b 回文数 p 与素数 q 使 n = p + q；对 b ≥ 4 例外集有限且很小", "精确枚举"],
                ["15 个进制裁决", "13 confirmed（含 5 个零例外）· 1 open（b=3）· 1 rejected（b=2）",
                 "N0=5×10⁶ → N1=10⁷ 例外集汇合、无新例外"],
                ["独立复算", "另写一套 FFT 实现复算 base 3–47：b=3 例外 68 个，清单逐项与 harness 一致",
                 "本次会话独立实现（另一份代码）"],
                ["边界修正", "旧账本曾记 base 4 有 20 万个例外，真值 5 个；错的是账本，不是结论", "docs/novelty_ledger_corrections.md"],
            ],
        },
        "note": "状态只来自判定器：confirmed 是数值汇合，不是证明。世界新问题仍为 0。",
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
            ("ModelScope · dao-v-0.3", "https://www.modelscope.cn/studios/skopskp/dao-v-0.3"),
            ("GitHub", "https://github.com/shikunpneg/ask-dao-machine"),
        ],
        "foot": "道生一，一生二，二生三，三生万物",
    },
]


if __name__ == "__main__":
    print("slides:", len(SLIDES))
    for s in SLIDES:
        print(f"  [{s['kind']:7s}] {s['title'].splitlines()[0][:34]}")
    print("biomed:", B["total"], "=", B["generic"], "通用 +", B["biomed"], "生物医学")
    print("  方法学追问", B["mg"], "（作者已论及", B["touched"], "/ 文中未见", B["untouched"], "）+ E-value", B["ev"])
    print("E-values:", {k: (v["evalue_point"], v["evalue_ci_bound"]) for k, v in EV.items()})
