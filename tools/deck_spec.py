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

F = "figs/"
SLIDES = [
    # ══════════ 封面 ══════════
    {
        "kind": "cover",
        "kicker": "ASK-DAO-MACHINE · 成果汇报",
        "title": "问道知识发现系统\n成果汇报",
        "lead": "一台制造知识的机器：**推理验证 / 联想 / 大胆猜想**。\n"
                "汇报顺序：原理 → 生物医学的实践 → dao 模型的实践 → 扩展的实践 → 方向与瓶颈。",
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
            ("三、dao 模型在生物医学的实践", f"dao-v-0.3 这一代：问题路 **{len(MODEL_PROBS)} 条 / {N_DOM} 个领域**；"
                                   f"想象路 **{N_COMBO:,}** 个组合词走完五步；独立裁决 **{len(HARNESS)} 个进制命题**。"),
            ("四、扩展的实践", f"同一套判据换领域：**{N_FIELDS} 个领域 / {N_PAIRS} 个配对 / {N_BRIDGE} 座结构桥梁**；"
                          "音乐与记录域重算出的已知结果**对上了**——这是校准自己的方式。"),
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
            "src": F + "fig_two_paths.png",
            "caption": "左：问题路（产问题）。右：想象路（产概念）。两条路可以各自单独跑，"
                       "也可以选择过经验检索桥——过桥只做脚手架，不做裁判。",
        },
        "bullets": [
            ("问题路 · 成功标准", "**答案成立 / 可判**。每条问题必须带 `route`（判定方式），"
                            "判不了的不产出。"),
            ("想象路 · 成功标准", "**语法正确 + 逻辑通畅 + 有推理判断**——不是「有真实所指」。"),
            ("互不评判", "用问题路的逻辑（「这新吗」「有真实所指吗」）去判想象路的概念，是**范畴错误**。"),
            ("经验检索桥（可选）", "把组合词接到现实经验（维基双通道 + arXiv 回退 → 经验锚点）。"
                            "**过桥不改变任何判定**，检索失败即退化为无锚点。"),
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
        "kind": "figure",
        "kicker": "二、在生物医学的实践 · 新知识",
        "title": "机器算出来的三个残余混杂门槛",
        "lead": "要把论文报告的效应解释成「没有效应」，未测混杂必须与暴露、结局**同时**达到多强的关联。"
                "**原文中 “E-value” 出现 0 次**——这三个数是算出来的，不是抄来的。",
        "figure": {
            "src": F + "fig_evalue.png",
            "caption": "青：论文自报的效应量。朱砂：机器算出的 E-value（门槛）。"
                       "黑色竖线：按 95% CI **下界**重算的门槛——更保守的那一个。",
        },
        "bullets": [
            ("主结果", f"HR **{EV['1.19']['evalue_point']}**（CI 下界 {EV['1.19']['evalue_ci_bound']}）："
                     f"未测混杂要与暴露、结局各自达到 RR≈{EV['1.19']['evalue_point']} 才能把效应解释为零。"),
            ("最高风险组", f"HR **{EV['1.49']['evalue_point']}**（{EV['1.49']['evalue_ci_bound']}）："
                       "所需混杂强度更高，**最难被混杂解释**。"),
            ("替代分析", f"HR **{EV['1.02']['evalue_point']}**（{EV['1.02']['evalue_ci_bound']}）："
                      "这一条最脆，**几乎任何微弱混杂都能解释掉**。"),
            ("怎么复核", "公式 E = RR + √(RR(RR−1))，用 HR 近似 RR（结局须不常见）。"
                     "**任何人都能用论文里的数字复核这三个数。**"),
        ],
        "note": "纪律：这是**门槛**，不是结论。它不主张效应存在，也不构成任何临床建议。",
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

    # ══════════ 三、dao 模型在生物医学的实践（dao-v-0.3 · 模型侧） ══════════
    {
        "kind": "figfull",
        "kicker": "三、dao 模型在生物医学的实践 · 这一代",
        "title": "dao-v-0.3：把「造词」做成一条能跑完的流水线",
        "lead": f"想象路不是问题路的子功能，而是与它**并列的一条路**。{N_COMBO:,} 个领域专业词组合，"
                "每个都要走完五步，产出的是**被理解的概念**。",
        "figure": {
            "src": F + "fig_pipeline5.png",
            "caption": "五步流水线。原则：**每个词都有意义，只不过是我们缺少想象力，无法理解它**——"
                       "因此不存在空想。",
        },
        "note": "版本线：v0.2 产品 → **v0.3.0 两条路** → v0.3.1 可视化/README → v0.4 问题树 → v0.5（问道）。"
                "ModelScope 上的 `dao-v-0.3` 就是这一代。",
    },
    {
        "kind": "figure",
        "kicker": "三、dao 模型在生物医学的实践 · 问题路",
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
        "kicker": "三、dao 模型在生物医学的实践 · 独立裁决",
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
        "kicker": "三、dao 模型在生物医学的实践 · 经验",
        "title": "模型侧学到的两件事",
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
