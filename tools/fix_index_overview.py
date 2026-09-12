# -*- coding: utf-8 -*-
"""最后一招：在写 README 那一步直接前置「目录结构总览」，不依赖列表拼接顺序。"""
from pathlib import Path

TI = Path(r"E:\ask-dao\ask-dao-machine\tools\tools_index.py")
t = TI.read_text(encoding="utf-8")

if "STRUCT_OVERVIEW" in t:
    print("已打过补丁，跳过")
else:
    patch = '''
STRUCT_OVERVIEW = """## 目录结构总览

```
tools/
├── run_resident.py      常驻长跑总控（三链路轮转的入口）
├── tools_index.py       本索引的生成器
├── core/                产品依赖（被 src/ask_dao_machine 调用）
├── engines/             长跑链路引擎（被 run_resident.py 调用）
├── build/               生成产物：站点 / PPT / 架构图 / logo（手动入口）
├── maintain/            工程维护：重构 / 修复 / 补抓语料 / 索引（手动入口）
├── research/            研究实验：提问题 / 扫描 / 验证 / 度量
├── archive/             归档：没有运行者的历史脚本（先别删，可能是证据链）
└── site/                站点模板与数据（非 .py）
```

**怎么找**：知道脚本名就搜文件名；不知道就按上表看它属于哪一类再翻。
`research/` 里多数是当时的研究脚本，能不能跑取决于当时的产物还在不在。
**怎么加**：新脚本请放进对应子目录 —— `core/`（产品要用）、`engines/`（长跑要用）、
`build/`（生成产物）、`maintain/`（工程维护）、`research/`（一次性研究）。
放完重跑 `python tools/tools_index.py`。

"""

'''
    t = t.replace('(TOOLS / "README.md").write_text("\\n".join(out), encoding="utf-8")',
                  patch + '(TOOLS / "README.md").write_text(\n'
                  '    STRUCT_OVERVIEW + "\\n".join(out), encoding="utf-8")', 1)
    TI.write_text(t, encoding="utf-8")
    print("已打补丁")
