# 02 CONTEXT —— 上下文与现状（Claude Code 接手用）

## 1. 目标（唯一）
造一台**问题制造机**：批量产出"真实问题"，理想是产出前所未有的新问题；当前工程目标是**可审计地筛出新问题**（三重门槛：机器可真判 → OEIS/文献未见 → LLM/人工不排除）。

## 2. 用户口径（已确认的修正）
- 第二步判**真伪**（不是可行性），可行性后置；
- 领域定义借鉴**分部门哲学**；
- 及格线 = 稳定产出真问题；"前所未有"=惊喜指标；
- **LLM 是操作层裁判**，人类只在出版级/N2-N3 裁决；
- 产出：能小范围跑出成果的机器 + 产品化（github 仓库）。

## 3. 理论审计结论（语料派，勿重做）
- 母题论：弱版成立（生成程序），强版（封闭母题库）被哥德尔/科恩/塔斯基否决；
- "所有问题早期是真伪问题"：作为**问题语法形式**成立；真值悬置是常态；判定须分域；
- 思想实验 = 概念裁决（一致性/可能性），不给经验真值；
- 发现（第一猜想）不可程序化；**"反例→新问题"可程序化**（机器甜区）；
- 领域 = 宪章五件套；解释类型是最硬分界；张力（异常/悖论/统一）是大问题之源（科学史 M1–M7）；
- 当务启发式 H1–H10（见 `docs/BIG_PROBLEMS.md`）——**必须证据依赖**才可用。

## 4. 架构（现行）
- 包 `src/ask_dao_machine/`：model(ProblemRecord 出处链) / registry(母题 86) / judges_math / 引擎 math·records·combo·fusion·ling·direction·break·sparse / pipeline(ProblemMaker) / viz / cli / novelty_judge / verifier / judge_blueprints / motif_composer / motif_growth / grammar
- 工具 `tools/`：oeis_check/sweep/sweep2、big_score、**big_score_ev（证据门）**、tension_detector/v1、method3_gen_tension/unified、cross_explore、cross_multidomain、cross_md_v3、verify_cross_md、dedupe_survivors、iterate、make_ledger、humanities_math/sig、build_motif_map、graph_space、station3、p_A4/p_B_deep/p_C_integrate/p_C_round2/p_C_ev_regrade
- 文档 `docs/`：MASTER_PLAN、LONG_PLAN、METHODOLOGY3、PLAN_TENSION_DETECTOR、BIG_PROBLEMS、MOTIF_DEFINITION、DESIGN、EXPLORATION_REPORT、EXECUTION_LOG、EXPERIMENT_RECORD、novelty_ledger、llm_grade_tension、tension_gap_map、tension_formal_yanyi、human_review_sheet

## 5. 现状指标（最近）
| 指标 | 值 |
|---|---|
| 问题总量 | ~100+（8 域文件） |
| 裁判分布 | N0×28 / N1×57 / N2×10 / **N3=0** |
| OEIS 双未见 | S2 广义 Collatz 停时表 ×7（低值表数据） |
| 检索级未见 | 言不尽意×语言熵率（已物化为"意义状态建模"前问题） |
| 张力候选 | 中哲 31（26 对峙）+ 西哲 98 = 129 |
| 张力注入 | 129→387→258 幸存→19 唯一→LLM A2/B17/C0 |
| 多域交叉 | 矩阵 454→130 有判定器；1 个**真三域**样本（信念×迭代×信道，仿真：低容量不学习阈值） |
| **世界新问题** | **0** |

## 6. 诚实结论
系统已被证明：批量制造良构可判问题 + 分域判定 + 三层筛新 + 张力召回 + 多域交叉。
尚未证明：稳定产出世界级新问题。跨过边界需：参照系稀薄的深参数空间 / 规模化主张库与悖论检测 / 专家在环 / 更大算力。

## 7. 未决与不确定
- 三域交叉**名义化缺陷**（第三域未真参与）——待整改；
- 矩阵自动短语导致语句语义偏空（F1 门槛太松）；
- OEIS 已滤掉全部"假 R"；剩余候选价值低；
- 美学域判官=人类/实验，尚无数据接入。
