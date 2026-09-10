# 领域交叉融合 × 母题扩张 —— 实施计划 (PLAN-CROSS-MOTIF)

## 目标
两条此前只有"脚手架/演示"的管线做成闭环:
1. **母题扩张**: 母题不只靠人工编辑 registry; 机器组合->实例化->试判->晋升(带 parent 溯源)。
2. **领域交叉融合**: 消灭"只填槽/只蓝图"状态 —— 每个跨域候选必须落到 {已判定 | 可轻量仿真 | 明确不可判}。

## 成功指标(每轮)
- 扩张: 新增 confirmed 母题 ≥ N(带试判证据 + parent), 其中"晋升后被后续问题复用"数 ≥ 1。
- 融合: 每个候选有 judgement 或显式不可判理由; 融合线产出的"已判融合命题"≥ 3/轮。
- 新问题率: novelty ledger 更新(N0/N1/N2/N3), R/突破计数。

## Phase A 母题扩张
- A0 结构: registry v2 = {name, domain, type, note} + 可选 carrier(机器可枚举载体) + stage + parent。
- A1 组合实例化: motif_composer 的 math-route DM 对, 直接小规模试判(阈值/存在/纪录), 有非平凡结果 -> stage=confirmed。
- A2 参数变异: 字母表 k / 步集 / 模 m / 约束串 / 递归规则 — 参数化家族(combo 已含雏形)。
- A3 晋升: confirmed 母题进入 grown_motifs.json, 后续引擎可引用(parent 链保持)。

## Phase B 真融合
- B1 度量函子 × 载体库: 熵/偏差/游走/复杂度 作为"眼睛"作用于 质数/因子和/语法/字符串/编码。
- B2 机制模板 × 对象: 迭代-收敛(选择方程/信念修正/递归)、覆盖-阈值、纪录-极值 —— 换对象重放。
- B3 概念对桥: 跨域轴(优美-崇高/选择-漂变/功能-结构) 以可计算代理进入生成。
- 路由: 数值判(fusion/math/combo) > 轻量仿真(确定性迭代/随机模拟, 本机) > blueprint(真实验, 注明原因)。

## Phase C 闭环
- 迭代环: R/边界意外 -> 子代(扩界/变约束/加母题变异) -> 存活率统计。
- 台账: out/demo/novelty_ledger.md 每轮追加 {generated, judged, R, breakthrough, promoted, N-distribution}。
