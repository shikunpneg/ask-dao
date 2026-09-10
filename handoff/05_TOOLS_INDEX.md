# 05 TOOLS INDEX —— 脚本/引擎索引（用途一览）

## 引擎（src/ask_dao_machine/）
| 模块 | 用途 | 产出 |
|---|---|---|
| math_engine | 数论母题组合+判定(25题) | problems_math.json |
| records_engine | 双类两数和覆盖扫描(28) | problems_records.json |
| combo_engine | 受限串/游程/游走计数(23)+本地种子表 | problems_combo.json |
| fusion_engine | 别域度量×数学对象(4) | problems_fusion.json |
| lang_info_engine | 语言×信息: 文法熵率(3) | problems_ling.json |
| direction_engine | 方向模板×载体(4) | problems_direction.json |
| break_engine | 纪录复核(Collatz停时/质数间隙锚) | (run 内) |
| sparse_engine | 参数化映射族(二次迭代循环/广义Collatz停时) | (run 内) |
| aesthetics_engine | 美学可测问题(8, 待实验) | problems_aesthetics.json |
| novelty_judge | LLM裁判 N0-N3 | 写回 records |
| verifier | 查证器(agent-in-loop)+按族批量回写 | 写回 records |
| judge_blueprints | 跨域候选判定蓝图 | run 内 |
| motif_composer / motif_growth | 母题组合(80对)/扩张晋升(21对) | derived/grown_motifs.json |
| grammar | 问句句式(7式) | 跨域填槽 |
| viz / cli / pipeline | 可视化/命令行/编排 | viz/index.html |

## 工具（tools/）
| 脚本 | 用途 |
|---|---|
| oeis_check / oeis_sweep / oeis_sweep2 | OEIS 离线反查（严格/宽容/去零） |
| big_score / **big_score_ev** | 当务评分（关键词版 / **证据依赖版**） |
| tension_detector / tension_v1 | 语料张力召回 v0/v1（对峙 vs 并存） |
| method3_gen_tension / method3_unified / dedupe_survivors | 张力注入生成/统一池/去重 |
| cross_explore / cross_multidomain / cross_md_v3 | 交叉探索（笛卡尔×过滤）/ 多域(2-3域) / 放大矩阵 |
| verify_cross_md | 真三域仿真（信念修正×迭代×信道） |
| iterate | 迭代环（R 母题→子代） |
| make_ledger | novelty 台账 |
| humanities_math / humanities_sig | 数学×人文计量文体学 + 置换检验 |
| build_motif_map | L0–L4 母题地图(139基元/86方向) |
| graph_space / station3 | 图不变量 / 极小构造（OEIS 过滤） |
| p_A4 / p_B_deep / p_C_integrate / p_C_round2 / p_C_ev_regrade | LONG_PLAN 各阶段脚本 |

## 数据（out/demo/）
problems_*.json、derived/grown_motifs.json、tensions_v0/v1/…_west、gap_template_candidates、method3_*、cross_multidomain、cross_md_v3、cross_md_belief、s2_deep、iteration_gen2、humanities_math、viz/(index.html+data.js)
