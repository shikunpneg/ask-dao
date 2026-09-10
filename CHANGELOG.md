# CHANGELOG

## v0.5.0 —— 极简 logo + 架构图 + 详细手册 + GitHub Pages（2026-09-11）

### 新增
- **极简 logo** `tools/art_logo.py`：书法「道」二值化提墨、去纸纹与斑点 → 纯墨色（透明/白底/圆角）
  `assets/logo.png`(透明) / `logo_white.png`(白底) / `favicon.png`
- **架构图** `tools/arch_diagram.py` → `assets/architecture.svg`（SVG：四模块 + 两条路 + 诚实边界）
- **详细使用手册** `docs/guide/`（9 篇）：
  架构详解 / 快速开始 / 问题路手册 / 想象路手册 / 什么算新知识 / AI4S 接口 / 结果与证据 / 诚实边界 / 术语表
- **GitHub Pages 站点** `docs/_config.yml` + `docs/index.md`
- README 重写：极简 logo + 架构图内嵌 + **结果突出** + 手册链接表

### 改进
- 可视化深色页面改用白底 logo（黑墨透明版在深色下不可见）

## v0.4.0 —— 节点连线树 + 书法 logo（2026-09-11）

### 新增
- **Logo 艺术化** `tools/art_logo.py`：用**用户提供的书法原图**（`道.png`）处理 ——
  裁边 + 提对比 + 宣纸暖调光晕 + 朱红「问道」印章 + 圆角
  产出 `assets/logo.png`(640) / `logo_small.png`(240) / `logo_banner.png`(1100x300)
  原图留档 `assets/dao_original.png`
- **节点连线树** `tools/tree_svg.py`：SVG 树渲染器（宣纸底 + 墨线 + 节点）
  - `render_concept_tree`：概念 → 实体 → 子实体 → 原子概念（拆词来龙去脉）
  - `render_problem_tree`：领域根 → 问题（生成来路）
- 可视化升级：`build_paths_viz.py` 现渲染 **23 域问题树 + 11 概念树 = 34 棵节点连线树**
  （318 节点 / 584 标签），不再是纯表格

### 说明
树风格与 logo 一致：宣纸底、墨色节点、暖褐连线。
## v0.3.1 —— README / Logo / 可视化（2026-09-11）

### 新增
- **Logo**：书法「道」（行楷 + 宣纸 + 「问」印章）— `assets/logo.png`，由 `tools/make_logo.py` 生成
- **统一可视化** `tools/build_paths_viz.py` → `docs/viz/paths.html`（自包含，双击可开）
  - 一、两条路总览  二、问题树（260 条 / 23 领域，带判定路由）
  - 三、概念树（深度 d 拆解）  四、概念论证（定义→判断→比较→结论）
- **README 重写**：仿 minimind 风格 — logo + slogan「道生一，一生二，二生三，三生万物」
  + 项目目的（发现新知识）+ 什么是新知识（K1/K2/K3 三层 + 三种"新"）+ 架构图 + 可视化 + 使用文档
- **LICENSE**（MIT）

### 修复
- 可视化两列布局在窄视口下折行 → 改 `auto-fit minmax(320px,1fr)`

## v0.3.0 —— 两条路（2026-09-11）

**架构确立**：系统 = 两条独立的路 + 五模块。

### 新增：想象路（Imagination Path）
- **输入接口：词**（任意词或词对）
- 五步流程：
  1. **组词** — 穷尽领域专业词组合（82×82 = 6642）：`word_fusion.py` `word_understand.py`
  2. **拆词**（深度 d 为变量）— 问"它是什么?" → 拆实体 → 再问 → 可再拆？：`depth_sentence.py` `depth_batch.py`
  3. **还原造句**（嵌套 + 推理 + 判断 + 比较）— 从底往上还原：`reconstruct.py` `reconstruct_sent.py` `reconstruct_judge.py` `reconstruct_compare.py`
  4. **成段** — 定义 → 判断 → 比较 → 结论
  5. **解释** — 指什么现象/机制/深问：`understand_deep.py`
- **不可动摇原则**：每个词都有意义，只不过是我们缺少想象力，无法理解它（不存在空想）
- **成功标准**：解释语法正确 + 逻辑通畅 + 有推理判断（**不是**"有真实所指"——那是问题路逻辑）

### 新增：问题路输入接口
- **外部信息**：视觉 `perception_module.py` / 网页文本 `web_experience.py` / arXiv `arxiv_miner.py`
- **日常问题**：`question_refiner.py`（分类 + 判定路由）
- **母题**：`registry.py` + `make_ledger.py`

### 新增：统一入口
- `tools/run_paths.py` —— 两条路的 CLI（`problem` / `imagine` 子命令）

### 新增文档
- `docs/ARCHITECTURE_V3.md` —— 五模块总图
- `docs/IMAGINATION_MODULE.md` —— 想象路五步详解
- `docs/K2_LEDGER.md` —— 证据推进台账
- README 全重写（两条路总览）

### 问题路进展（R22–R69）
- 重建新颖性判定：`oeis_index.py`（倒排索引）+ `novelty_gate.py`（四道真门，N3 路径可达）
- 反例驱动引擎 `counterex_engine.py`（只提机器答不出的问题）
- 问题树 `territory_engine.py`（L0–L5 分层 + 谱系门）
- 全领域并行 `all_domains_engine.py`（14 领域 × 14 进程）
- 深层融合 `deep_fusion.py` / `field_fusion.py`（操作子×结构 / 领域级+结构桥梁）
- AI4S harness `ai4s_harness.py`（独立验证跨进制 13 条 confirmed）
- 跨进制规律：`回文数(b)+素数` 例外有限（b≥4），到 3×10⁷ 稳定
- **N3 仍 = 0**（诚实）

---

## v0.2.0 —— 产品化（2026-09-09）
- 包结构 `src/ask_dao_machine/`：model（出处链）/ registry（86 母题）/ 各引擎 / pipeline / viz / cli
- CLI `python -m ask_dao_machine`；可视化 `out/demo/viz/index.html`

## v0.1.0 —— 单文件原型（2026-09-09）
- `machine_v1/`：math_machine / aesthetics_machine + viz
