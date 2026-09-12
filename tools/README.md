# tools/ —— 每个脚本是干什么的

> 本文件自动生成（`python tools/tools_index.py`）。改脚本后请重新生成。

共 141 个脚本。按「**谁在运行它**」分组——只有被运行的才算活代码；只在历史日志里被提到的，不算。

## src　（1 个）

| 脚本 | 作用 |
|---|---|
| `territory_scan.py` | 领地稀疏度实测(LONG_PLAN_V2 Phase 1 的 DoD) |

## src、文档　（2 个）

| 脚本 | 作用 |
|---|---|
| `perception_module.py` | 感知/经验模块(用户愿景的"第一手经验"入口) |
| `run_paths.py` | 统一入口：两条路的输入接口（v0.2） |

## src、文档、tools　（5 个）

| 脚本 | 作用 |
|---|---|
| `novelty_gate.py` | 真实新颖性门(替代"手写字符串 + 无法输出N3的启发式裁判") |
| `oeis_index.py` | OEIS 离线倒排索引(批量反查用) |
| `question_refiner.py` | 日常疑问 -> 可判科学问题（R55） |
| `retrieve_browser.py` | 浏览器检索器(selenium + Edge) for 想象模块方案2 |
| `retrieve_context.py` | 想象模块的"经验文本检索器" |

## src、长跑总控、文档、tools　（1 个）

| 脚本 | 作用 |
|---|---|
| `word_understand.py` | 词的认真理解器（R72） |

## 长跑总控、tools　（4 个）

| 脚本 | 作用 |
|---|---|
| `fusion_territories.py` | Track 4 & 5: 生物/心理稀疏领地 + 领域融合 |
| `imagination_sentence.py` | 想象路造句器（R79） |
| `oeis_batch_gate.py` | 批量 OEIS 门: 全库序列候选 -> 自动分级 |
| `run_resident.py` | 常驻长跑总控: 三链路轮转, 用满核, 无超时 |

## 长跑总控、文档、tools　（6 个）

| 脚本 | 作用 |
|---|---|
| `all_domains_engine.py` | 全领域并行引擎：数学/生物/物理/哲学/化学... 所有领域（R69） |
| `browser_mass_search.py` | 全量双通道维基搜索(词条通道 + 组合词搜索通道) |
| `deep_fusion.py` | 深层结构性融合（R63） |
| `field_fusion.py` | **领域级融合**：造新领域（R40） |
| `parallel_factory.py` | 并行算力工厂：用满全部核去生成和扫描问题（R67） |
| `word_fusion.py` | 穷尽关键词组合：先造词，再解释，再联想（R70） |

## 文档　（17 个）

| 脚本 | 作用 |
|---|---|
| `arxiv_miner.py` | arXiv 前沿摘要挖掘：从最新论文里挖"开放/未知/新问题"（R56） |
| `build_paths_viz.py` | 两条路可视化: 节点连线树 + 概念论证（v0.4） |
| `composition_demo.py` | 方向级组合样例(L3 x L1 / L3 x L2) + 一个数值判定的融合探针 |
| `discovery_pipeline.py` | 问题发现器主入口（R52） |
| `extended_probe.py` | 把两个'未见'候选的验证范围扩到 N=300000, 记录新证据。 |
| `fetch_biomed_paper.py` | 抓一篇真实、开放获取的生物医学全文（Europe PMC）。 |
| `imagination_batch_verify.py` | 想象路批量验证：376 个疑似新概念查真实所指（R78） |
| `install_integrations.py` | 把问道挂到各宿主上（一份源码，多处安装）。 |
| `method3_unified.py` | 统一张力库(中31+西98) -> 注入生成 -> F4幸存 -> human_review |
| `problem_lineage.py` | 问题谱系：把孤立问题还原成**整根树枝**（R38） |
| `reconstruct.py` | 拆后从底往上还原成段落（R85） |
| `reconstruct_sent.py` | 句子化还原: 拆到底 -> 用完整句子从底还原 -> 成有语义的段落（R86） |
| `scihist_to_problems.py` | 科学史开放点 -> 正式问题 + 树融合（R59） |
| `sentence_method.py` | 造句方法（用户教的方法）（R81） |
| `tension_detector.py` | 语料张力探测器 v0 (PLAN_TENSION_DETECTOR) |
| `understand_deep.py` | 理解深化器：把造句展开成段落理解（R80） |
| `word_interpret.py` | 词的诠释器：给每个组合一个有想象力的解释（R71） |

## 文档、tools　（22 个）

| 脚本 | 作用 |
|---|---|
| `ai4s_harness.py` | AI4S harness(最小可跑版)：消化发现器的问题清单 |
| `big_score.py` | 当务评价器 v0 (基于科学史 H1-H10 启发式) |
| `build_site_problems.py` | 把机器实际产出的记录，整理成**分级 + 问题/命题形态**的展示数据。 |
| `corpus_to_problems.py` | Track 1: 普通文本语料 → 日常疑问 → 科学问题 |
| `cross_md_v3.py` | 1)矩阵放大(>=50组合) 2)F3参照系+LLM判 3)优先三域 |
| `depth_batch.py` | 批量深度造句: 10概念建树 + 自动d=自然深度（R84） |
| `depth_sentence.py` | 可调深度造句器（R83） |
| `fetch_wiki.py` | 抓取词库 82 词的维基百科词条正文, 每词一个 JSON 文件 |
| `field_forge.py` | 领域锻造：造**真的新领域**（Track 5 的攻关） |
| `imagination_deep.py` | 想象模块深度展开：从新造词到理论草稿（R73） |
| `llm_judgment.py` | LLM/人工裁判台账(操作层判官, 带文献出处) |
| `make_site.py` | 从 tools/site/home.html 生成最终首页 docs/index.html. |
| `mechanism_probe.py` | J2「机制追问」的**机器化**(LLM 裁判协议的核心必填项) |
| `palbase_scan.py` | 多进制扫描：回文数(b)+素数 覆盖，找"稳定小例外集"（R51） |
| `problem_gate.py` | 问题级门(对**定性**开放问题) |
| `problem_strata.py` | 问题的深度分层 + 层间生成（R37） |
| `reconstruct_compare.py` | 成段加概念比较（R88） |
| `reconstruct_judge.py` | 带推理判断的成段（R87） |
| `scale_hunt.py` | 用**计算优势**挖事实（R41） |
| `sentence_batch.py` | 批量造句(按用户方法): 问→拆→再问→再拆→成段（R82） |
| `tri_verifiers.py` | 真三域验证器(去名义化) |
| `web_experience.py` | 网页经验模块：随机爬取网页 -> 日常疑问 -> 科学问题 |

## tools　（23 个）

| 脚本 | 作用 |
|---|---|
| `big_score_ev.py` | 证据依赖版当务评分(整改版) |
| `candidate_rank.py` | Phase 3 (Axis S): 规模化 + 候选排序 |
| `conjecture_search.py` | 猜想生成器(Phase 3b, 替代手写 spec) |
| `crazy_scale.py` | 疯狂规模化：所有基础领域 × 所有组合 × 向前推进（R44） |
| `cross_md_v4.py` | 多域交叉 v4: 真F1门槛 + 真三域(去名义化) + 质量分层 |
| `deck_figs.py` | 从真实产物生成 PPT 用图（OJO 墨纸风）。 |
| `deck_spec.py` | 成果汇报 PPT 内容规格（v3：图片 + 解释为主）。 |
| `design_ink.py` | 墨纸设计系统（供架构图 / 问题生成树共用） |
| `final_candidates.py` | 把猜想生成器的幸存者过完整领地机器(Phase 3c) |
| `fix_multiname_imports.py` | 补漏：`from . import (a, b, c)` 这种多名字括号形式，rename_modules.py 的正则没覆盖。 |
| `fusion_matrix.py` | 操作子 × 结构 融合矩阵批量扫描（R64） |
| `grade_unseen.py` | 对 OEIS 门产出的未见候选做严格分级 |
| `imagination_verify.py` | 想象路的质量验证器（R76） |
| `iterate.py` | P4 迭代环 v1: combo 的 R/边界项 -> 子代(变异约束 + 扩界) -> 分类存活率 |
| `llm_judge_pass.py` | LLM 裁判协议(补做 R25–R33 一直没真正做的事) |
| `make_ledger.py` | P4.5 novelty_ledger 台账: 汇总所有域问题集的裁判/状态分布 + R + 晋升, |
| `make_pptx.py` | 用 python-pptx 生成可编辑的 .pptx（与 HTML 版同一份 deck_spec）。 |
| `mega_scan.py` | 疯狂扩张：可复合算子链 × 大对象池 × 跨域融合（R39b） |
| `oeis_check.py` | 离线 OEIS 反查: 用序列前缀在 stripped.gz 中找 A 编号 |
| `rename_modules.py` | 把 src/ask_dao_machine/ 的模块按功能重命名，并更新全仓库引用。 |
| `s2_bounded.py` | S2 广义Collatz停时"有界性"严格复算(纠错版) |
| `significance_vs_random.py` | 可机检的显著性判据(置换零模型版) |
| `tree_svg.py` | 节点连线树（SVG）: 展示来龙去脉与生成全过程（R91） |

## 没有运行者　（60 个）

> 这些脚本当前**没有任何东西调用它**。可能是一次性探针、已完成使命的历史脚本，或需要保留的证据链。**先别删**——但要对它们做任何事之前，先确认不是证据链的一环。

| 脚本 | 作用 |
|---|---|
| `alias_renamed_imports.py` | 补漏 2：`from . import new_X` 要写成 `from . import new_X as old_X`。 |
| `arch_diagram.py` | 系统架构图（墨纸风, 与 problem_tree.svg 同一套设计系统） |
| `art_logo.py` | 极简 logo: 书法「道」去纸纹、纯墨色（v0.5） |
| `banner_art.py` | 湖面艺术化 banner（真实湖泊图 + 道字 + 雾化水墨） |
| `build_motif_map.py` | build_motif_map.py v2 — 按 MOTIF_DEFINITION 分层; 新增: 其他域 L3 方向 + 每方向'典型问 |
| `build_tree_viz.py` | 母题树生长 + 树交叉可视化(用户 R22 重申的重要项) |
| `constant_engine.py` | 常驻并行引擎：14 进程长时间后台生成+扫描（R68） |
| `cross_explore.py` | METHODOLOGY3 编排 v1 (本地, 确定性): |
| `cross_multidomain.py` | 多域交叉融合 v2 (2域/3域) |
| `daily_to_tree.py` | 日常问题 -> 问题树生长/融合（R57） |
| `dedupe_survivors.py` | 258幸存去重(按 topic+双极唯一) 供 LLM 分级 |
| `fix_wiki_titles.py` | 修正搜索 API 挑偏的 4 个词条（人工指定正确条目标题）。 |
| `frust6.py` | n=6 全部 6-边图的阻挫签名分类(大规模) |
| `frustration_index.py` | 图的阻挫指数(融合: 伊辛基态简并度 -> 图度量) |
| `genspace_scan.py` | 生成空间策略对照实验(回答"能不能发现新问题") |
| `graph_space.py` | 第2站: 图不变量空间(小n标号图暴搜) |
| `humanities_math.py` | 数学 × 人文学科 交叉(计量文体学): |
| `humanities_sig.py` | 数学x人文 第二步: 置换检验 |
| `imagination_run1.py` | 想象模块完整跑一小轮（R90） |
| `lateral_scan.py` | 侧向矩阵大扫描（R39） |
| `make_deck.py` | 把 deck_spec 渲成两样东西：可编辑的 .pptx 与线上 HTML/PDF。 |
| `make_logo.py` | 生成项目 logo:「道」(行书) on 宣纸 |
| `make_problem_tree.py` | 用**真实数据**画「问题生成树」 |
| `make_site_assets.py` | 站点素材生成器（全部来自真实素材，不用字体冒充书法） |
| `mega_branch_scan.py` | 全力扫描: 算术函数 x k泛化 x 奇偶 x 大N（R61） |
| `mega_filter.py` | 疯狂融合的**诚实过滤**（R39c） |
| `method3_gen_tension.py` | METHODOLOGY3 ①阶段升级: |
| `oeis_sweep.py` | 用离线 OEIS 索引反查 combo 全部 R 项 + 迭代子代, |
| `oeis_sweep2.py` | 宽容匹配: 起始偏移 0..3, 6项前缀窗, 批量反查 12 个严格未命中项 |
| `omni_scan.py` | 全方位扫描器（R62） |
| `open_branch_gen.py` | 人类已知开放问题 -> 相邻问题生成(领域融合分支)（R60） |
| `open_mine.py` | 开放问题挖掘器：从人类知识库提取"自我承认的未知"（R47） |
| `p_A4.py` | P-A.A4 雏形验证: 有限文法熵率(子命题1) + S2 p=3 快速(子命题2建模雏形) |
| `p_A5_yanyi.py` | P-A.A5: "言不尽意 × 熵率" 的可判雏形(把前问题做成判定器) |
| `p_B_deep.py` | P-B 深扫 S2 广义Collatz停时(扩展 Q 到更多, 看是否单调爬升) |
| `p_C_ev_regrade.py` | 整改后重跑: 证据依赖评分 vs 关键词评分 |
| `p_C_integrate.py` | P-C 当务升级回路: |
| `p_C_round2.py` | P-C 二轮: LLM 判 21 条当务≥3, 选 A/A- 写终稿候选 |
| `pcset_entropy.py` | 探索"看起来空"的格子：音级集合 × 熵（R42） |
| `recompute_entry_channel.py` | 强制重算「词条通道」（本地，不开浏览器）。 |
| `refetch_wiki_api.py` | 重抓 82 词条正文（MediaWiki API，纯 HTTP）。 |
| `refresh_bridge_anchors.py` | 重跑 9 个重点组合的 M7 经验锚点（语料补全后），不走浏览器。 |
| `repair_alias_damage.py` | 修复 alias 脚本的越界替换：把 `X as Y.method()` 还原成 `Y.method()`。 |
| `resolve_missing_wiki.py` | 补齐维基里没有同名条目的词：用搜索 API 解析到最相关条目标题，再抓正文。 |
| `scale_1e9.py` | 把"回文数+素数"覆盖推进到 10⁹（K2-10） |
| `scale_grid.py` | 把"计算优势"规模化：对多个领域格批量算到底（R43） |
| `sparse_expand.py` | S2 参数扩张扫荡 + OEIS 过滤 |
| `station3.py` | 第3站: 极小构造纪录 |
| `tension_hist.py` | 科学史语料的张力探测(用户: 别只做哲学) |
| `tension_v1.py` | 张力探测器 v1: 段落窗 + 子类判定 |
| `tools_index.py` | 按「谁真的运行它」重判 tools/，并生成 tools/README.md 索引。 |
| `verify_cross_md.py` | 三域交叉候选的仿真验证 |
| `verify_hero_ab.py` | A/B 渲染: 切出"墨迹层", 客观验证首屏的『道』确实是真实书法。 |
| `verify_page_effects.py` | 收尾验证（轻量）：水面物理判定 + 截图级粒子/涟漪 + 整页背景统一。 |
| `verify_page_shots.py` | 生成截图用副本: 去掉外部字体(离线渲染会挂住), hero 固定高度, 强制显示滚动动画元素。 |
| `verify_particle_footprint.py` | 决定性实验: 粒子到底覆盖了哪些像素? |
| `verify_screenshot.py` | 数值化验证首页渲染结果（不依赖视觉模型）。 |
| `verify_site_http.py` | 在 HTTP 下验证站点（线上同源条件）：水面模式 / 物理 / 整页背景统一 / 粒子存在。 |
| `verify_water_physics.py` | 水面自检 v2：径向剖面度量（波前位置 = 环带平均幅度最大的半径），并检查叠加干涉。 |
| `word_structural.py` | 词组合的结构相容过滤（R70b） |
