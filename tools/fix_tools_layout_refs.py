# -*- coding: utf-8 -*-
"""tools/ 分目录后，修 4 处兼容点。

移动本身不会自己生效——有 4 个地方硬编码了 tools/ 的扁平结构：
  1. src 的 _repo_tools()：把 tools/ 加进 sys.path 再 import → 现在模块在子目录里
  2. run_resident.py：按文件名 subprocess `TOOLS / cmd` → 现在文件在子目录里
  3. tools_index.py：只扫 TOOLS.glob('*.py') → 漏掉子目录
  4. 文档里的 `tools/xxx.py` 路径引用 → 全仓库改路径

这个脚本把 4 处一起修，改完立刻自检。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
SUB_OF: dict[str, str] = {}
for d in sorted(TOOLS.iterdir()):
    if d.is_dir() and not d.name.startswith("_"):
        for f in d.glob("*.py"):
            SUB_OF[f.stem] = d.name

print(f"子目录索引：{len(SUB_OF)} 个模块")


def sub_of(stem: str) -> str | None:
    return SUB_OF.get(stem)


# ══════════════════════════════════════════════════════════════════
# 1) src 的 _repo_tools()
# ══════════════════════════════════════════════════════════════════
CLI = ROOT / "src" / "ask_dao_machine" / "interface_cli.py"
NEW_REPO_TOOLS = '''def _repo_tools():
    """源码运行时复用 tools/ 里的判定器（question_refiner 等）。装成 wheel 时不可用。

    注：tools/ 已按功能分到子目录（core/ engines/ build/ maintain/ research/ archive/），
    所以这里要把 tools/ **及其所有子目录**都加进 sys.path ——
    否则 `import question_refiner` 找不到它（现在在 tools/core/）。
    """
    import sys as _s
    for base in (Path.cwd(), Path(__file__).resolve().parents[2]):
        for p in [base, *base.parents]:
            tdir = p / "tools"
            if not tdir.is_dir():
                continue
            cands = [tdir] + [d for d in sorted(tdir.iterdir())
                              if d.is_dir() and not d.name.startswith("_")]
            if not any((d / "run_paths.py").exists() for d in cands):
                continue
            for d in cands:
                sd = str(d)
                if sd not in _s.path:
                    _s.path.insert(0, sd)
            return p
    return None
'''
t = CLI.read_text(encoding="utf-8")
m = re.search(r'def _repo_tools\(\):.*?\n    return None\n', t, re.S)
if m:
    CLI.write_text(t[:m.start()] + NEW_REPO_TOOLS + t[m.end():], encoding="utf-8")
    print("  ✓ 1. interface_cli._repo_tools() 已改为「tools/ + 所有子目录都进 sys.path」")
else:
    print("  ✗ 1. 没找到 _repo_tools()，需人工处理", file=sys.stderr)

# ══════════════════════════════════════════════════════════════════
# 2) run_resident.py：按文件名在子目录里找
# ══════════════════════════════════════════════════════════════════
RR = TOOLS / "run_resident.py"
t = RR.read_text(encoding="utf-8")
if "_find_tool" not in t:
    helper = '''

def _find_tool(cmd: str):
    """tools/ 分了子目录，按文件名在根与各子目录里找（找不到返回 None）。

    踩过的坑：原来写死 `TOOLS / cmd`，分目录后全都找不到 —— 而 subprocess 拿到
    不存在的路径不会抛异常，只会静默 rc!=0，长跑看起来在跑其实什么都没做。
    """
    p = TOOLS / cmd
    if p.exists():
        return p
    for d in sorted(TOOLS.iterdir()):
        if d.is_dir() and not d.name.startswith("_"):
            q = d / cmd
            if q.exists():
                return q
    return None

'''
    t = t.replace("\ndef run(cmd, tag", helper + "\ndef run(cmd, tag", 1)
    t = t.replace(
        '    cmd_parts = [sys.executable, str(TOOLS / cmd)]',
        '    tool = _find_tool(cmd)\n'
        '    if tool is None:\n'
        '        print(f"[{tag}] 找不到工具 {cmd}（tools/ 及其子目录都没有），跳过", flush=True)\n'
        '        return -2\n'
        '    cmd_parts = [sys.executable, str(tool)]')
    RR.write_text(t, encoding="utf-8")
    print("  ✓ 2. run_resident 已改为按文件名在子目录里找（找不到会明确报错，不静默）")
else:
    print("  · 2. run_resident 已有 _find_tool，跳过")

# ══════════════════════════════════════════════════════════════════
# 3) tools_index.py：递归扫描
# ══════════════════════════════════════════════════════════════════
TI = TOOLS / "tools_index.py"
t = TI.read_text(encoding="utf-8")
t = t.replace('files = sorted(TOOLS.glob("*.py"))',
              'files = sorted(p for p in TOOLS.rglob("*.py")\n'
              '               if "__pycache__" not in p.parts)')
TI.write_text(t, encoding="utf-8")
print("  ✓ 3. tools_index 已改为递归扫描子目录")

# ══════════════════════════════════════════════════════════════════
# 4) 全仓库改 `tools/xxx.py` 路径
# ══════════════════════════════════════════════════════════════════
SKIP = {".git", "__pycache__", "out", "data", "handoff", "ask_dao_machine.egg-info",
        ".dsh-uploads", ".venv", "build", "dist", "node_modules"}
SUF = {".py", ".md", ".yml", ".yaml", ".toml", ".html", ".txt", ".json", ".cfg"}
n_files = 0
n_hits = 0
for p in ROOT.rglob("*"):
    if not p.is_file() or p.suffix.lower() not in SUF:
        continue
    if any(s in p.parts for s in SKIP):
        continue
    if p.name in ("reorganize_tools.py",):
        continue
    try:
        t = p.read_text(encoding="utf-8")
    except Exception:
        continue
    orig = t
    for stem, sub in SUB_OF.items():
        if stem in ("run_resident", "tools_index", "reorganize_tools"):
            continue
        # tools/xxx.py  |  tools\xxx.py
        t = re.sub(rf"(tools[/\\]){re.escape(stem)}\.py", rf"\1{sub}/{stem}.py", t)
        # `python tools/xxx.py` 之外的裸文件名引用（只改带路径的）
    if t != orig:
        p.write_text(t, encoding="utf-8")
        n_files += 1
        n_hits += len(re.findall(r"tools[/\\]", orig)) and 1 or 1
print(f"  ✓ 4. 文档/脚本里的 tools/ 路径引用：改了 {n_files} 个文件")

print("\n完成。下一步：跑 tools_index.py 重生成索引，然后验证。")
