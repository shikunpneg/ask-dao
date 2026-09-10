# 问题路手册

> 目的：把"困惑"变成**精确可判的问题**，交 AI4S 求解。
> 成功标准：**答案成立 / 可判**。

---

## 三种输入

### 1. 外部信息

| 类型 | 工具 | 说明 |
|---|---|---|
| 视觉 | `tools/perception_module.py` | 图像 → 结构特征（密度/对称/局部熵/边界密度）→ 触发模板 → 日常问题 |
| 网页文本 | `tools/web_experience.py` | 抓页 → 疑问句抽取 → 日常问题 |
| arXiv | `tools/arxiv_miner.py` | 摘要 → 开放点信号（open / unresolved / challenging） |

```bash
python tools/web_experience.py
python tools/arxiv_miner.py
python tools/perception_module.py
```

### 2. 日常问题

"为什么X？""X有多少？""什么是X？" → 分类 + 映射判定路由。

```bash
python tools/run_paths.py problem --input daily --q "为什么黑洞会蒸发?"
```

输出：
```
类型: 机制/因果   路由: 机制建模
科学问题: 驱动'黑洞蒸发'的机制是什么？能否用可检验模型刻画？
```

支持 5 类疑问 → 判定路由：

| 疑问类型 | 典型问法 | 判定路由 |
|---|---|---|
| 数量/边界 | 有多少？多大？ | 统计 / 枚举 |
| 机制/因果 | 为什么？ | 机制建模 / 实验 |
| 定义/本质 | 什么是？ | 概念分析 / 形式化 |
| 存在性/可行性 | 能否？是否存在？ | 构造 / 验证 |
| 真伪判断 | 是否？ | 判定 / 实验 |

### 3. 母题

```bash
python tools/run_paths.py problem --input motif --m "质数"
```

---

## 核心技术

### 反例驱动（机器的甜区）

> 发现（第一猜想）不可程序化；**反例 → 新问题 可程序化**。

`counterex_engine.py`：算**完整反例集** → 结构拟合 → **诚实延伸探针** → 产出
`status = 开放(机器无法结算)` 的问题。

```bash
python -m ask_dao_machine.counterex_engine
```

关键设计：**本引擎只提它自己答不出的问题**。其他引擎先算判定再写陈述
（陈述与判定同生），产出的是"计算"；本引擎把反例集的**结构**变成问题，
而机器无法结算这些问题。

### 问题树（L0–L5 分层）

| 层 | 问法 | 机器能做什么 |
|---|---|---|
| L0 计数 | 有多少？ | 直接算（**是计算，不是问题**） |
| L1 刻画 | 充要条件是什么？ | 枚举样本，给不出充要条件 |
| L2 渐近 | 增长率/极限/密度？ | 看趋势、拟合 |
| L3 机制 | 为什么是这个结构？ | 无因果模型 |
| L4 规范 | 哪些是禁忌？ | 判不了 |
| L5 反事实 | 实际中哪些从不出现？ | 需外部数据 |

**层间生成规则**（可机械执行）：
```
L0→L1: 有多少 → 哪些(充要刻画)
L1→L2: 哪些 → 极限/密度
L2→L3: 极限? → 为什么是这个极限
L3→L4: 为什么 → 该不该
L4→L5: 该不该 → 实际怎样
```

**⇒ 造新问题 = 从已解决的层，沿深度轴下移一格。**

```bash
python -m ask_dao_machine.counterex_engine     # 反例驱动
python -m ask_dao_machine.territories.digit_base
```

### 领域融合

- **局部融合**（操作子 × 结构）：`deep_fusion.py`
  例：伊辛模型 × 图 → 基态简并度（阻挫指数）
- **领域级融合**：`field_fusion.py`，含**结构桥梁**判据
  （对象携带的结构 ∩ 方法作用的结构 ≠ ∅，否则是空洞笛卡尔积）

```bash
python tools/deep_fusion.py
python tools/field_fusion.py
```

### 新颖性门

四道真门，全部实际执行：

```
G1 机器真判 → G2 OEIS 实查 → G3 结构可推性 → G4 分级
```

- **G2**：用本地倒排索引（393,600 序列）实查，带偏移对齐
- **G3**：检验序列是否可由已知结构推出（线性递推 / 低阶多项式 / 已知变换后命中 OEIS / 平凡序列）
- **G3.5 构造伪影检测**：单调序列判为"运行极值"伪影
- **G3.6 显著性证书**：要求"具名对象的不变量 + 在 ≥2 个任意选择扰动下保持"
- **G4**：分级 N0（已知）/ N1（可推）/ N2（检索未见）/ **N3（强候选）**

> **N3 路径已证明可达**（早期"N3 永远为 0"是结构性假象：裁判代码没有任何路径返回 N3）。

```bash
python tools/novelty_gate.py        # 需先下载 OEIS stripped 到 data/
python tools/oeis_index.py          # 建索引
```

---

## 完整流程

```bash
# 1. 全引擎 + 可视化 + 新颖性门
python -m ask_dao_machine all --out out/demo

# 2. 统一入口
python tools/run_paths.py problem --input daily --q "..."
python tools/run_paths.py problem --input text  --src <文件>
python tools/run_paths.py problem --input motif --m "..."

# 3. 全领域并行扫描
python tools/all_domains_engine.py

# 4. 交 AI4S 执行
python tools/ai4s_harness.py
```

---

## 产出格式

问题清单 `out/demo/discovery_manifest.json`，每条：

```json
{
  "id": "Q_b5",
  "domain": "数论(进制依赖)",
  "statement": "每个 n 是否都可写成 回文数(base 5) + 素数?",
  "conjecture": "猜想: 例外集有限且 = [66, 418, 448, 1266]",
  "evidence": {"scan_to": 5000000, "exceptions": [...], "count": 4},
  "judge_route": "数值枚举到 N(向量化标记)",
  "status": "疑似有限(最后例外后全覆盖)",
  "layer": "L0/L2"
}
```

**判定路由是关键**——AI4S harness 据此知道怎么验证。
