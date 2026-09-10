---
title: AI4S 接口
---

# AI4S 接口

> 问题路产出的问题清单，交给 AI4S 执行模块求解。

---

## 为什么需要 AI4S

AI4S（AI for Science）生态已经很强：AlphaFold（蛋白折叠）、FunSearch（程序搜索）、
ChemCrow（化学工具链）、AI-scientist（自动论文）、DeepChem、RDKit…

**但它们都需要明确的输入问题。**

缺的是"**谁定义值得解的问题**"——这正是问题路的产出。

```
问题路（定义问题） → 问题清单（带判定路由） → AI4S（求解） → 裁决回灌
```

---

## 问题清单格式

`out/demo/discovery_manifest.json`：

```json
{
  "generator": "ask-dao-machine/discovery_pipeline",
  "target": "AI4S harness",
  "problem_format": "{statement, conjecture, evidence, judge_route, status, layer}",
  "count": 260,
  "problems": [
    {
      "id": "Q_b5",
      "domain": "数论(进制依赖)",
      "statement": "每个 n 是否都可写成 回文数(base 5) + 素数?",
      "conjecture": "例外集有限且 = [66, 418, 448, 1266]",
      "evidence": {"scan_to": 5000000, "count": 4, "last": 1266},
      "judge_route": "数值枚举到 N(向量化标记)",
      "status": "疑似有限(最后例外后全覆盖)",
      "layer": "L0/L2"
    }
  ]
}
```

**`judge_route` 是关键字段**——AI4S harness 据此知道怎么验证。

---

## 内置 harness（最小可跑版）

`tools/ai4s_harness.py`：对每条问题做**独立验证**（不同代码路径 + 更大 N），
产出裁决并回灌清单。

```bash
python tools/ai4s_harness.py
```

**裁决类型**：

| 裁决 | 含义 |
|---|---|
| `confirmed` | 例外汇合到同一集合，扩大 N 后无新例外 |
| `rejected` | 出现新例外（原主张被削弱） |
| `open` | 例外多 / 仍在冒 |

**实测结果**（15 条跨进制问题）：

```
confirmed 13  /  rejected 1 (base 2)  /  open 1 (base 3)
```

---

## 接入主流 AI4S 的方式

### 方式一：直接喂问题清单

把 `discovery_manifest.json` 里 `judge_route = "数值枚举"` 的问题，
交给能做数值/符号计算的 harness（FunSearch 风格最匹配数论问题）。

### 方式二：按问题类型路由

| 判定路由 | 适合的 harness 类型 |
|---|---|
| 数值枚举 | FunSearch / 程序搜索 |
| 定理证明 | 自动定理证明器（Lean/Coq 接口） |
| 实验设计 | AI-scientist 风格 |
| 仿真 | 领域模拟器 |

### 方式三：裁决回灌

AI4S 的求解结果写回 `problems[i].harness_verdict`，
问题路据此更新：

- 哪个问题被解决了
- 哪里的裂缝结论变化了
- 是否需要生成下游问题

---

## 闭环

```
问题路提出  →  AI4S 求解  →  裁决回灌  →  问题路更新
    ↑                                          │
    └──────────────────────────────────────────┘
```

**注意**：AI4S 求解的是**问题路**的问题。
**想象路的概念不交给 AI4S**——那是范畴错误（概念需要"解释"，不是"解决"）。
