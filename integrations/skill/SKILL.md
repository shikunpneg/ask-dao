---
name: ask-dao-machine
description: 'Use when the user wants questions rather than answers — turning a paper (especially biomedical/clinical), a daily puzzle, an image, or a made-up word into judgeable problems with explicit verification routes. Triggers: "这篇论文有什么没被提出的问题", "从这篇论文里找问题", "把这个问题变成科学问题", "给我造个新概念", "ask-dao", "问道", "paper-to-problems", biomedical follow-up questions, E-value / residual confounding bounds, 方法学追问.'
---

# 问道 · ask-dao-machine

一台**制造知识**的机器：输入论文 / 疑问 / 图像 / 自造词，输出**可被判定**的问题，而不是答案。
两条独立的路——**问题路**产问题（需解决）、**想象路**产概念（需解释）。

## 绝不违反的诚实边界（每条结果都要一起转述给用户）

1. **世界新问题（N3）至今 = 0 条。** 产出的是*候选问题*与*证据边界推进*，不是"已确认的新知识"。不要写成"发现了新问题"。
2. **"检索未见" ≠ "新"。** 参照系只有 OEIS + 检索；真正的文献门需要人/联网。
3. **论文支线里「作者已提出」的未解点不算机器新问题**，必须与「机器提出」分开标注（`is_author_stated`）。
4. **生物医学领域包的方法学追问不主张新**：它把文中一处方法学缺口写成可判形式；`author_touched: true` 表示作者已在局限/讨论中触及。
5. **E-value 是算术换算**（用 HR/OR 近似 RR，要求结局不常见），数值可复核，它是**门槛**不是发现。
6. 一条问题好不好，看它**能不能被判定**——`route` 字段给的就是判定方式。

## 怎么用（CLI 优先；宿主里也可挂 MCP）

```bash
pip install -e .                       # 只要 Python 3.9+，核心零依赖

# 论文 → 问题（生物医学领域包：方法学追问 + 机器算出的 E-value）
ask-dao-machine paper papers/biomed/PMC13331974.md --domain biomed --out out/biomed

# 日常疑问 → 类型 + 判定路由 + 科学问题
python tools/run_paths.py problem --input daily --q "为什么有些数学猜想几十年都没人证明出来？"

# 自造词 → 概念链（组词→拆词(d)→还原造句→成段→解释）
python tools/run_paths.py imagine --word 记忆调性 --depth 3

# 经验桥（可选）：组合词 → 维基双通道 + arXiv 回退 → 经验锚点
ask-dao-machine bridge 熵 选择

# 图像（经验）→ 结构特征 → 带判定路由的问题
ask-dao-machine perceive photos/ --out out/perceive

# 全领域跑批（母题 → 问题树 L0–L5 → 领域融合）
ask-dao-machine all

# 环境自查 / 取参照系
ask-dao-machine doctor
ask-dao-machine data fetch
```

产出固定落在 `--out` 目录：`problems_*.json`（机器可读，每条带 `route`）与 `REPORT.md`（一页人话）。

## 生物医学场景（最常用）

输入论文对应部分，输出**作者未提出的更进一步问题**。领域包（`--domain biomed`）找的是十类方法学缺口：
因果方向、残余混杂强度、剂量—反应形状、人群外推边界、效应量 vs 判定阈值、测量误差方向、
替代分析的反事实、交互尺度与多重比较、多重比较与假发现、机制的必要性/充分性。

其中「残余混杂强度」是**真算数**：从论文自报的 `HR/OR/RR (95% CI a–b)` 直接算 E-value 门槛，例如
`HR=1.19 (95% CI 1.08–1.30) → E=1.67（按 CI 下界 1.37）`，含义是：未测混杂必须与暴露、结局
各自达到 RR≈1.67 的关联，才能把该效应解释为零。**报这个数时务必带上近似前提。**

`--domain auto`（默认）按词表自动判断领域；`--domain none` 只用通用三机制
（①作者自陈未解 ②文本张力 ③结构追问）。

## 输出怎么读

| 字段 | 含义 |
|---|---|
| `type` | ①作者自陈未解 / ②文本张力 / ③结构追问 / ④方法学追问（领域包） |
| `is_author_stated` | `true` = 作者自己已经提出 → **不算机器新问题** |
| `author_touched` | 领域包专用：作者已在局限/讨论中触及该点 |
| `evidence` | 触发这条问题的**原文句子**（可核对，不要省略） |
| `route` | 判定方式；没有 route 的问题不产出 |
| `computed` | 机器算出的数值（目前是 E-value 及其前提） |
| `status` | `机器算出（数值可复核）` / `待实验/待数据` / `悬置(开放)` |

## 什么时候不要用它

- 用户要的是**答案/证明/诊断**，不是问题 → 直接回答或查文献。
- 需要**临床决策**（用药、诊断阈值）→ 这台机器只产问题，不产医嘱。
- 用户把输出当成"已确认的新发现" → 先纠正，再展示结果。

## 分工建议

产出问题后，把**最有价值的三条**连同 `evidence` 原文与 `route` 一起呈现；
其余给文件路径即可。不要在不知道 `route` 的情况下替用户判断哪条"更重要"。
