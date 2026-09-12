<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/logo_white.png">
  <img src="assets/logo.png" width="180" alt="道">
</picture>

# 问道 · ask-dao-machine

**道生一，一生二，二生三，三生万物**

不是问答机，也不是单纯的问题制造机 —— 它是一台**知识发现机器**

[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-v0.5.0-orange.svg)](CHANGELOG.md)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blueviolet.svg)](https://shikunpneg.github.io/ask-dao-machine/)
[![Stdlib](https://img.shields.io/badge/deps-纯标准库-brightgreen.svg)](#快速开始)

</div>

---

## 📖 目录

- [项目目的：发现新知识](#项目目的发现新知识)
- [什么是新知识](#什么是新知识)
- [系统架构：两条路](#系统架构两条路)
- [问题生成树](#问题生成树)
- [可视化：问题树与概念树](#可视化问题树与概念树)
- [结果与证据](#结果与证据)
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

| | 问题路 · Problem Path | 想象路 · Imagination Path |
|---|---|---|
| **产出** | 问题 | 概念 |
| **需要** | **解决** | **解释** |
| **成功标准** | 答案成立 / 可判 | 语法正确 + 逻辑通畅 + 有推理判断 |
| **输入** | 外部信息 · 日常问题 · 母题 | 词 |

两条路**互相独立**。想象路造出的概念**不是拿来"解决"的**，而是拿来**"理解"**的——
用问题路的逻辑（"这有真实所指吗""这新吗"）去评判想象路的概念，是范畴错误。


两条路**可以各自单独跑，也可以选择过桥**。经验桥（`ask-dao-machine bridge <词A> <词B>`）
把组合词接到现实经验上：中文维基双通道（词条通道：a 的词条里是否提到 b；搜索通道：组合词是否已成词）
+ arXiv 回退 → **经验锚点**写进概念理解。它只提供**脚手架**，不做裁判：
过桥不改变任何判定，检索失败即退化为无锚点，概念照常成立。
已跑：6,642 个组合词 · 词条通道命中 558（8.4%）· 维基已有独立条目 37（0.6%）· 经验锚点 7 处。

---

## 什么是新知识

我们反复重定义过"新"。最终确立**三层问题发现模式**和**两种新知识产生方式**：

| 三层问题发现模式 | 是什么 | 机器能做到 |
|---|---|---|
| **K1 提出问题** | 把困惑改造成**精确可判**的问题 | ok |
| **K2 推进解答** | 对旧问题给出更强证据 / 更大边界 | ok |
| **K3 归纳理论** | 从数据归纳出可验证的普遍律 |  部分 |

| 两种新知识产生方式 | 说明 |
|---|---|
| **① 提出新问题** | 爱因斯坦的追光思想实验不是解答，是问题——但它改变了物理 |
| **② 旧问题的新解答** | `回文数+素数` 从 10⁶ 推到 **10⁸ 零例外**——这是新知识 |

> 早期只用"K3 且人类未知"（N3）当唯一及格线，于是把 K1/K2 的实际产出当成"不够格"。这是错的。

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

![系统架构](assets/architecture.svg)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  问题路 (Problem Path)  ——  产问题，需解决                                  │
│                                                                          │
│   输入: 外部信息(视觉/听觉/文本) │ 日常问题 │ 母题                           │
│   流水: 日常问题 → 前问题 → 科学问题 → 基础领域 → 问题树 → 领域融合           │
│   出口: 可判问题清单(带判定路由) → AI4S 执行模块                             │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↑ （经验桥）
┌──────────────────────────────────────────────────────────────────────────┐
│  想象路 (Imagination Path)  ——  产概念，需解释                              │
│                                                                          │
│   输入: 词                                                                │
│   流水: 组词 → 拆词(深度d) → 还原造句(嵌套/推理/判断/比较) → 成段 → 解释      │
│   出口: 被理解的概念 / 理论                                                │
│   原则: 每个词都有意义，只不过是我们缺少想象力，无法理解它。                   │
└──────────────────────────────────────────────────────────────────────────┘
```

### 输入 → 输出（按代码核对）

| 输入 | 入口 | 产出 |
|---|---|---|
| 经验（图像） | `python -m ask_dao_machine perceive 图片/` | 结构特征 → 带判定路由的视觉问题 |
| 日常问题 | `python tools/run_paths.py problem --input daily --q "…"` | 判定路由 → 科学问题 |
| 已知未解 | `python tools/scihist_to_problems.py` · `problem_lineage.py` | 正式问题 + 谱系（前问题/后代/侧枝） |
| 母题（86 个） | `python -m ask_dao_machine all` | 问题树：母题 → 前问题 → 科学问题 → 基础领域 → 问题树 L0–L5 → 领域融合 |
| 造词 | `python tools/run_paths.py imagine --word 记忆调性` | 概念（组词 → 拆词(d) → 还原造句 → 成段 → 解释） |
| 论文 / 语料 | `python -m ask_dao_machine paper papers/` | 问题清单（「作者已提出」与「机器新提出」分开标注） |

**输出**：① 问题清单（`problems_*.json` / `discovery_manifest.json`，主产物）
② 概念/理论草稿（`word_*.json` / `sentence_batch.json`）
③ 判定结果与证据推进（`harness_verdicts.json` / `novelty_report.json`）
④ 报告与可视化（`REPORT.md` / `docs/viz/paths.html`）。

> **未来尝试的反向：多模态实体提取**——不是「信息 → 疑问」，而是反过来从图像/声音里
> 直接抽出实体（对象 / 关系 / 量）当两条路的入口。**尚未实现**：现在只有 `perceive`
> 这条「图像 → 结构特征」的最小闭环。

> **论文是输入，不是输出**——机器不写论文。且世界新问题（N3）至今为 0：
> 输出的是**候选问题**与**证据边界推进**，不是"已确认的新知识"。

### 关键引擎

| 引擎 | 作用 | 纪律 |
|---|---|---|
| `counterex_engine` | 反例驱动：从例外集长出机器**答不出**的问题 | 只提机器结算不了的问题 |
| `territory_engine` | 问题树 L0–L5 分层 + 谱系门 | 每爬一层必须机器实测 |
| `novelty_gate` | 四道真门：机器真判 → OEIS 实查 → 结构可推性 → 显著性证书 | N3 路径已证明可达 |
| `all_domains_engine` | 14 领域 × 14 进程并行扫描 | 全领域覆盖 |
| `field_fusion` | 领域级融合（含**结构桥梁**判据） | 无共享结构的配对是空洞笛卡尔积 |

---

## 问题生成树

![问题生成树](assets/problem_tree.svg)

**母题**通过组合模板生长为**问题树**，树与树在结构桥梁处交叉融合 → 新问题。
问题路分五步（`territory_engine`）：**母题 → 前问题 → 科学问题 → 基础领域 → 问题树 → 领域融合**，
每一步都必须机器实测，不许空转。

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
| **二、问题树** | 260+ 条问题，按 23 个领域分组，每条带**判定路由**与状态徽章 |
| **三、概念树** | 9 个概念按**深度 d** 拆解到原子概念（如"记忆调性"→ 过去/影响/现在/主音/音级/偏离/回归） |
| **四、概念论证** | 定义 → **据此可以推断** → **但必须区分** → 因此 |

> 范例（概念论证）：
> **记忆调性**，若是一个真实概念，指的是：记忆不是平铺的档案，而是围绕某些"主音"组织。
> **据此可以推断**：失忆不是记忆的"丢失"，而是记忆的"调性崩溃"。
> **更进一步**：记忆有调性，恰恰保证了人类能更高效地分配精力。
> **但必须区分**：失忆症是一种疾病，而记忆调性是正常现象——正如"心律失常"是病，"心跳有节律"是正常。
> **因此**，记忆调性回答"正常记忆如何组织"，失忆症回答"组织被摧毁时发生什么"。

---

## 结果与证据

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

### 五、经验检索桥：想象路接上现实经验

想象路原本只吃「词」。桥的作用是给组合词接一个**可核对的现实接口**——
现实中这两件事有没有被放在一起说过——但**只做脚手架，不做裁判**。

| 工具 | 作用 |
|---|---|
| `tools/fetch_wiki.py` | 抓词库 82 词的中文维基词条正文 → `data/wiki/{term}.json`（断点续跑，失败记 `_failed.json`） |
| `tools/retrieve_browser.py` | 双通道检索：**词条通道**（a 的词条里是否提到 b → 经验锚点）· **搜索通道**（组合词 a×b 在维基是否已成词） |
| `tools/retrieve_context.py` | arXiv API 回退（`all:a AND all:b` 摘要片段）；网络失败 → 空 hits，不崩 |
| `tools/browser_mass_search.py` | 全量跑 82 词两两组合的双通道检索，断点续跑 → `out/demo/browser_mass_search.json` |
| `tools/word_understand.py` | `understand(a,b,da,db,context=None)`：非空时把检索到的真实机制写成 **M7 经验锚点** |

**跑出来的真实数字**（6,642 个组合词，本次跑批）：

| 项 | 数字 | 说明 |
|---|---|---|
| 组合词总数 | **6,642** | 词库 82 词两两组合 |
| 词条通道命中 | **558（8.4%）** | a 或 b 的维基词条里提到了对方 —— 现实中确有联系 |
| 搜索通道：已成词 | **37（0.6%）** | 组合词本身在维基已有独立条目 |
| 维基搜索命中（中位 / 最大） | 381 / 48,287 | ≥1000 条的有 2,023 个；0 条的 **0 个** |
| 语料规模 | **49 词条** | `data/wiki/`（82 词中已抓 49），平均 9.1 段/词 |
| 经验锚点已写入 | **7 处** | 维基·公理系统 / 熵 ×2 / 意识 / 记忆 / 责任 / 正义（当前只对 9 个重点组合检索，`RETRIEVE_ALL=1` 全量） |

**纪律**（写进代码与网页，不只是口号）：只检索、不做价值判断；检索到的机制用来支撑理解，
不改变「概念不需要真实所指」；桥失败时退化为无锚点，想象路照常走。
可判性留给问题路——桥**不**判定概念真伪。

📋 [结果与证据（含负结果与 12 次自纠错）→](docs/guide/results.md)

---

## 快速开始

```bash
git clone https://github.com/shikunpneg/ask-dao-machine && cd ask-dao-machine
pip install -e .               # 只要 Python 3.9+，核心零依赖
export PYTHONPATH=src          # Windows PowerShell: $env:PYTHONPATH='src'
```

装好后命令行是 `ask-dao-machine`（等价 `python -m ask_dao_machine`）。**直接敲它**，看到的是「道」的徽标与命令速查：

```bash
$ ask-dao-machine        # 进去就知道机器开着（徽标 + 速查；TTY 才上色）
```

![进入时的徽标与命令速查](docs/assets/cli-banner.png)

### 真实使用（生物医学）：一次运行的完整回放

不是示例，是**实际跑过的命令与输出**。输入是一篇开放获取论文
（[PMC13331974](https://europepmc.org/article/PMC/PMC13331974)，J Nutr Health Aging，CC BY 4.0；
UK Biobank 前瞻队列 n=156,000，中位随访 13.3 年，调整后 HR 1.19）。

```bash
# 1. 找一篇开放获取论文并抓全文（Europe PMC 公开接口，记录许可字段）
python tools/fetch_biomed_paper.py --list
python tools/fetch_biomed_paper.py --pmcid PMC13331974

# 2. 生成问题（--domain biomed：11 类方法学追问 + 从 HR/CI 直接算 E-value）
ask-dao-machine paper papers/biomed/PMC13331974.md --domain biomed --out out/biomed_demo

# 3. 一页人话报告
ask-dao-machine report --out out/biomed_demo

# 4. 只看机器真正算出来的数
python -c "import json;d=json.load(open('out/biomed_demo/problems_paper.json',encoding='utf-8'));[print(p['id'],p['computed']['effect_type'],p['computed']['point'],'-> E =',p['computed']['evalue_point']) for p in d['problems'] if p.get('computed')]"
```

![真实终端：抓开放获取全文](docs/assets/real-use/t1-fetch.png)

![真实终端：生成问题 + 一页人话报告](docs/assets/real-use/t2-run.png)

![真实终端：逐条查看（3 条机器算出的 E-value + 11 类方法学追问的证据句）](docs/assets/real-use/t3-items.png)

![产物本身：out/biomed_demo/REPORT.md](docs/assets/real-use/t4-report.png)

54 条产出里，**32 条是生物医学方法学追问**，其中 3 条是**真算数**（残余混杂门槛）：

| 论文报告 | 机器算出 | 含义 |
|---|---|---|
| HR 1.19 (95% CI 1.08–1.30) | 残余混杂门槛 **E=1.67**（按 CI 下界 1.37） | 未测混杂要与暴露、结局**各自**达到 RR≈1.67 才能把效应解释为零 |
| HR 1.02 (95% CI 1.01–1.04) | 残余混杂门槛 **E=1.16** | 替代分析那一条**最脆**：几乎任何微弱混杂都能解释掉 |
| HR 1.49 (95% CI 1.28–1.74) | 残余混杂门槛 **E=2.34** | 最高风险组更难被混杂解释 |

诚实标注：32 条里 **23 条的主题作者已在文中论及**（机器只贡献"写成可判形式"），
**9 条的主题文中未见**（E-value、效应量 vs 决策阈值、人群外推边界）；两种都不主张"机器首先提出"。
逐条说明与「这个演示**不**证明什么」见 `docs/guide/demo-biomed.md`。

### 子命令

**统一入口是 `run`**：给它一个输入，选走哪条路，选到哪一站停。

| 命令 | 输入 → 输出 |
|---|---|
| `ask-dao-machine <回车>` | **进来看徽标 + 速查**（含 `run` 的用法块；`NO_COLOR=1` 关闭颜色） |
| **`ask-dao-machine run <论文/图片>`** | **统一入口**：一个输入 → **选路** `--path problem\|imagination\|both` → **选终止点** `--stop prequestion\|scientific\|domain\|tree\|ai4s` |
| **`ask-dao-machine run --words 熵,记忆 [--bridge]`** | 想象路：**任意词都行**——词表外的词会自动解析「本质」，也可 `--essence 折叠="多肽链自发形成三维构象"` 自己指定；`--bridge` 过经验桥 |
| `ask-dao-machine run --list` | 看跑过哪些产物、在哪、接报告的命令 |
| `ask-dao-machine paper <文件/目录> [--domain auto\|biomed\|none]` | 论文/语料 → 问题清单（「作者已提出」与「机器新提出」分开标注）；**按论文标题建目录**，同标题重跑递增 `-v2`/`-v3` 不覆盖 |
| `ask-dao-machine ask "<疑问>" [--stop tree]` | 疑问 → **走问题路五站**（类型判定 + 判定路由 + 结构追问 + 分层），与论文同一条流水线 |
| `ask-dao-machine imagine <任意词> [--depth d] [--bridge]` | 造词 → 概念（五步；`--bridge` 过经验桥） |
| `ask-dao-machine bridge <词A> <词B>` | 经验桥（可选）：维基双通道 + arXiv 回退 → 经验锚点（只检索，不判真伪） |
| `ask-dao-machine perceive <图片/目录>` | 图像（经验）→ 结构特征 → 带判定路由的问题 |
| `ask-dao-machine all` | 86 母题 → 问题树 L0–L5 → 领域融合（+ 新颖性门） |
| `ask-dao-machine report --out DIR` | 把一次跑批汇总成一页人话 `REPORT.md` |
| `ask-dao-machine doctor` / `data fetch` | 环境自查 / 取 OEIS 参照系（约 32MB） |
| `ask-dao-machine mcp` | 以 **MCP server** 方式运行，供宿主挂载（见下节） |

**问题路五站的终止点**（`--stop`，每站都在上一站的产出上真实推进）：

| 终止点 | 到哪一步 |
|---|---|
| `prequestion` | 前问题：良构成问句，还没有判定方式 |
| `scientific` | 科学问题：加基础领域候选 + 判定路由（**默认**） |
| `domain` | 基础领域：明确归类并按领域分组 |
| `tree` | 问题树：分 L0–L5 并成族 |
| `ai4s` | 跑完 AI4S：算得出的给判定，**算不出的诚实标「机器无法结算」** |

**通用开关**（`run` / `ask` / `paper` 都支持）：

```bash
--depth shallow|normal|deep   # 每类机制产出 3 / 8 / 20 条；③结构追问套 2 / 4 / 4 问
--max-total N                 # 总条数硬上限（0 = 不限）
--json                        # 结果只走 stdout，人看的日志走 stderr → 可直接接管道
--quiet / -q                  # 少说话，只留结果路径
--out DIR                     # 输出根目录（也可用环境变量 ASK_DAO_OUT）
```

**输出根统一**：所有命令收敛到同一个根，子目录按功能分——

```
out/paper/   ← paper / run <论文>      （按论文标题建子目录，同标题递增版本）
out/ask/     ← ask / run --question    （按问句建子目录）
out/image/   ← run <图片> / perceive
out/words/   ← run --words … / imagine
```

### 挂到 Agent 宿主：Claude Code / DSH / Cursor / Codex

一份实现、三种挂法，**已实测**的是前三行：

| 宿主 | 挂法 | 一条命令 | 状态 |
|---|---|---|---|
| 任何 shell（**Claude Code**、Codex、CI） | CLI | `ask-dao-machine paper …` | ✅ 实测 |
| **Claude Code / Cursor / Continue** | MCP server（项目 `.mcp.json`） | `python tools/install_integrations.py` | ✅ 配置已生成 |
| **DSH** | 技能目录（`.dsh/skills/`） | 同上 | ✅ 本机热加载验证通过 |
| **DSH** | MCP client 插件行（`cordis.yml`） | 见 `install_integrations.py` 输出片段 | ⬜ 未在本机挂（片段已给全） |
| GitHub | Action | 论文进 `papers/` 推送即评论回问题 | ✅ 已跑通 |

```bash
python tools/install_integrations.py          # 项目级：CC + DSH 技能目录 + .mcp.json
python tools/install_integrations.py --user   # 用户级：~/.claude/skills · ~/.dsh/skills · ~/.agents/skills
python tools/install_integrations.py --check  # 只检查现状
```

技能源文件只有一份：`integrations/skill/SKILL.md`（写入各宿主目录后内容一致，`--check` 可验证）。
`ask-dao-machine mcp` 暴露 5 个工具：`ask_dao_limits`（诚实边界，先读）、`ask_dao_problem`、
`ask_dao_imagine`、`ask_dao_paper`、`ask_dao_perceive`；宿主侧工具名形如
`mcp__askdao__ask_dao_paper`（DSH 与 Claude Code 同款约定）。

### 全部命令

```bash
# ⓪ 统一入口：一个输入 → 选路 → 选终止点（新用户从这条开始）
ask-dao-machine run paper.pdf                          # 问题路，默认到「科学问题」
ask-dao-machine run paper.pdf --stop ai4s              # 一路跑到底
ask-dao-machine run paper.pdf --depth deep --max-total 60
ask-dao-machine run photo.png --stop tree              # 图像输入，自动识别
ask-dao-machine run --words 熵,记忆                    # 想象路：两两组合（任意词都行）
ask-dao-machine run --words 折叠 --essence '折叠="多肽链自发形成三维构象"'
ask-dao-machine run --words 熵,记忆 --bridge           # 想象路 + 过经验桥
ask-dao-machine run --list                             # 看跑过哪些、产物在哪
ask-dao-machine run paper.pdf --json                   # 机器可读：stdout 只出 JSON
```

```bash
# ① 全引擎 + 可视化 + 新颖性门
python -m ask_dao_machine all --out out/demo
```

```bash
# ② 问题路：你自己的疑问 → 走同一条五站流水线
ask-dao-machine ask "为什么有些蛋白质能自发折叠成特定形状，而另一些会聚沉?"
ask-dao-machine ask "为什么代糖没降低肾病风险?" --stop domain --max-total 6
#    问句不会被截断；领域判不出来时不会硬拼成「在通用中…」这种怪句
```

```bash
# ③ 想象路：词 → 五步（组词/拆词/还原造句/成段/解释）
ask-dao-machine imagine 记忆调性 --depth 3
ask-dao-machine imagine 熵选择 --bridge      # 选择过经验桥：先检索现实经验作脚手架
ask-dao-machine bridge 熵 选择               # 只看桥本身：经验锚点 + 是否已成词
```

```bash
# ④ 可视化：问题树 + 概念树 + 概念论证
python tools/build_paths_viz.py     # → docs/viz/paths.html

# ⑤ 输入论文 → 输出问题（支持 md/txt/pdf/docx/epub 或目录）
python -m ask_dao_machine paper papers/ --flat --out out/papers
#    单文件默认按论文标题建目录，同标题重跑递增 -v2/-v3（不覆盖别篇）；
#    目录输入用 --flat 平铺到 --out（CI 用法）
#    产出含两类标注：「作者已提出（作者自陈的开放点）」与「机器新提出」
#    GitHub 上：把论文放进 papers/ 推送即可，见 .github/workflows/paper-to-problems.yml

# ⑥ 一页人话汇总（跑完先看这个，不用自己翻 10 个 JSON）
python -m ask_dao_machine report --out out/demo   # → out/demo/REPORT.md

# ⑦ 参照系（新颖性门要用；约 32MB，来自 oeis.org）
python -m ask_dao_machine data fetch              # → data/stripped.gz
python -m ask_dao_machine doctor                  # 环境自查：缺什么、下一步做什么
```

跑完每条命令都会给「下一步可以：」提示，里面的命令可直接复制。

```bash
# 开发/测试（pytest 在 dev 附加依赖里）
pip install -e ".[dev]" && pytest -q
```

---

## 使用文档

| 手册 | 内容 |
|---|---|
| [**架构详解**](docs/guide/architecture.md) | 四模块 / 两条路 / 关键设计决策 |
| [**问题路手册**](docs/guide/problem-path.md) | 三种输入 / 反例驱动 / 问题树 L0–L5 / 新颖性门 |
| [**想象路手册**](docs/guide/imagination-path.md) | 五步流程 / 深度变量 d / 成段范例 / 常见误区 |
| [**什么算新知识**](docs/guide/new-knowledge.md) | 三层问题发现模式 / 两种新知识产生方式 / 显著性 |
| [**命令行**](docs/guide/cli.md) | 徽标与「道」怎么来的 / 全部命令 / 可复用的三条约定 |
| [**生物医学完整演示**](docs/guide/demo-biomed.md) | 真实论文 → 54 条问题 / 11 类方法学缺口 / E-value 真算数 |
| [**演示幻灯片**](docs/ppt/index.html) | 《问道知识发现系统在生物医学领域的发现》（14 页，OJO 墨纸风；PPTX / PDF 同目录） |
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

---

## 目录结构

```
ask-dao-machine/
├── assets/                     # logo（书法「道」）+ 架构图 + 问题生成树图
│   ├── logo.png                # 书法「道」logo
│   ├── architecture.svg        # 系统架构图
│   └── problem_tree.svg        # 问题生成树图
├── src/ask_dao_machine/        # 包：引擎 / 判定器 / 母题库 / 可视化 / CLI / MCP server
├── integrations/skill/         # 一份 SKILL.md，装进 Claude Code / DSH / agents 技能目录
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

6. **73% 的产出无法判定。**
   "不可判" ≠ "已排除"。

---

<div align="center">

**问道 · ask-dao-machine** v0.5.0 · MIT License

*道生一，一生二，二生三，三生万物*

</div>
