# -*- coding: utf-8 -*-
"""修 tools_index.py：blurb 的取路径还在用根目录拼（文件已进子目录）。"""
from pathlib import Path

TI = Path(r"E:\ask-dao\ask-dao-machine\tools\tools_index.py")
t = TI.read_text(encoding="utf-8")

# 建一个 name -> 实际路径 的映射，替换掉所有 TOOLS / f"{n}.py"
old_head = 'live = sources()'
new_head = '''live = sources()

# 文件已按功能分到子目录，所以"按名字拼路径"是错的 ——
# 之前 blurb(TOOLS / f"{n}.py") 因此全部读不到，说明列退化成「—」。
PATH_OF: dict[str, Path] = {p.stem: p for p in files}
'''
if old_head in t and "PATH_OF" not in t:
    t = t.replace(old_head, new_head, 1)

t = t.replace('blurb(TOOLS / f"{n}.py")', 'blurb(PATH_OF.get(n, TOOLS / f"{n}.py"))')
t = t.replace("blurb(TOOLS / f'{n}.py')", "blurb(PATH_OF.get(n, TOOLS / f'{n}.py'))")
t = t.replace('        p = TOOLS / f"{n}.py"\n', '        p = PATH_OF.get(n, TOOLS / f"{n}.py")\n')

TI.write_text(t, encoding="utf-8")
print("已修：blurb 取路径改用 PATH_OF 映射")
print("剩余 'TOOLS / f\"{n}.py\"' 次数:", t.count('TOOLS / f"{n}.py"'))
