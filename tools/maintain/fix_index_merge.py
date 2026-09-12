# -*- coding: utf-8 -*-
"""修 tools_index.py：两处 out = [...]，后者覆盖前者 → 把总览并进去。"""
from pathlib import Path
import re

TI = Path(r"E:\ask-dao\ask-dao-machine\tools\tools_index.py")
t = TI.read_text(encoding="utf-8")

# 1) 把我插入的那块改名成 _overview，别用 out
t = t.replace('\nout = ["# tools/ —— 每个脚本是干什么的",\n       "",\n       "> 本文件自动生成（`python tools/tools_index.py`）。改脚本后请重新生成。",\n       "",\n       "## 目录结构总览",',
              '\n_overview = ["# tools/ —— 每个脚本是干什么的",\n       "",\n       "> 本文件自动生成（`python tools/tools_index.py`）。改脚本后请重新生成。",\n       "",\n       "## 目录结构总览",', 1)

# 2) 原列表改成 _overview + [...]，并去掉重复的标题三行
old = ('out = ["# tools/ —— 每个脚本是干什么的",\n'
       '       "",\n'
       '       "> 本文件自动生成（`python tools/tools_index.py`）。改脚本后请重新生成。",\n'
       '       "",\n'
       '       f"共 {len(names)} 个脚本。')
new = ('out = _overview + [\n'
       '       f"共 {len(names)} 个脚本。')
if old in t:
    t = t.replace(old, new, 1)
    print("  ✓ 已合并两个 out 列表")
else:
    print("  ! 未找到原列表，请人工看一眼")

TI.write_text(t, encoding="utf-8")
print("完成")
