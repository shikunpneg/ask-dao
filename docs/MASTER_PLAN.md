# MASTER_PLAN —— 制造知识的问题机器：总计划与里程碑

> 目标一句话: 从 v0.15 推进到"能产出**可审计的真实新问题**的最小闭环", 产品持续在
> github.com/shikunpneg/ask-dao-machine。判定口径: LLM 为操作层裁判(N0-N3), 人工仅出版级介入;
> 诚实纪律: 状态只来自判定器, 惊喜=查证+裁判, 不冒充新。

## P0 理论底盘(已基本完成 ✓)
文件: _theory 审计/definitions_audit/basic_domains/plan_v2; product 内 docs(DESIGN/纪律/MOTIF_DEFINITION/PLAN_CROSS_MOTIF)。
- 母题定义分层 L0-L4 + 操作判据(MOTIF_DEFINITION) ✓
- 裁判权口径(LLM操作层/人类出版级) ✓

## P1 母题系统重建(进行中)
- 1.1 数学母题地图: 115 基元 = 52 方向(L3) + 17 算子 + 24 对象 + 12 结构 (map v1 ✓, 存 out/demo/motif_map.json)
- 1.2 每域 L4→L0 建图(物理/生物/心理/信息/工程/伦理/美学/语言 逐个; 当前多为占位 → 补)
- 1.3 载体(可枚举) + 方向问题模板(该方向典型问法) + 判定路由 逐条挂接 → registry v2
- 1.4 母题扩张闭环: 组合→实例化→试判→晋升(confirmed/needs_extend/hypothesis) ✓雏形(grown_motifs), 需"晋升后被复用"证明

## P2 组合引擎族(升级)
- 2.1 对象级: records(两数和/覆盖) / combo(禁构/游程/游走) / ling(语法×熵) ✓
- 2.2 **方向级组合引擎(L3×L1 / L3×L3)**: "A方向的典型问法模板" × "B方向对象/算子" → 候选
      第一波样例已演示(composition_demo, 3n+k 探针判出 k偶结构逃逸) → 引擎化
- 2.3 语法槽位升级: grammar frames 接 L3 方向模板(不只对象类)

## P3 判定器扩张
- 3.1 数值族(已多) 3.2 轻量仿真族(群体动力学迭代/图算法/随机模拟—本机可跑)
- 3.3 blueprint→带可证伪标准(judge_blueprints) 3.4 实验数据接口(美学 A01/A03 最易起步)

## P4 新颖性工程
- 4.1 参照系: 种子表(16族) → OEIS 级离线索引(stripped 若可取) → R 有意义
- 4.2 查证器(agent-in-loop, 8/26 已跑) 4.3 LLM裁判 novelty_judge(N0-N3) ✓
- 4.4 迭代环: R/边界意外→子代(扩界/变异)→存活率 4.5 novelty_ledger 台账(每轮)

## P5 产品与可视化
- 母题树/问题树/provenance 可视化(现有 viz 需扩: L0-L4 层 + derived/grown 母题层 + 裁判徽章)
- CLI/包完整(pyproject) ✓; README/DESIGN 与现状同步; 持续 push

## P6 评估与里程碑验收
指标: 稳定真问题率 / R率(每百题) / 晋升复用率 / N2-N3 产出 / 迭代存活率 / 内部抽查一致性
- M1 数学+物理 L3 方向模板库 ≥80 条, 其中 ≥30 条可实例化判定
- M2 方向级组合引擎每轮产 ≥3 条 L3×L3 "已判"融合命题
- M3 novelty_ledger 每轮更新; 查证器跑完全部悬置候选
- M4 出现经 LLM 裁判为 N2 且经 2 轮迭代存活 的候选 ≥1
- M5 v1.0 发布(含可视化母题树+裁判记录), README 全同步

## 依赖顺序建议
P1(地图/模板) → P2(方向组合引擎) → P3(仿真判定) ∥ P4(参照系/台账) → M 验收; P5 贯穿。
