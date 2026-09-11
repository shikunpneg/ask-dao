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

（本 README 会被自动跳过，不会被当成论文。）
