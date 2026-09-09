# ask-dao-machine · 问题制造器

把"问题"当一等公民来**制造**的可复用模块：母题库（登记库）× 组合引擎 → 候选命题 → 判定器（真 / 假 / 悬置 / 待实验）→ 带**完整出处链**的问题记录 → 可视化解释"问题是怎么长出来的"。

## 一句话

不是问答机，是**问题制造机**：输入是母题与日常疑问，输出是良构、可判、带诚实标签（是否已知著名/是否惊喜候选）的问题及其生长路径。

## 快速开始

```bash
# 无需安装也能跑(纯标准库)
cd ask-dao-machine
set PYTHONPATH=src          # Windows PowerShell: $env:PYTHONPATH='src'
python -m ask_dao_machine all --out out/demo

# 或安装为包
pip install -e .
ask-dao-machine math --out out/math
```

产物：
- `out/demo/problems_math.json`、`problems_aesthetics.json` —— 问题集（含出处链）
- `out/demo/viz/index.html` —— **可视化**（双击打开；每个问题展开可见 母题链→模板→参数→判定记录→诚实标签，树形展示生长关系）

## 架构

```
assets/registry.json (86 母题登记库)
        │
src/ask_dao_machine/
   registry.py        母题库: 数学核心32(可实例化) + 全域54(物理/生物/心理/信息/工程/伦理/美学/语言/元层)
   model.py           数据模型: ProblemRecord(出处链) / ProblemSet / 状态机(真·假·悬置·待实验)
   judges_math.py     判定原语(纯函数): 阈值扫描/存在例证/结构反例/构造/表对照
   math_engine.py     数学问题制造器(25 题/1.4s)
   aesthetics_engine.py 美学问题制造器(8 题, 判定权=人类/实验)
   pipeline.py        ProblemMaker: 统一入口 run(domain) → ProblemSet
   viz.py             可视化构建: ProblemSet+Registry → data.js + index.html
   cli.py             CLI
```

## 诚实层（产品纪律）

- **状态**只来自判定器：`真`(构造/验证到上限) `假`(反例/结构反例) `悬置`(开放·命中著名问题如实标注) `待实验/待评审`。
- **新颖性双标签**：命中内置"著名问题签名"→ `已知`；未命中 → `惊喜候选(需查证)`，**不冒充新**。
- 每个问题记录都带 provenance（生长步骤），可视化据此解释"为什么是这么长出来的"，而不是一段凭空文字。

## 扩展：如何加域/加母题

1. 加母题：编辑 `src/ask_dao_machine/assets/registry.json`（name/type/note）。
2. 加域引擎：实现 `run(limits) -> (roots:[TreeRoot], records:[ProblemRecord])`，注册进 `pipeline.py` 的 `engines`。
3. 加模板/判定：数学域在 `math_engine.py` 内用 `judges_math` 原语组合。

## 路线

- v0.1 单文件原型 → **v0.2 本产品**：包结构 / CLI / 出处链 / 可视化
- 下一件：registry 其余 54 个母题逐域接通判定器（物理对称×守恒最先）；更多数学模板扩大惊喜候选率

（仓库：https://github.com/shikunpeng/ask-dao-machine —— 推送前请先在本机配置 git 凭证）
