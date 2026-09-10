<div align="center">

<img src="assets/logo.png" width="180" alt="道">

# 问道 · ask-dao-machine

**道生一，一生二，二生三，三生万物**

不是问答机，也不是单纯的问题制造机 —— 它是一台**知识发现机器**

[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-v0.3.0-orange.svg)](CHANGELOG.md)
[![Stdlib](https://img.shields.io/badge/deps-纯标准库-brightgreen.svg)](#快速开始)

</div>

---

## 📖 目录

- [项目目的：发现新知识](#项目目的发现新知识)
- [什么是新知识](#什么是新知识)
- [系统架构：两条路](#系统架构两条路)
- [可视化：问题树与概念树](#可视化问题树与概念树)
- [快速开始](#快速开始)
- [使用文档](#使用文档)
- [目录结构](#目录结构)
- [诚实边界](#诚实边界)

---

## 项目目的：发现新知识

> **这台机器只做一件事：发现新知识。**

已有的 AI4S（AI for Science）生态擅长**解决问题**——给定问题，它能算出答案。
但"问题从哪来"这一环长期空缺：**能定义问题、提出问题的系统，远比能解题的系统稀缺。**

问道补的正是这一环。它认为知识产出于**两条独立的路**：

| | 问题路 | 想象路 |
|---|---|---|
| **产出** | 问题 | 概念 |
| **需要** | **解决** | **解释** |
| **成功标准** | 答案成立 / 可判 | 语法正确 + 逻辑通畅 + 有推理判断 |
| **输入** | 外部信息 · 日常问题 · 母题 | 词 |

两条路**互相独立**。想象路造出的概念**不是拿来"解决"的**，而是拿来**"理解"**的——
用问题路的逻辑（"这有真实所指吗""这新吗"）去评判想象路的概念，是范畴错误。

---

## 什么是新知识

我们反复重定义过"新"。最终确立**三层问题发现模式和两种新知识产生方式**：

| 层 | 是什么 | 举例 | 机器能做到 |
|---|---|---|---|
| **K1 提出问题** | 把日常困惑/知识裂缝，改造成**精确可判**的问题 | "言不尽意" → 最小文法类分离问题 | ✅ |
| **K2 推进解答** | 对**旧问题**给出更强证据 / 更大验证边界 | `回文数+素数` 从 10⁶ 推到 **10⁸ 零例外** | ✅ |
| **K3 归纳理论** | 从数据里归纳出**可验证的普遍律** | 格律熵 = n/2+1 bit | ⚠️ 部分 |

**关键判断**（两条，均为项目共识）：

1. **提出新问题，本身就是新知识的第一步，而且很重要。**
   爱因斯坦的追光思想实验不是解答，是问题——但它改变了物理。
   哥德巴赫猜想的**提出**（1742）比它的任何进展都更早地定义了一个领域。

2. **旧问题的新解答，也是新知识。**
   这是机器最擅长、最扎实、最确定的一类产出：不必造人类未知的问题，
   只要把已知问题的证据边界**推进一个数量级**。

**"新"的三种形态**：

```
陈述新  —— 这个句子没出现过        （廉价：换个说法就算新）
对象新  —— 这个结构没被研究过      （可造：但查证后常被占领）
接口新  —— 问题站在刚被解锁的节点上 （稀缺：科学史大问题的真实产地）
```

> 真正的大问题不是"没人问过"，而是"**问不出来**"——它在某个节点之前，
> 既没有问它的动机，也没有答它的工具。

---

## 系统架构：两条路

```
┌──────────────────────────────────────────────────────────────────────────┐
│  问题路 (Problem Path)  ——  产问题，需解决                                  │
│                                                                          │
│   输入: 外部信息(视觉/听觉/文本) │ 日常问题 │ 母题                           │
│   流水: 日常问题 → 前问题 → 科学问题 → 基础领域 → 问题树 → 领域融合           │
│   出口: 可判问题清单(带判定路由) → AI4S 执行模块                             │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↑
┌──────────────────────────────────────────────────────────────────────────┐
│  想象路 (Imagination Path)  ——  产概念，需解释                              │
│                                                                          │
│   输入: 词                                                                │
│   流水: 组词 → 拆词(深度d) → 还原造句(嵌套/推理/判断/比较) → 成段 → 解释      │
│   出口: 被理解的概念 / 理论                                                │
│   原则: 每个词都有意义，只不过是我们缺少想象力，无法理解它。                   │
└──────────────────────────────────────────────────────────────────────────┘
```

### 五模块

```
① 感受模块 ──→ ② 问题制造模块 ──→ ③ 执行模块(AI4S)
 视觉/听觉/文本    日常→前问题→科学问题      (解题)
                  →基础领域→问题树→融合
                        ↑
                  ④ 想象模块 (造词→拆词→还原造句→成段→解释)
```

| 模块 | 状态 | 关键文件 |
|---|---|---|
| ① 感受 | 视觉(最小) / 网页文本 / arXiv | `perception_module.py` `web_experience.py` `arxiv_miner.py` |
| ② 问题制造 | 全通 | `corpus_to_problems.py` `counterex_engine.py` `territory_engine.py` `all_domains_engine.py` |
| ③ 执行 (AI4S) | 最小 harness | `ai4s_harness.py` |
| ④ 想象 | 五步全通 | `word_fusion.py` `depth_sentence.py` `reconstruct_*.py` `understand_deep.py` |

### 关键引擎

| 引擎 | 作用 | 纪律 |
|---|---|---|
| `counterex_engine` | 反例驱动：从例外集长出机器**答不出**的问题 | 只提机器结算不了的问题 |
| `territory_engine` | 问题树 L0–L5 分层 + 谱系门 | 每爬一层必须机器实测 |
| `novelty_gate` | 四道真门：机器真判 → OEIS 实查 → 结构可推性 → 显著性证书 | N3 路径已证明可达 |
| `all_domains_engine` | 14 领域 × 14 进程并行扫描 | 全领域覆盖 |
| `field_fusion` | 领域级融合（含**结构桥梁**判据） | 无共享结构的配对是空洞笛卡尔积 |

---

## 可视化：问题树与概念树

生成自包含的交互页面（双击即可打开，无需服务器）：

```bash
python tools/build_paths_viz.py     # → docs/viz/paths.html（入库）与 out/demo/viz/paths.html
```

📄 **[打开可视化 →](docs/viz/paths.html)**

页面包含四个部分：

| 部分 | 内容 |
|---|---|
| **一、两条路** | 问题路 / 想象路 的输入、流水、出口、标准 |
| **二、问题树** | 260 条问题，按 23 个领域分组，每条带**判定路由**与状态徽章 |
| **三、概念树** | 9 个概念按**深度 d** 拆解到原子概念（如"记忆调性"→ 过去/影响/现在/主音/音级/偏离/回归） |
| **四、概念论证** | 定义 → **据此可以推断** → **但必须区分** → 因此 |

> 范例（概念论证）：
> **记忆调性**，若是一个真实概念，指的是：记忆不是平铺的档案，而是围绕某些"主音"组织。
> **据此可以推断**：失忆不是记忆的"丢失"，而是记忆的"调性崩溃"。
> **更进一步**：记忆有调性，恰恰保证了人类能更高效地分配精力。
> **但必须区分**：失忆症是一种疾病，而记忆调性是正常现象——正如"心律失常"是病，"心跳有节律"是正常。
> **因此**，记忆调性回答"正常记忆如何组织"，失忆症回答"组织被摧毁时发生什么"。

---

## 快速开始

```bash
git clone https://github.com/shikunpneg/ask-dao-machine && cd ask-dao-machine
export PYTHONPATH=src          # Windows PowerShell: $env:PYTHONPATH='src'
```

```bash
# 全引擎 + 可视化 + 新颖性门
python -m ask_dao_machine all --out out/demo
```

```bash
# 两条路统一入口
python tools/run_paths.py problem --input daily --q "为什么黑洞会蒸发?"
```

```bash
# 可视化（问题树 + 概念树 + 概念论证）
python tools/build_paths_viz.py     # → docs/viz/paths.html
```

---

## 使用文档

### 问题路

```bash
# ① 外部信息 → 日常问题 → 科学问题
python tools/run_paths.py problem --input text  --src <语料文件>
python tools/web_experience.py                   # 网页抓取
python tools/arxiv_miner.py                      # arXiv 前沿摘要 → 开放点

# ② 日常问题 → 科学问题（定型 + 判定路由）
python tools/run_paths.py problem --input daily --q "为什么黑洞会蒸发?"

# ③ 母题 → 问题树
python tools/run_paths.py problem --input motif --m "质数"

# ④ 反例驱动（只提机器答不出的问题）
python -m ask_dao_machine.counterex_engine

# ⑤ 全领域并行扫描
python tools/all_domains_engine.py

# ⑥ 新颖性门（OEIS 实查）
python tools/novelty_gate.py
```

### 想象路

```bash
# 五步：组词 → 拆词(d) → 还原造句 → 成段 → 解释
python tools/run_paths.py imagine --word 记忆调性 --depth 3
python tools/run_paths.py imagine --pairs 经济 信息

python tools/word_fusion.py           # ① 组词（6642 组合）
python tools/depth_sentence.py        # ② 拆词（深度变量 d）
python tools/reconstruct_compare.py   # ③④ 还原造句 + 成段（含比较）
python tools/understand_deep.py       # ⑤ 解释
```

### AI4S 执行

```bash
python tools/ai4s_harness.py          # 独立验证 + 裁决回灌
```

---

## 目录结构

```
ask-dao-machine/
├── assets/logo.png             # logo（书法「道」）
├── src/ask_dao_machine/        # 包：引擎 / 判定器 / 母题库 / 可视化 / CLI
├── tools/                      # ~100 个工具（两条路的引擎与探针）
├── docs/
│   ├── ARCHITECTURE_V3.md      # 五模块总图
│   ├── IMAGINATION_MODULE.md   # 想象路五步详解
│   ├── EXECUTION_LOG.md        # R1–R90 逐轮执行日志
│   ├── EXPERIMENT_RECORD.md    # 完整实验史
│   ├── LONG_PLAN_V2.md         # 长程计划
│   └── K2_LEDGER.md            # 证据推进台账
├── tests/                      # 冒烟测试
├── handoff/                    # 交接包（提示词 / 上下文 / 快照）
└── out/demo/                   # 产物（问题清单 / 概念 / 可视化）
```

---

## 诚实边界

1. **N3（世界新问题）至今 = 0。**
   机器能产"真问题""已知·未解问题""参照系未见候选"，但**没有一条通过三重门槛**。
   不许粉饰。

2. **"检索未见" ≠ "新"。**
   手头参照系只有 OEIS + 检索；真正的文献门需要人/联网。

3. **想象路的成功标准是"解释"，不是"真实所指"。**
   不许用问题路的逻辑评判想象路的概念。

4. **显著性 > 新颖性。**
   任选参数的序列同样"OEIS 未见"——过 OEIS 门是廉价的，
   唯一拦得住的是**显著性证书**（具名对象的不变量 + 任意选择扰动下保持）。

5. **验证边界是机器最扎实的产出。**
   例如 `回文数+素数` 已被推到 10⁸ 零例外（人类讨论此前止于 10⁶），
   并用两种独立实现交叉验证。

---

<div align="center">

**问道 · ask-dao-machine** v0.3.0

*道生一，一生二，二生三，三生万物*

</div>
