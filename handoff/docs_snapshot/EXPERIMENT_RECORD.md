# EXPERIMENT_RECORD —— 实验总记录（从最初理论到多域交叉）

> 读者：本项目所有者。目的：一份可核对的完整实验史（做了什么、得到什么、怎么判的、代码/数据在哪）。
> 仓库：github.com/shikunpneg/ask-dao-machine · 记录截止提交见各节"提交"栏。

---

## 第 0 部分 起点：理论主张（用户）
1. 三能力：推理验证 / 联想 / 大胆猜想；
2. 理论：领域由"母题"组成；问题早期都是真伪问题，像树一样分支；跨域融合碰撞产生新问题；
3. 三步：日常疑问 → 领域结构化（发现真问题）→ 思想实验验证 →（后修正：真伪判定为主，可行性后置）→ 扩展成理论；
4. 目标：能制造科学问题/知识的机器；后来明确：**要产出真实的新问题**。

## 第 1 部分 理论审计（语料派）
- 语料：爱思唯尔科学哲学手册 8 种 14 册、梯利《西方哲学史》、哲学100问、北大《中国哲学史》第2版、库恩《科学革命的结构》、斯特雷文斯《知识机器》、波普尔《科学发现的逻辑》等。
- 方法：EPUB→文本（pandoc/自写提取器）→ 分片派子代理精读 → 取证报告 A/B/C/D/E/F + 汇总。
- 关键裁决：
  * 母题论：弱版成立（结构/机制/对称/功能这类生成程序），强版（封闭母题库）被哥德尔/科恩/塔斯基否决；
  * "所有问题早期都是真伪问题"：作为**问题语法形式**成立，但真值悬置是常态；判定须分域（形式/经验/规范）；
  * 思想实验=概念裁决（一致性/可能性），不给经验真值；
  * 发现（第一猜想）不可程序化，但"反例→新问题"可程序化（机器甜区）；
  * 领域定义=宪章五件套；解释类型是最硬分界。
- 产物：`_theory/definitions_audit.md`、`basic_domains.md`、`plan_v2.md`、`synthesis_理论审查报告.md`、report_A–F。

## 第 2 部分 机器原型（v0.1 → v0.17）
- v0.1：`machine_v1/`（math_machine/aesthetics_machine + viz）——数学自判 + 美学待实验 + 可视化。
- 工程化：`ask-dao-machine` 包（pyproject + CLI），问题制造器封装为 `ProblemMaker`；`ProblemRecord` 带完整出处链（母题/模板/参数/判定证据/诚实标签/树边）。
- 引擎清单（现行）：math(25题) records(28) combo(23) fusion(4) ling(3) direction(4) break(sparse+纪录复核)；美学 8。
- 可视化：`out/demo/viz/index.html`（母题总览 + 问题树 + 徽章 + 出处链展开）。

## 第 3 部分 新颖性工程（核心教训都在这）
1. **参照系**：下载 OEIS stripped（39.9 万序列）建离线索引（`tools/oeis_check.py`），做严格/宽容/去零三种匹配。
   * 结果：combo 全部"假 R"被 OEIS 命中（如 禁0101→A118870、maxrun4→A275544、禁010→A014167）。
2. **裁判**：`novelty_judge`（N0 已知/N1 大概率已知/N2 疑似未见/N3 强候选）全量覆盖；当前分布 N0×28 / N1×57 / N2×10 / **N3=0**。
3. **迭代环**：`tools/iterate.py`（R 母题→变异/扩界子代 30，11 存活）。
4. **诚实纠错（≥5 次，每次都让候选缩水）**：
   * P4 判定 bug（三角+孤立点误判）→ cograph 修正后命中 A006351；
   * 置换检验分母 bug → p 从 1.0 纠为 **0.0002**（数学×人文句长差异显著）；
   * X3"熵率上界"误标悬置 → 实为平凡上界 log|Σ|；
   * "偶 q 停时恒 14"结构陷阱 → 剔除；
   * 阈值贴边界 → 标 needs_extend 不谎报 confirmed。
5. **当务分自灌水事件（最重要教训）**：P-C 用关键词版 big_score 得到 21 个 H=6.5 候选，但分数来自我在模板里嵌入的触发词（公设/测量/悖论/统一/预言）。**整改**：`big_score_ev`（证据依赖门：每分项须挂出处/路由/预言/测量/异常≥3/年限/实验设计）→ **21 全部归 0**，而带真实证据的史例（第五公设）得 **7.0**。

## 第 4 部分 生成空间五站（旧线攻坚）
| 站 | 空间 | 结果 |
|---|---|---|
| 1 | 广义 Collatz 停时表 (p×奇q) | **OEIS 双未见 ×7**（唯一过 OEIS 门者；低值表数据）；深扫 p∈{3,5,7} 停时随 Q 单调↑（表观有界未证） |
| 2 | 图不变量（无三角/二部/cograph） | 全命中(A213434/A047864/A006351)或结构平凡(Ramsey) |
| 3 | 极小构造（双 de Bruijn / 两平方表示） | 命中 A004766/A018782 |
| 4 | 边界评估 | 结论：教科书式漂亮问题全被表化；参照系稠密空间已饱和 |
| A | 数学×人文（计量文体学） | 学术 vs 通俗句长 46.6 vs 35.0，**置换 p=0.0002 显著**；Zipf/熵表 |
| B | 纪录复核 | Collatz 停时纪录 837799/524 ✓；质数最大间隙 114@492113、154@4652353 ✓ |

## 第 5 部分 张力线（新方向）
- 探测器 v0/v1：中哲 31（26 对峙/5 并存）+ 西哲 98（理性vs经验…）= 129 张力候选（命中即交锋引文）。
- METHODOLOGY3 张力注入：129 → 387 候选 → F4 幸存 258 → 去重 **19 唯一**（对照朴素笛卡尔 0/24）。
- LLM 预判（人类之前）：A/A- 2（物自体可知性、自由意志-必然性，均属"活但著名"）/ B 17 / C 0 → **可供人类的新问题 = 0**。
- 张力×当代形式化缺口映射（10 条）：8 条已有当代处理；**1 条检索级未见**：言不尽意 × 语言熵率（命中的全是诠释学线）→ 物化为"意义状态如何建模才使可嵌入性可判"（新前问题）。

## 第 6 部分 多域交叉（本轮）
- 引擎 `tools/cross_multidomain.py`：域母题(L3方向)×载体×第三域判据，2 域/3 域；F1/F2/证据门。
- 5 模板 → 4 过门；两个 3 域候选 H=2.0。
- 三域仿真（心理信念修正×数学迭代×信息信道，`verify_cross_md.py`）：模型正确⇒恒收敛；**低估噪声在低容量段(C≲0.03bit)塌成完全不学习**，偏差随容量单调↓ → 真(仿真)、N1 已知-标准。

## 第 7 部分 总结论（诚实）
- **世界新问题 = 0**（三重门槛：机器可真判 + OEIS/文献未见 + LLM/人工不排除，无一项通过）；
- 系统已证明能力：批量制造**良构可判**问题、自动**分域判定**、**三层筛新**（参照系/裁判/证据门）、**张力召回**与**多域交叉**；
- 尚未证明能力：稳定产出世界级新问题；
- 跨过边界所需的四条件：参照系稀薄的深参数空间 / 规模化主张库与悖论检测 / 专家在环 / 更大算力预算。

## 附：代码与数据索引
- 包：`src/ask_dao_machine/`（model/registry/judges/各引擎/pipeline/viz/cli/novelty_judge/grammar/verifier/judge_blueprints/motif_composer/motif_growth）
- 工具：`tools/`（oeis_check/oeis_sweep/oeis_sweep2/big_score/big_score_ev/tension_detector/tension_v1/method3_*/cross_explore/cross_multidomain/verify_cross_md/dedupe_survivors/iterate/make_ledger/humanities_math/humanities_sig/build_motif_map/graph_space/station3/sparse_*/break_engine 等）
- 数据：`out/demo/*.json`（problems_*、tensions_*、gap_*、s2_deep、cross_md_belief 等）
- 文档：`docs/`（MASTER_PLAN、LONG_PLAN、METHODOLOGY3、PLAN_TENSION_DETECTOR、BIG_PROBLEMS、MOTIF_DEFINITION、DESIGN、EXPLORATION_REPORT、EXECUTION_LOG、novelty_ledger、llm_grade_tension、tension_gap_map、tension_formal_yanyi、human_review_sheet + 本文件）
