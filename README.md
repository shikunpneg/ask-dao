<div align="center">

<img src="assets/logo_white.png" width="150" alt="道">

# 问道 · ask-dao-machine

**道生一，一生二，二生三，三生万物**

一台**知识发现机器**

[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-v0.5.0-orange.svg)](CHANGELOG.md)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blueviolet.svg)](https://shikunpneg.github.io/ask-dao-machine/)
[![Stdlib](https://img.shields.io/badge/deps-纯标准库-brightgreen.svg)](#快速开始)

**[📖 文档](https://shikunpneg.github.io/ask-dao-machine/) · [📊 可视化](docs/viz/paths.html) · [📋 结果与证据](docs/guide/results.md) · [⚠️ 诚实边界](docs/guide/honesty.md)**

</div>

---

## 这是什么

不是问答机，也不只是问题制造机 —— 它有**两条独立的路**：

| | 问题路 · Problem Path | 想象路 · Imagination Path |
|---|---|---|
| **产出** | 问题 | 概念 |
| **输入** | 外部信息 · 日常问题 · 母题 | 词 |
| **需要** | **解决** | **解释** |
| **成功标准** | 答案成立 / 可判 | 语法正确 + 逻辑通畅 + 有推理判断 |

> ⚠️ 两条路**互相独立**。不许用问题路的逻辑（"这有真实所指吗""这新吗"）
> 去评判想象路的概念 —— 那是**范畴错误**。

---

## 架构

![系统架构](assets/architecture.svg)

```
① 感受模块 ──→ ② 问题制造模块 ──→ ③ 执行模块(AI4S)
 视觉/听觉/文本    日常→前问题→科学问题      (解题)
                  →基础领域→问题树→融合
                        ↑
                  ④ 想象模块 (组词→拆词→还原造句→成段→解释)
```

| 模块 | 状态 | 关键文件 |
|---|---|---|
| ① 感受 | 视觉(最小) / 网页文本 / arXiv | `perception_module.py` `web_experience.py` `arxiv_miner.py` |
| ② 问题制造 | 全通 | `corpus_to_problems.py` `counterex_engine.py` `territory_engine.py` `all_domains_engine.py` |
| ③ 执行 (AI4S) | 最小 harness | `ai4s_harness.py` |
| ④ 想象 | 五步全通 | `word_fusion.py` `depth_sentence.py` `reconstruct_*.py` |

📖 [架构详解 →](docs/guide/architecture.md)

---

## 结果

### 一、证据边界推进（最扎实）

**`回文数(base b) + 素数` 覆盖** —— 到 10⁷ 的例外：

| base | 例外数 | 最后例外 | 状态 |
|---|---|---|---|
| **4** | **5** | 4345 | ✅ confirmed |
| **5** | **4** | 1266 | ✅ confirmed |
| **6** | **1** | 1855 | ✅ confirmed |
| **7/8/10/12/15** | **0** | — | ✅ confirmed |
| **9/11/13/14/16** | **1** | 124/126/126/540/539 | ✅ confirmed |
| 2 | 持续增长 | 贴边界 | ❌ rejected |

> **base 10 已推到 10⁸ 零例外，两种独立实现交叉验证。**
> 人类讨论此前止于 ~10⁶（MO #250504 曾怀疑 999999 是反例）。

### 二、机器产出的问题

| 来源 | 数量 |
|---|---|
| 跨进制规律 | 15 |
| 反例驱动（机器答不出的） | 11 |
| 跨域组合 | 7 |
| 科学史未解 | 32 |
| 网页 / arXiv | ~30 |
| **合计** | **260+** |

**科学史挖出的真未解**：奇完全数 · 曲线与直线比较 · 欧拉-哥德巴赫 …

### 三、复核性结果（机器重发现）

| 项目 | 机器 | 已知 |
|---|---|---|
| Tn/TnI 集合类 | **224** | Forte 224 ✓ |
| 最大熵集合类 | 恰 2 个 | all-interval tetrachords ✓ |
| 多完全数 k=2,3,4 | {6,28,496,8128} / {120,672,523776} / {30240,32760} | OEIS A007539 ✓ |

### 四、想象路产出的概念

| 概念 | 核心判断 |
|---|---|
| **记忆调性** | 失忆 = 调性崩溃；记忆调性保证精力分配 |
| **认知压缩** | 理解与失真是同一硬币两面；直觉 = 解压最快路径 |
| **责任催化** | 问责 = 最强催化剂；责任爆炸的临界点 |
| **资本反馈** | 反馈强度决定财富分布形态 |

📋 [结果与证据（含负结果与 12 次自纠错）→](docs/guide/results.md)

---

## 什么算新知识

我们反复重定义过"新"。最终确立**三层问题发现模式和两种新知识产生方式**：

| 三层问题发现模式 | 是什么 | 机器能做到 |
|---|---|---|
| **K1 提出问题** | 把困惑改造成**精确可判**的问题 | ✅ |
| **K2 推进解答** | 对旧问题给出更强证据 / 更大边界 | ✅ |
| **K3 归纳理论** | 从数据归纳出可验证的普遍律 | ⚠️ 部分 |

| 两种新知识产生方式 | 说明 |
|---|---|
| **① 提出新问题** | 爱因斯坦的追光思想实验不是解答，是问题——但它改变了物理 |
| **② 旧问题的新解答** | `回文数+素数` 从 10⁶ 推到 **10⁸ 零例外**——这是新知识 |

> 早期只用"K3 且人类未知"（N3）当唯一及格线，于是把 K1/K2 的实际产出当成"不够格"。这是错的。

📖 [什么算新知识（含三种"新"与显著性）→](docs/guide/new-knowledge.md)

---

## 快速开始

```bash
git clone https://github.com/shikunpneg/ask-dao-machine && cd ask-dao-machine
export PYTHONPATH=src          # Windows PowerShell: $env:PYTHONPATH='src'
```

```bash
# ① 全引擎 + 可视化 + 新颖性门
python -m ask_dao_machine all --out out/demo
```

```bash
# ② 问题路：日常问题 → 科学问题
python tools/run_paths.py problem --input daily --q "为什么黑洞会蒸发?"
```

```bash
# ③ 想象路：词 → 五步（组词/拆词/还原造句/成段/解释）
python tools/run_paths.py imagine --word 记忆调性 --depth 3
```

```bash
# ④ 可视化：问题树 + 概念树 + 概念论证
python tools/build_paths_viz.py     # → docs/viz/paths.html
```

📖 [快速开始（含常见问题）→](docs/guide/quickstart.md)

---

## 使用手册

| 手册 | 内容 |
|---|---|
| [**架构详解**](docs/guide/architecture.md) | 四模块 / 两条路 / 关键设计决策 |
| [**问题路手册**](docs/guide/problem-path.md) | 三种输入 / 反例驱动 / 问题树 L0–L5 / 新颖性门 |
| [**想象路手册**](docs/guide/imagination-path.md) | 五步流程 / 深度变量 d / 成段范例 / 常见误区 |
| [**什么算新知识**](docs/guide/new-knowledge.md) | 三层问题发现模式 / 两种新知识产生方式 / 显著性 |
| [**AI4S 接口**](docs/guide/ai4s.md) | 问题清单格式 / 裁决回灌 / 闭环 |
| [**结果与证据**](docs/guide/results.md) | 全部可复核数字 |
| [**诚实边界**](docs/guide/honesty.md) | 四条硬边界 / 血泪教训 |
| [**术语表**](docs/guide/glossary.md) | 全部术语 |

---

## 想象路的核心原则

> **每个词都有意义，只不过是我们缺少想象力，无法理解它。**

因此**不存在空想**。任何组合词都有意义 —— 任务不是判断"有没有意义"，
而是**想出一个自洽的理解**。

**成段范例（记忆调性）**：

> 记忆调性，若是一个真实概念，指的是：记忆不是平铺的档案，而是围绕某些"主音"组织。
> **据此可以推断**：失忆不是记忆的"丢失"，而是记忆的"调性崩溃"。
> **更进一步**：记忆有调性，恰恰保证了人类能更高效地分配精力。
> **但必须区分**：失忆症是一种疾病，而记忆调性是正常现象 —— 正如"心律失常"是病，"心跳有节律"是正常。
> **因此**，记忆调性回答"正常记忆如何组织"，失忆症回答"组织被摧毁时发生什么"。

📖 [想象路手册 →](docs/guide/imagination-path.md)

---

## 诚实边界

| # | 边界 |
|---|---|
| 1 | **N3（世界新问题）至今 = 0** —— 不许粉饰 |
| 2 | **"检索未见" ≠ "新"** —— 参照系只有 OEIS + 检索，文献门需人/联网 |
| 3 | **显著性 > 新颖性** —— 任选参数的序列同样"OEIS 未见"，过门是廉价的 |
| 4 | **73% 的产出无法判定** —— "不可判" ≠ "已排除" |

**明确不承诺**：产出"世界级新问题"。

📖 [诚实边界（含血泪教训与 12 次自纠错）→](docs/guide/honesty.md)

---

## 目录结构

```
ask-dao-machine/
├── assets/                     # logo + 架构图
│   ├── logo_white.png          # 极简书法「道」
│   └── architecture.svg
├── src/ask_dao_machine/        # 包：引擎 / 判定器 / 母题库 / 可视化 / CLI
├── tools/                      # ~100 个工具（两条路的引擎与探针）
├── docs/
│   ├── index.md                # GitHub Pages 首页
│   ├── guide/                  # ← 使用手册（9 篇）
│   ├── viz/                    # 可视化（paths.html）
│   └── *.md                    # 实验史 / 执行日志 / 长程计划
├── tests/                      # 冒烟测试
└── handoff/                    # 交接包
```

---

<div align="center">

**问道 · ask-dao-machine** v0.5.0 · MIT License

*道生一，一生二，二生三，三生万物*

</div>
