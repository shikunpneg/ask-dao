# ask-dao-machine · 问道

> 朝闻道，夕死可矣。
>
> 一台**知识发现机器**：不是问答机，也不只是问题制造机——它有**两条独立的路**，
> 一条生产**问题**（待解决），一条生产**概念**（待解释）。

---

## 系统总览：两条路

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  问题路 (Problem Path)  —— 产问题，需解决                                       ║
║    输入: 外部信息(视觉/听觉/文本) │ 日常问题 │ 母题                              ║
║    流水: 日常问题 → 前问题 → 科学问题 → 基础领域 → 问题树 → 领域融合              ║
║    出口: 可判问题清单(带判定路由) → AI4S 执行模块                                ║
║    标准: 答案成立 / 可判                                                        ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  想象路 (Imagination Path)  —— 产概念，需解释                                   ║
║    输入: 词                                                                     ║
║    流水: 组词 → 拆词(深度d) → 还原造句(嵌套/推理/判断/比较) → 成段 → 解释        ║
║    出口: 被理解的概念 / 理论                                                     ║
║    标准: 解释语法正确 + 逻辑通畅 + 有推理判断                                     ║
║    原则(不可动摇): 每个词都有意义，只不过是我们缺少想象力，无法理解它。            ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

两条路**互相独立，各有各的成功标准**：
- 想象路的概念**不是拿来"解决"的**，是拿来**"解释/理解"**的。
- 不许用问题路的逻辑（"是否有真实所指""是否已研究""是否新"）去评判想象路的概念——那是范畴错误。

---

## 五模块架构

```
① 感受模块 → ② 问题制造模块 → ③ 执行模块(AI4S)
  (视觉/听觉/文本)   (日常→前问题→科学问题      (解题)
                     →基础领域→问题树→融合)
                          ↑
                    ④ 想象模块 (造词→拆词→还原造句→成段→解释)
```

| 模块 | 状态 | 工具 |
|---|---|---|
| ① 感受 | 视觉(最小) / 网页文本 / arXiv | `perception_module.py` `web_experience.py` `arxiv_miner.py` |
| ② 问题制造 | 全通 | `corpus_to_problems.py` `counterex_engine.py` `territory_engine.py` `all_domains_engine.py` |
| ③ 执行(AI4S) | 最小 harness | `ai4s_harness.py` |
| ④ 想象 | 五步全通 | 见下 |

---

## 快速开始

```bash
git clone https://github.com/shikunpneg/ask-dao-machine && cd ask-dao-machine
export PYTHONPATH=src          # Windows PowerShell: $env:PYTHONPATH='src'

# 全引擎 + 可视化 + 新颖性门
python -m ask_dao_machine all --out out/demo

# 两条路统一入口
python tools/run_paths.py problem --input daily --q "为什么黑洞会蒸发?"
python tools/run_paths.py problem --input text  --src <语料文件>
python tools/run_paths.py problem --input motif --m "质数"
python tools/run_paths.py imagine --word 记忆调性 --depth 3
python tools/run_paths.py imagine --pairs 经济 信息
```

---

## 问题路详解

**输入接口**（三种）：

| 输入 | 说明 | 工具 |
|---|---|---|
| 外部信息 | 视觉(图像结构) / 听觉 / 文本(语料/网页/arXiv) | `perception_module.py` `web_experience.py` `arxiv_miner.py` |
| 日常问题 | "为什么X?" "X有多少?" → 定型为科学问题 | `question_refiner.py` |
| 母题 | 领域母题 → 方向模板 → 实例化问题 | `registry.py` `make_ledger.py` |

**流水线**：
```
日常问题 → 前问题 → 科学问题 → 基础领域 → 问题树 → 领域融合
```
- 反例驱动：`counterex_engine.py`（例外集 → 刻画/有限性/密度问题）
- 问题树：`territory_engine.py`（Spec → L0–L5 问题，自动分型 char/holds）
- 全领域并行：`all_domains_engine.py`（14 领域 × 14 进程）
- 领域融合：`deep_fusion.py`（操作子×结构）、`field_fusion.py`（领域级，含结构桥梁判据）
- 新问题判定：`novelty_gate.py`（OEIS 实查 + 结构可推性 + 显著性证书）
- 执行：`ai4s_harness.py`（独立验证 + 裁决回灌）

**诚实纪律**：N3（世界新问题）至今 = 0，不许粉饰；"检索未见" ≠ "新"。

---

## 想象路详解（五步）

**输入接口**：**词**（任意词，或词对）

| 步 | 做什么 | 工具 |
|---|---|---|
| ① 组词 | 穷尽领域专业词组合（82×82 = 6642） | `word_fusion.py` `word_understand.py` |
| ② 拆词 | 问"它是什么?" → 拆实体 → 再问 → 可再拆？ **深度 d 是变量** | `depth_sentence.py` `depth_batch.py` |
| ③ 还原造句 | 从底往上还原；**嵌套 + 推理 + 判断 + 比较** | `reconstruct*.py` |
| ④ 成段 | 定义 → 判断 → 比较 → 结论 | `reconstruct_judge.py` `reconstruct_compare.py` |
| ⑤ 解释 | 指什么现象/机制/深问 | `understand_deep.py` |

**范例（记忆调性）**：
> 记忆调性，若是一个真实概念，指的是：记忆不是平铺的档案，而是围绕某些"主音"组织。
> **据此可以推断**：失忆不是记忆的"丢失"，而是记忆的"调性崩溃"。
> **更进一步**：记忆有调性，恰恰保证了人类能更高效地分配精力。
> **但必须区分**：失忆症是一种疾病，而记忆调性是正常现象——正如"心律失常"是病，"心跳有节律"是正常。
> **因此**，记忆调性回答"正常记忆如何组织"，失忆症回答"组织被摧毁时发生什么"。

**详版**：见 [`docs/IMAGINATION_MODULE.md`](docs/IMAGINATION_MODULE.md)

---

## 目录结构

```
ask-dao-machine/
├── src/ask_dao_machine/    # 包: 引擎/判定器/母题库/可视化/CLI
├── tools/                  # ~100 个工具: 两条路的引擎与探针
├── docs/                   # 设计/计划/日志/实验记录
│   ├── ARCHITECTURE_V3.md      # 五模块总图
│   ├── IMAGINATION_MODULE.md   # 想象路五步详解
│   ├── EXECUTION_LOG.md        # R1–R90 逐轮执行日志
│   ├── EXPERIMENT_RECORD.md    # 完整实验史
│   ├── LONG_PLAN_V2.md         # 长程计划
│   └── K2_LEDGER.md            # 证据推进台账
├── tests/                  # 冒烟测试
├── handoff/                # 交接包(提示词/上下文/快照)
└── out/demo/               # 产物(问题清单/概念/可视化)
```

---

## 当前产出

| 路 | 产出 |
|---|---|
| 问题路 | 问题清单 260+ 条（含判定路由）；跨进制规律（harness 13 条 confirmed） |
| 想象路 | 6642 组合词；概念树（自然深度 3）；3 个完整论证段落；6 个深度解释 |

---

## 诚实边界

1. **N3（世界新问题）至今 = 0** —— 机器能产"真问题""已知·未解问题""参照系未见候选"，但**没有一条通过三重门槛**。
2. **"检索未见" ≠ "新"** —— 手头参照系只有 OEIS + 检索；文献门需人/联网。
3. **想象路的成功标准是解释，不是真实所指** —— 不许用问题路逻辑评判。
4. **显著性 > 新颖性** —— 任选参数的序列同样"OEIS 未见"，唯一拦得住的是显著性证书。

---

## 版本

- v0.1 单文件原型 → v0.2 包结构 / CLI / 出处链 / 可视化
- **v0.3 两条路**（本版）：问题路 + 想象路，统一入口 `tools/run_paths.py`

（仓库：https://github.com/shikunpneg/ask-dao-machine）
