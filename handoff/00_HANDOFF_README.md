# 00 HANDOFF —— 交接说明（搬到 Claude Code 用）

> 目的：把本会话的全部上下文、提示词、实验记录、执行日志、代码与数据索引，整理成可移植交接包。
> 仓库：https://github.com/shikunpneg/ask-dao-machine

## 建议阅读顺序（Claude Code 里）
1. `01_PROMPTS.md` —— 用户历次指令原文（需求与口径的唯一权威）
2. `02_CONTEXT.md` —— 理论/口径/架构/指标/诚实结论/未决项
3. `docs/EXPERIMENT_RECORD.md` —— 从最初到现在的完整实验史（做了什么、数据、代码位置）
4. `docs/EXECUTION_LOG.md` —— 逐轮执行日志（R1–R22）
5. `03_NEXT_STEPS.md` —— 待办队列与整改项
6. `05_TOOLS_INDEX.md` —— 全部脚本/引擎用途索引
7. `docs/` 其余（MASTER_PLAN / LONG_PLAN / METHODOLOGY3 / BIG_PROBLEMS / MOTIF_DEFINITION / EXPLORATION_REPORT / novelty_ledger / human_review_sheet …）

## 环境与运行
```bash
git clone https://github.com/shikunpneg/ask-dao-machine
cd ask-dao-machine
# 纯标准库；PYTHONPATH=src 或 pip install -e .
export PYTHONPATH=src         # Windows: $env:PYTHONPATH='src'
python -m ask_dao_machine all --out out/demo     # 全引擎 + 可视化
python tools/oeis_check.py                       # 需先下载 OEIS stripped 到 data/stripped.gz
```
语料（不在仓库）：`E:\ask-dao\_text\`（中西哲学史、科学哲学手册8卷、译丛、科学史等，均 EPUB→md）

> R22 新增产物：`handoff/viz/tree.html`（母题树生长+树交叉可视化，单文件自包含）；
> 新工具 `s2_bounded` / `tri_verifiers` / `cross_md_v4` / `p_A5_yanyi` / `build_tree_viz`。

## 必须带走的纪律（否则会重蹈覆辙）
1. **状态只来自判定器**：真/假/悬置/待实验；不许用"似乎""可能"冒充判定。
2. **当务分必须证据依赖**（`tools/big_score_ev.py`）：关键词版会自灌水（已验证：21 候选关键词 6.5 → 证据门 0）。
3. **新颖性三层**：机器可真判 → OEIS/文献未见 → LLM/人工不排除；**N3 至今 = 0**，不许粉饰。
4. **自纠错优先**：历史上 5 次自纠（P4 判定、置换分母、X3 上界、偶 q 陷阱、阈值尾窗），每次自纠都让候选缩水，这才是对的。
5. **三域交叉必须真参与**（当前缺陷：名义三域，见 03）。
