# papers/ —— 把论文放这里

把论文（`.md` / `.txt` / `.pdf` / `.docx` / `.epub`）放进这个目录，推送到 GitHub 后，
**paper-to-problems** workflow 会自动：

1. 抽取文本（pdf 优先用 pypdf/pdftotext，都没有则用内置尽力提取——扫描件无效）；
2. 用三种机制生成问题：
   - **① 作者自陈未解**（抓 open problem / remains unclear / 尚不明确 …）—— **作者已经提出，不算新问题**
   - **② 文本张力**（然而 / 但是 / 矛盾 / conflicting / whereas …）→ 形式化追问 —— **作者未提出**
   - **③ 结构追问**（对所有/等价/单调/上界/收敛… 的结论句套四类追问：范围 / 反例 / 机制 / 定量）—— **作者未提出**
3. 产出 `problems_paper.json` 与 `REPORT.md`，作为构建产物上传；若是 PR，还会把问题清单评论在 PR 上。

本地跑同样的东西：

```bash
pip install -e .
python -m ask_dao_machine paper papers/ --out out/papers
python -m ask_dao_machine report --out out/papers
```

> 纪律：① 与 ②③ 在清单里**分开标注**。作者自己写下的"有待研究"不是新问题；
> 世界新问题（N3）至今为 0。

## 生物医学领域包（`--domain biomed`）

```bash
python -m ask_dao_machine paper papers/biomed/PMC13331974.md --domain biomed --out out/biomed_demo
```

在通用三机制之外，再加 **11 类方法学追问**（因果方向 / 残余混杂强度 / 剂量-反应形状 /
人群外推边界 / 效应量 vs 判定阈值 / 测量误差方向 / 替代分析的反事实 / 交互尺度 /
多重比较 / 机制必要性充分性），并能从论文自报的 `HR/OR/RR (95% CI)` **直接算出
E-value 残余混杂门槛**。完整演示见 [`docs/guide/demo-biomed.md`](../docs/guide/demo-biomed.md)。

- `--domain auto`（默认）：按词表自动判断是否套用领域包
- `--domain none`：只用通用三机制
- 领域包条目的 `author_touched` 字段表示**该主题作者已在文中论及**；这些条目不主张机器首先提出该主题。

## `papers/biomed/` 的版权

`papers/biomed/PMC13331974.{md,meta.json}` 是一篇**开放获取（CC BY 4.0）**论文的全文与元数据，
仅用于可复现演示，来源与许可见 `PMC13331974.meta.json`（含 PMCID / DOI / 抓取日期）。
重新抓取：`python tools/fetch_biomed_paper.py`。**未标 CC BY 的论文请勿放入本仓库。**

（本 README 会被自动跳过，不会被当成论文。）
