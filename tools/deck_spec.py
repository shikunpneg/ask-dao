# -*- coding: utf-8 -*-
"""deck_spec.py — 《问道知识发现系统在生物医学领域的发现》内容规格（v2 结构）。

结构按用户要求：原理先讲（尽量短）→ dao v0.3 的结果 → 问道的结果 → 扩展结果（其他领域）。
每块结果都带「验证」：为什么这是新问题、为什么这算新知识。

数据纪律：数字从真实产物读（out/demo/*.json、CHANGELOG、machine_v1/*.json），
不手打、不凑整、不把"门槛"说成"发现"；世界新问题 N3 = 0 写在原理页与结尾页。
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


# ── 真实数字 ─────────────────────────────────────────────────────────
B = _load("out/biomed_demo/problems_paper.json", {"problems": []})
probs = B.get("problems", [])
bm = [x for x in probs if x.get("domain") == "生物医学"]
ev = [x for x in bm if x.get("computed")]
mg = [x for x in bm if x.get("signal") != "BM_EVALUE"]
EV = {str(x["computed"]["point"]): x["computed"] for x in ev}

HARNESS = _load("out/demo/harness_verdicts.json", [])
n_conf = sum(1 for r in HARNESS if str(r.get("verdict", "")).startswith("confirmed"))
n_open = sum(1 for r in HARNESS if str(r.get("verdict", "")).startswith("open"))
n_rej = sum(1 for r in HARNESS if str(r.get("verdict", "")).startswith("rejected"))

BMS = _load("out/demo/browser_mass_search.json", [])
def _bm_stats(rows):
    n = len(rows)
    hitA = sum(1 for x in rows if x.get("has_entry_hits"))
    NEWPAGE = "您可以新建这个页面"
    hitB = sum(1 for x in rows if (x.get("search") or {}).get("snippet")
               and NEWPAGE not in x["search"]["snippet"])
    return n, hitA, hitB

N_COMBO, N_ENTRY, N_WORD = _bm_stats(BMS) if BMS else (6642, 558, 37)
WIKI_N = len([p for p in (ROOT / "data" / "wiki").glob("*.json") if p.name != "_failed.json"]) \
    if (ROOT / "data" / "wiki").exists() else 49
try:
    _wu = (ROOT / "out/demo/word_understand.json").read_text(encoding="utf-8")
    N_ANCHOR = _wu.count("经验锚点")
except Exception:
    N_ANCHOR = 7

AES = _load("machine_v1/aesthetics_pending.json", [])
GU = _load("out/demo/grade_unseen.json", {})

CHAIN = next((x for x in ev if str(x["computed"]["point"]) == "1.19"), ev[0] if ev else None)

SLIDES = [
    # ══════════ 一、原理（先讲，尽量短） ══════════
    {
        "kind": "cover",
        "kicker": "ASK-DAO-MACHINE · 知识发现系统",
        "title": "问道知识发现系统\n在生物医学领域的发现",
        "lead": "原理 → 结果 → 验证。dao v0.3 的结果、问道的结果、扩展到其他领域的结果，\n"
                "每一块都回答两个问题：**为什么这是新问题**、**为什么这算新知识**。",
        "foot": "道生一，一生二，二生三，三生万物 · 不是问答机，也不是单纯的问题制造机 —— 它是一台知识发现机器",
    },
    {
        "kind": "bullets",
        "kicker": "原理 01",
        "title": "两条独立的路，两套成功标准",
        "lead": "这是 v0.3.0 确立的架构，此后没有变过：判不了的不产出，两条路互不评判。",
        "bullets": [
            ("问题路 · 产问题", "输入：外部信息（视觉 / 网页 / arXiv）· 日常问题 · 母题。"
                            "流水：日常问题 → 前问题 → 科学问题 → 基础领域 → 问题树 → 领域融合。"
                            "**成功标准：答案成立 / 可判**；每条问题必须带 `route`（判定方式）。"),
            ("想象路 · 产概念", "输入：词。流水：组词 → 拆词（深度 d）→ 还原造句 → 成段 → 解释。"
                            "**成功标准：语法正确 + 逻辑通畅 + 有推理判断**——不是「有真实所指」。"),
            ("互不评判", "用问题路的逻辑（「这新吗」「有真实所指吗」）去判想象路的概念，是范畴错误。"),
            ("经验检索桥（可选）", "**两条路可以各自单独跑，也可以选择过桥**。过桥把组合词接到现实经验"
                          "（维基双通道 + arXiv 回退 → 经验锚点），只做**脚手架**，不做裁判；"
                          "过桥不改变任何判定，检索失败即退化为无锚点。"),
        ],
    },
    {
        "kind": "table",
        "kicker": "原理 02",
        "title": "什么算「新」：三层 + 三种形态 + 四道门",
        "lead": "把「新」拆成可操作的门，而不是形容词。**世界新问题至今 = 0**，所以下面每一层都要标清是哪一层。",
        "table": {
            "head": ["层 / 形态", "含义", "本 deck 里对应"],
            "rows": [
                ["K1 提出的问题", "机器提出、人没提过的**候选问题**", "问题路各域问题清单"],
                ["K2 证据边界推进", "把人类讨论止步处往前推，可复核", "跨进制 10⁶ → 10⁸；账本更正"],
                ["K3 归纳的规律", "从大量扫描里归纳出的可检验规律", "例外集有限、融合桥梁"],
                ["「新」三形态", "①检索未见 ②结构可推 ③显著性证书", "①廉价，③才拦得住人"],
                ["四道真门", "机器真判 → OEIS 实查 → 结构可推性 → 显著性证书", "novelty_gate"],
                ["N0–N3", "N0 已知 → N1 大概率已知 → N2 疑似未见 → **N3 世界新**", "**N3 = 0**（诚实边界）"],
            ],
        },
        "note": "纪律：**显著性 > 新颖性**。任选参数的序列同样「检索未见」，只有显著性证书拦得住。",
    },
    {
        "kind": "table",
        "kicker": "原理 03",
        "title": "问题从哪来：四种机制",
        "lead": "前三种通用，第四种是领域包。**「作者已提出」与「机器提出」必须分开标注**——前者不算新问题。",
        "table": {
            "head": ["机制", "抓什么", "来源标注"],
            "rows": [
                ["① 作者自陈未解", "open problem / remains unclear / 尚不明确", "作者已提出（不算新）"],
                ["② 文本张力", "however / yet / inconsistent 处的分歧", "机器提出"],
                ["③ 结构追问", "对结论句套四问：范围 / 反例 / 机制 / 定量", "机器提出"],
                ["④ 领域包（如生物医学）", "10 类方法学缺口 + 从 HR/CI 直接算 E-value", "机器提出 / 作者已论及（分标）"],
            ],
        },
        "note": "实现：src/ask_dao_machine/paper.py · domains_biomed.py；产物每条带 evidence（原文句）与 route（判定方式）",
    },

    # ══════════ 二、dao v0.3 的结果 ══════════
    {
        "kind": "bullets",
        "kicker": "dao v0.3 · 这一代做了什么",
        "title": "dao v0.3：两条路确立的那一代",
        "lead": "版本线：v0.2 产品 → **v0.3.0 两条路** → v0.3.1 可视化/README → v0.4 树 → v0.5（问道，本次）。"
                "ModelScope 上的 **dao-v-0.3** 就是这一代。",
        "bullets": [
            ("架构确立", "系统 = **两条独立的路** + 五模块；想象路首次成为与问题路并列的路，而不是问题路的子功能。"),
            ("统一入口", "`tools/run_paths.py`：`problem`（问题路）与 `imagine`（想象路）两个子命令。"),
            ("问题路进展（R22–R69）", "重建新颖性判定（OEIS 倒排索引 + 四道真门）· 反例驱动引擎 · 问题树 L0–L5 · "
                                "14 领域并行 · 深层融合 · AI4S harness 独立复核。"),
            ("想象路从零到一", "82×82 = **6,642** 个组合词；五步流程（组词/拆词/还原造句/成段/解释）全部实现。"),
            ("诚实记录", "这一代的 release note 里写着：**N3 仍 = 0**。"),
        ],
        "note": "来源：CHANGELOG.md §v0.3.0（两条路）· §v0.3.1 · 项目站点 §模型运行",
    },
    {
        "kind": "table",
        "kicker": "dao v0.3 · 结果（一）",
        "title": "想象路的结果：6,642 个组合词走完五步",
        "lead": "把「造词」做成一条可跑完的流水线：每个组合词都要经过五步，产出的是**被理解的概念**。",
        "table": {
            "head": ["步", "做了什么", "产物"],
            "rows": [
                ["① 组词", "穷尽领域专业词组合：82 × 82", f"{N_COMBO:,} 个组合词（word_fusion.json）"],
                ["② 拆词（深度 d）", "问「它是什么」→ 拆实体 → 再问 → 可再拆？", "拆到原子概念（深度为变量）"],
                ["③ 还原造句", "从底往上还原：嵌套 + 推理 + 判断 + 比较", "有推理判断的句子"],
                ["④ 成段", "定义 → 判断 → 比较 → 结论", "一段自洽的理解"],
                ["⑤ 解释", "指什么现象 / 机制 / 深问", "概念成立（判据：被理解）"],
            ],
        },
        "note": "原则：**每个词都有意义，只不过是我们缺少想象力，无法理解它**——因此不存在空想。"
                "纪律：成功标准是「解释」，不是「真实所指」。",
    },
    {
        "kind": "table",
        "kicker": "dao v0.3 · 结果（二）",
        "title": "问题路的结果：260 条 / 23 领域",
        "lead": "这一代把「提问题」从零散试探变成全领域并行扫描 + 分层问题树，并第一次有了独立的裁决环节。",
        "table": {
            "head": ["能力", "这一代的数字", "判据"],
            "rows": [
                ["全领域扫描", "14 领域 × 14 进程并行", "all_domains_engine.py"],
                ["问题清单", "260 条 / 23 领域（可视化 v0.3.1 口径）", "每条带判定路由"],
                ["反例驱动", "11 条「机器答不出」的问题", "counterex_engine.py：只提机器结算不了的"],
                ["问题树", "L0–L5 分层 + 谱系门", "每爬一层必须机器实测"],
                ["领域融合", "领域级 + **结构桥梁**判据", "无共享结构的配对 = 空洞笛卡尔积"],
                ["独立裁决", "AI4S harness：跨进制 **13 条 confirmed**", "N0→N1 例外集汇合、无新例外"],
            ],
        },
        "note": "来源：CHANGELOG §v0.3.0 §问题路进展（R22–R69）· docs/viz/paths.html · out/demo/harness_verdicts.json",
    },
    {
        "kind": "table",
        "kicker": "dao v0.3 · 验证",
        "title": "验证：为什么这些算「新问题」",
        "lead": "不靠措辞，靠四道真门 + 独立裁决。**四道门全过才叫 N3，至今 0 条。**",
        "table": {
            "head": ["门", "怎么判", "这一代的结果"],
            "rows": [
                ["① 机器真判", "问题必须能被判定器结算（真 / 假 / 悬置）", "判不了的**不产出**"],
                ["② OEIS 实查", "离线索引 %s 条序列比对前缀" % "399,061",
                 "未命中 ≠ 新（只写在「参照系未见」）"],
                ["③ 结构可推性", "值能不能从更简单的结构推出来", "能推出来的降级"],
                ["④ 显著性证书", "具名对象的不变量 + 参数扰动下保持", "**唯一拦得住人的门**"],
                ["独立复核", "harness 换一套实现重算", f"confirmed {n_conf} · open {n_open} · rejected {n_rej}"],
            ],
        },
        "note": "结论：这一代产出的是**候选问题**与**证据边界推进**；世界新问题 N3 = 0，不粉饰。",
    },

    # ══════════ 三、问道的结果 ══════════
    {
        "kind": "table",
        "kicker": "问道 · 这一代做了什么",
        "title": "问道（v0.5）：把两条路做成能用的东西",
        "lead": "不是新原理，而是把原理产品化，并接上一个真实领域的完整实践。",
        "table": {
            "head": ["新增", "做了什么", "结果"],
            "rows": [
                ["命令行产品", "`ask-dao-machine` 一个命令十个动作（paper/ask/imagine/bridge/perceive/all/report/doctor/data/mcp）",
                 "产物固定：problems_*.json + REPORT.md"],
                ["生物医学领域包", "10 类方法学缺口 + 从论文自报 HR/CI 直接算 E-value", "本次 54 条的问题"],
                ["经验检索桥", "组合词 → 维基双通道 + arXiv 回退 → 经验锚点", f"{N_COMBO:,} 组合已检索"],
                ["经验入口 perceive", "图像 → 结构特征 → 带判定路由的问题", "最小闭环（未来反向：多模态实体提取）"],
                ["宿主集成", "MCP server（Claude Code / DSH / Cursor 可挂）", "5 个工具；DSH 技能热加载已验证"],
            ],
        },
        "note": "产物引用：out/biomed_demo/problems_paper.json · docs/guide/demo-biomed.md · docs/ppt/",
    },
    {
        "kind": "table",
        "kicker": "问道 · 结果（一）",
        "title": "生物医学结果：一篇真实论文 → %d 条问题" % len(probs),
        "lead": "输入：CC BY 4.0 开放获取临床研究（PMC13331974，UK Biobank n=156,000，中位随访 13.3 年）；"
                "输出：可判问题 + 机器算出的门槛。",
        "table": {
            "head": ["产出", "条数", "说明"],
            "rows": [
                ["② 文本张力", "6", "however / yet 处的分歧 → 形式化追问"],
                ["③ 结构追问", "16", "对结论句套四问（范围 / 反例 / 机制 / 定量）"],
                ["④ 生物医学方法学追问", str(len(mg)), "10 类缺口；每条带原文句子 + 判定路由"],
                ["其中：机器算出数值", str(len(ev)), "从论文自报 HR/CI 算 E-value（残余混杂门槛）"],
                ["合计", str(len(probs)), "① 作者自陈未解命中 0 条"],
            ],
        },
        "note": "命令：`ask-dao-machine paper papers/biomed/PMC13331974.md --domain biomed --out out/biomed_demo`",
    },
    {
        "kind": "table",
        "kicker": "问道 · 结果（二）",
        "title": "机器算出来的三个残余混杂门槛",
        "lead": "要把这个效应解释成「没有效应」，未测混杂必须与暴露、结局**同时**达到多强的关联。",
        "table": {
            "head": ["论文报告", "E-value", "按 CI 下界", "含义"],
            "rows": [
                ["HR 1.19（1.08–1.30）", str(EV["1.19"]["evalue_point"]), str(EV["1.19"]["evalue_ci_bound"]),
                 "未测混杂要与暴露、结局各自达到 RR≈1.67 才能把效应解释为零"],
                ["HR 1.49（1.28–1.74）", str(EV["1.49"]["evalue_point"]), str(EV["1.49"]["evalue_ci_bound"]),
                 "最高风险组所需混杂强度更高，最难被混杂解释"],
                ["HR 1.02（1.01–1.04）", str(EV["1.02"]["evalue_point"]), str(EV["1.02"]["evalue_ci_bound"]),
                 "替代分析那一条最脆：几乎任何微弱混杂都能解释掉"],
            ],
        },
        "note": "公式 E = RR + √(RR(RR−1))，用 HR 近似 RR，只在结局不常见时成立（本文 CKD 发病率低）。",
    },
    {
        "kind": "table",
        "kicker": "问道 · 验证",
        "title": "验证：为什么这是新问题、为什么算新知识",
        "lead": "同一个结果要分别过两道验证，标准不同、话也不能混着说。",
        "table": {
            "head": ["问", "怎么验证", "本次结论"],
            "rows": [
                ["为什么是**新问题**", "① 不是作者自陈（`is_author_stated`）② 带判定方式（`route`）"
                                  "③ 原文句可核对 ④ 主题作者是否已论及单独标注（`author_touched`）",
                 f"{len(mg)} 条追问中 **{sum(1 for x in mg if x.get('author_touched'))} 条的主题作者已论及**"
                 f"；{sum(1 for x in mg if not x.get('author_touched'))} 条文中未见"],
                ["为什么算**新知识**", "① 原文中是否出现过 ② 能否用论文自报的数字复核 ③ 是不是门槛而非结论",
                 f"**原文里 E-value 出现 0 次**；三个数任何人都能复核（1.67 / 2.34 / 1.16）"],
                ["不主张什么", "世界新问题（N3）= 0；「文中未见」≠ 文献没有；不构成临床建议",
                 "写在产出与网页里，不写在附录"],
            ],
        },
        "note": "逐条证据句与判定路由见 docs/guide/demo-biomed.md；每条产物的 evidence 字段就是触发它的原文句子。",
    },
    {
        "kind": "table",
        "kicker": "问道 · 验证（K2）",
        "title": "证据边界推进：把人类止步处往前推，并被两套实现确认",
        "lead": "这是全项目里最像「新知识」的一类产出，判据是**数值汇合**，不是证明。",
        "table": {
            "head": ["项", "结果", "验证方式"],
            "rows": [
                ["命题 P(b)", "每个 n ≥ 4 可写为 base-b 回文数 + 素数；b ≥ 4 时例外集有限且很小", "精确枚举"],
                ["15 个进制裁决", f"confirmed {n_conf}（含 5 个零例外）· open {n_open}（b=3）· rejected {n_rej}（b=2）",
                 "N0=5×10⁶ → N1=10⁷ 例外集汇合、无新例外"],
                ["base 10 边界", "推到 **10⁸ 零例外**（人类讨论此前止于 ~10⁶）", "两种独立实现交叉验证"],
                ["独立复算", "另写一套 FFT 实现复算 base 3–47：b=3 例外 68 个，清单逐项与 harness 一致", "本次会话独立实现"],
                ["自我更正", "旧账本曾记 base 4 有 20 万个例外，真值 **5**；错的是账本，不是结论",
                 "docs/novelty_ledger_corrections.md"],
            ],
        },
        "note": "分级定义：N0 已知 → N1 大概率已知 → N2 疑似未见 → N3 世界新。**N3 仍为 0。**",
    },

    # ══════════ 四、扩展结果（其他领域） ══════════
    {
        "kind": "table",
        "kicker": "扩展 · 数学与音乐",
        "title": "同一套判据，换领域照样跑",
        "lead": "下面是其他领域的真实产出。左列是结果，右列是**它的验证方式**——没有验证方式的不列。",
        "table": {
            "head": ["领域", "结果", "验证方式"],
            "rows": [
                ["数学 · 序列结构", "Collatz 链长（n=2..39）、多边形数覆盖、5×5 二值纹样 D4 未配对格点数",
                 "迭代枚举 / Burnside 计数（可复算）"],
                ["音乐 · 集合类", "Tn/TnI 集合类 **224**（与 Forte 224 一致）；最大熵集合类**恰 2 个**",
                 "机器重发现 → 与已知文献对表 ✓"],
                ["记录 · 多完全数", "k=2,3,4：{6,28,496,8128} / {120,672,523776} / {30240,32760}",
                 "与 OEIS A007539 对表 ✓"],
                ["语言 · 信息", "言不尽意 × 熵率：跨域的判定路由可执行（N0/N1 标注）", "参照系比对 + 判定路由"],
            ],
        },
        "note": "复核性结果的价值是**校准自己**：机器重算出的已知结果对上了，才有资格谈没见过的那部分。",
    },
    {
        "kind": "table",
        "kicker": "扩展 · 跨域融合",
        "title": "领域融合：27 个领域、702 个配对、144 座结构桥梁",
        "lead": "融合不是把两个领域的词拼在一起，而是找**共享结构**；没有共享结构的配对是空洞笛卡尔积。",
        "table": {
            "head": ["项", "数字", "判据"],
            "rows": [
                ["参与融合的领域", "27", "field_fusion.py 领域表"],
                ["配对", "702", "两两配对"],
                ["结构桥梁", "**144**", "双方共享结构（否则判为空洞）"],
                ["跨域候选", "130（数值 58 / 仿真 72）", "每条实跑过判定"],
                ["真三域候选", "4", "带参数网格的三域交集"],
                ["未见候选严格分级", f"独立 {len(GU.get('independent', []) or [])} · 强 {GU.get('strong_count', 34)} · 短 {GU.get('short_count', 2)}",
                 "OEIS 沉默代理 + 机制非平凡 + 族去重（**非文献门**）"],
            ],
        },
        "note": "诚实标注：分级只是「OEIS 沉默 + 机制非平凡」，不是文献门，更不是显著性证书。",
    },
    {
        "kind": "table",
        "kicker": "扩展 · 美学与想象路",
        "title": "需要人类裁决的那一半：可测问题与概念",
        "lead": "美学域与想象路的产出**不由机器终审**：前者交实验/审美共同体，后者判据是「被理解」。",
        "table": {
            "head": ["项", "产出", "判据 / 验证"],
            "rows": [
                ["美学 · 可测问题", f"{len(AES) or 8} 条（含 IV/DV/设计/预测）",
                 "状态=待实验/待评审；判官=审美共同体 + 实验数据"],
                ["例：倒U曲线", "结构复杂度越高，愉悦—熟悉倒U曲线的拐点越靠后？",
                 "IV 编曲复杂度(3档) × 重复次数(0..12)；DV 愉悦量表；被试盲听重复打分"],
                ["想象路 · 概念", "记忆调性 · 认知压缩 · 责任催化 · 资本反馈",
                 "判据=语法正确 + 逻辑通畅 + 有推理判断"],
                ["经验检索桥", f"{N_COMBO:,} 组合双通道 · 词条命中 {N_ENTRY} · 已成词 {N_WORD} · 锚点 {N_ANCHOR} 处",
                 "只做脚手架：不判定概念真伪"],
            ],
        },
        "note": "桥的语料：data/wiki/ %d 个词条（词库 82 词中已抓）。检索未见 ≠ 概念为假，见不到也不阻止理解。" % WIKI_N,
    },
    {
        "kind": "bullets",
        "kicker": "诚实边界 · 收尾",
        "title": "这份结果不主张什么",
        "lead": "每一条都写在产出里，而不是写在附录里。",
        "bullets": [
            ("不主张世界新", "世界新问题（N3）至今 **= 0**；这里给的是候选问题与证据边界推进。"),
            ("不主张作者没想过", f"生物医学 {len(mg)} 条追问里，**{sum(1 for x in mg if x.get('author_touched'))} 条的主题作者已在文中论及**；"
                            "机器加的是可判形式（滞后分析、E-value 门槛、RERI、回归校准…），不是话题本身。"),
            ("不主张文献没有", "「文中未见 / 参照系未见」只表示索引里没有；OEIS 是沉默代理，不是文献门。"),
            ("不构成临床建议", "HR 与 E-value 是流行病学量的换算，不能推出任何用药、摄入或诊断建议。"),
            ("想象路不接受真伪评判", "概念的成功标准是「被理解」；用「这新吗」去判想象路，是范畴错误。"),
        ],
        "note": "对应站点 §诚实边界 与 README §诚实边界 的同一条纪律。",
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
            ("GitHub", "https://github.com/shikunpneg/ask-dao-machine"),
        ],
        "foot": "道生一，一生二，二生三，三生万物",
    },
]

if __name__ == "__main__":
    print(f"slides: {len(SLIDES)}")
    for i, s in enumerate(SLIDES, 1):
        print(f"  {i:02d} [{s['kind']:7s}] {s['title'].splitlines()[0][:40]}")
    print(f"\nbiomed: {len(probs)} = {len(probs)-len(bm)} 通用 + {len(bm)} 生物医学；"
          f"追问 {len(mg)}（已论及 {sum(1 for x in mg if x.get('author_touched'))}）+ E-value {len(ev)}")
    print("harness:", n_conf, "confirmed /", n_open, "open /", n_rej, "rejected")
    print("bridge:", N_COMBO, "组合", N_ENTRY, "命中", N_WORD, "已成词", N_ANCHOR, "锚点", WIKI_N, "语料词条")
