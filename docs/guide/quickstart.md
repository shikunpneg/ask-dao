---
title: 快速开始
---

# 快速开始

## 环境

- Python 3.9+
- **纯标准库**可跑基础功能；数值/图像功能需 `numpy` `pillow`（可选）
- OEIS 反查需下载 `stripped.gz` 到 `data/`（可选，39.9 万序列，32MB）

## 安装

```bash
git clone https://github.com/shikunpneg/ask-dao-machine && cd ask-dao-machine
export PYTHONPATH=src          # Windows PowerShell: $env:PYTHONPATH='src'
```

## 第一次运行：跑全引擎

```bash
python -m ask_dao_machine all --out out/demo
```

输出：

```
[math]     {'problems': 25, ...} -> out/demo/problems_math.json
[combo]    {'problems': 23, ...}
[records]  {'problems': 28, ...}
[sparse]   {'problems': 4,  ...}
[counterex]{'problems': 11, ...}
...
[novelty]  全库分级: {'不可判(无序列)': 85, 'N0': 16, 'N1': 7, 'N2': 4}
```

> ⚠️ **注意 `不可判` 这一项**：它表示该批问题**没有机器可判的数据**（如无整数序列），
> 因此**进不了新颖性门**。这不是"已排除"，是"无法判定"。

## 第二次：看可视化

```bash
python tools/build/build_paths_viz.py     # → docs/viz/paths.html
```

双击 `docs/viz/paths.html` 打开：两条路总览 / 问题树 / 概念树 / 概念论证。

## 第三次：用两条路

### 问题路

```bash
# 日常问题 → 科学问题
python tools/core/run_paths.py problem --input daily --q "为什么黑洞会蒸发?"

# 外部信息 → 日常问题
python tools/research/arxiv_miner.py            # arXiv 前沿 → 开放点
python tools/research/web_experience.py         # 网页 → 疑问

# 母题 → 问题树
python tools/core/run_paths.py problem --input motif --m "质数"

# 反例驱动（只提机器答不出的问题）
python -m ask_dao_machine.engine_counterexample

# 全领域并行扫描
python tools/engines/all_domains_engine.py
```

### 想象路

```bash
# 词 → 五步：组词 → 拆词 → 还原造句 → 成段 → 解释
python tools/core/run_paths.py imagine --word 记忆调性 --depth 3

# 或逐步
python tools/engines/word_fusion.py            # ① 组词（6642 组合）
python tools/research/depth_sentence.py         # ② 拆词（深度 d）
python tools/research/reconstruct_compare.py    # ③④ 还原造句 + 成段
python tools/research/understand_deep.py        # ⑤ 解释
```

## 第四次：接 AI4S

```bash
python tools/research/ai4s_harness.py
```

对问题清单里的候选项做**独立验证**，产出裁决：

```
Q_b4  [confirmed(例外汇合: [35,255,515,1855,4345], N0->N1 无新)]
Q_b5  [confirmed(例外汇合: [66,418,448,1266], N0->N1 无新)]
Q_b2  [rejected(出现新例外 [5000001, 5000003, ...])]
```

## 建 OEIS 索引（可选，用于新颖性门）

```bash
curl -o data/stripped.gz https://oeis.org/stripped.gz
python tools/core/oeis_index.py     # 建倒排索引（~5 秒）
python tools/core/novelty_gate.py   # 自检
```

## 常见问题

**Q: `[novelty]` 显示"不可判"是什么意思？**
A: 该问题没有机器可判的数据（如定性问题、无整数序列），因此**无法过门**。
这是诚实的"无法判定"，不是"已排除"。

**Q: N3 是什么？为什么一直是 0？**
A: N3 = 强候选（机器真判 + OEIS 未见 + 结构不可推 + 有显著性证书）。
至今 0 是**实测结论**，不是判据缺陷（早期 N3 恒为 0 才是判据缺陷，已修）。

**Q: 想象路需要验证"有没有真实所指"吗？**
A: **不需要，也不允许**。想象路的标准是**解释**（语法正确 + 逻辑通畅），
用问题路的逻辑评判它是范畴错误。
