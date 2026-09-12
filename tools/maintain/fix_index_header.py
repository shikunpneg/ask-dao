# -*- coding: utf-8 -*-
"""给 tools/README.md 加一段「目录结构总览」（放在最前面，让人一眼看懂）。"""
from pathlib import Path

TI = Path(r"E:\ask-dao\ask-dao-machine\tools\tools_index.py")
t = TI.read_text(encoding="utf-8")

anchor = 'out = ["# tools/ —— 每个脚本是干什么的",'
if "目录结构总览" in t:
    print("已有总览，跳过")
else:
    new = '''DESC = {
    "core": "**产品依赖** —— 被 src/ask_dao_machine 调用，不能乱动",
    "engines": "**长跑链路** —— 被 run_resident.py 按文件名调用",
    "build": "**生成产物** —— 站点 / PPT / 架构图 / logo（手动入口）",
    "maintain": "**工程维护** —— 重构 / 修复 / 补抓语料 / 索引（手动入口）",
    "research": "**研究实验** —— 提问题 / 扫描 / 验证 / 度量（历史与在用的都在这里）",
    "archive": "**归档** —— 没有运行者的历史脚本（先别删，可能是证据链）",
    "site": "站点模板与数据（非 .py）",
}

out = ["# tools/ —— 每个脚本是干什么的",
       "",
       "> 本文件自动生成（`python tools/tools_index.py`）。改脚本后请重新生成。",
       "",
       "## 目录结构总览",
       "",
       "```",
       "tools/",
       "├── run_resident.py      常驻长跑总控（三链路轮转的入口）",
       "├── tools_index.py       本索引的生成器",
       "├── core/                产品依赖（被 src/ 调用）",
       "├── engines/             长跑链路引擎（被 run_resident 调用）",
       "├── build/               生成产物：站点 / PPT / 架构图 / logo",
       "├── maintain/            工程维护：重构 / 修复 / 补抓 / 索引",
       "├── research/            研究实验",
       "├── archive/             归档的历史脚本",
       "└── site/                站点模板与数据",
       "```",
       "",
       "| 目录 | 是什么 |",
       "|---|---|",
       ]
for _k in ("core", "engines", "build", "maintain", "research", "archive", "site"):
    _n = len([x for x in TOOLS.glob(f"{_k}/*.py")])
    out.append(f"| `{_k}/` | {DESC[_k]}{f'（{_n} 个脚本）' if _n else ''} |")
out += ["",
        "**怎么用**：想知道某个脚本干什么，直接在里面搜文件名；"
        "`research/` 里多数是当时的研究脚本，跑不跑得通取决于当时的产物还在不在。",
        ""]
'''
    t = t.replace(anchor, new + anchor, 1)
    TI.write_text(t, encoding="utf-8")
    print("已加目录结构总览")
