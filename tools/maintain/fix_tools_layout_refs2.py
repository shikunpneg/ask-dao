# -*- coding: utf-8 -*-
"""tools/ 分目录后，修「查找/导入 tools 模块」的逻辑（不是改文案）。

需要修的 4 类：
  A. src/pipeline_router.py 的 _load_tool()   —— 只找 tools/{name}.py
  B. src/interface_cli.py 里另有一处 sys.path.insert(..., "tools")
  C. src/interface_mcp.py 找仓库根时按 tools/run_paths.py 判断（现在在 tools/core/）
  D. 各 tool 脚本里的 _td = HERE / "tools"
sys.path.insert(0, str(_td))
for _sd in _td.iterdir():
    if _sd.is_dir() and not _sd.name.startswith("_"):
        sys.path.insert(0, str(_sd)) —— 要带上子目录
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"


def subdirs_expr(var: str = "HERE") -> str:
    return (f'for _d in (Path({var}) / "tools", *[d for d in (Path({var}) / "tools").iterdir()'
            f' if d.is_dir()]) if False else []:\n    pass')


# ── A. pipeline_router._load_tool ──────────────────────────────────
PR = ROOT / "src" / "ask_dao_machine" / "pipeline_router.py"
t = PR.read_text(encoding="utf-8")
old = '''    """从仓库 tools/ 里加载一个脚本模块（tools 不是包）。"""
    p = REPO / "tools" / f"{name}.py"
    if not p.exists():
        return None'''
new = '''    """从仓库 tools/ 里加载一个脚本模块（tools 不是包）。

    tools/ 已按功能分到子目录（core/ engines/ build/ maintain/ research/ archive/），
    所以要在根 + 各子目录里找。踩过的坑：原来只找 `tools/{name}.py`，
    分目录后全部找不到，而报错文案还误导（说文件不存在，其实只是换了目录）。
    """
    tdir = REPO / "tools"
    cands = [tdir / f"{name}.py"]
    if tdir.is_dir():
        cands += [d / f"{name}.py" for d in sorted(tdir.iterdir())
                  if d.is_dir() and not d.name.startswith("_")]
    p = next((c for c in cands if c.exists()), None)
    if p is None:
        return None'''
if old in t:
    t = t.replace(old, new)
    t = t.replace('    except Exception as e:                                     # noqa: BLE001\n'
                  '        print(f"[warn] 加载 tools/{name}.py 失败',
                  '    except Exception as e:                                     # noqa: BLE001\n'
                  '        print(f"[warn] 加载 {p.relative_to(REPO)} 失败')
    PR.write_text(t, encoding="utf-8")
    print("  ✓ A. pipeline_router._load_tool 已改为在根 + 子目录里找")
else:
    print("  · A. _load_tool 已是新版或结构不同，跳过")

# ── B/C/D. sys.path 与仓库根判断：统一换成"tools + 所有子目录"──
SUB_PATH_SNIPPET = (
    '{var} = str({base})\n'
    '    for _sd in [{var}] + [str(d) for d in Path({var}).iterdir() if d.is_dir()]:\n'
    '        if _sd not in sys.path:\n'
    '            sys.path.insert(0, _sd)'
)


def patch_syspath(p: Path) -> bool:
    try:
        t = p.read_text(encoding="utf-8")
    except Exception:
        return False
    orig = t
    # 形如 _td = HERE / "tools"
sys.path.insert(0, str(_td))
for _sd in _td.iterdir():
    if _sd.is_dir() and not _sd.name.startswith("_"):
        sys.path.insert(0, str(_sd))
    t = re.sub(
        r'sys\.path\.insert\(0,\s*str\((HERE|ROOT|REPO)\s*/\s*"tools"\)\)',
        lambda m: (f'_td = {m.group(1)} / "tools"\n'
                   f'sys.path.insert(0, str(_td))\n'
                   f'for _sd in _td.iterdir():\n'
                   f'    if _sd.is_dir() and not _sd.name.startswith("_"):\n'
                   f'        sys.path.insert(0, str(_sd))'),
        t)
    if t != orig:
        p.write_text(t, encoding="utf-8")
        return True
    return False


n = 0
for p in list(TOOLS.rglob("*.py")) + [ROOT / "src" / "ask_dao_machine" / "interface_cli.py",
                                      ROOT / "src" / "ask_dao_machine" / "interface_mcp.py"]:
    try:
        if patch_syspath(p):
            n += 1
            print(f"  ✓ sys.path 补子目录: {p.relative_to(ROOT)}")
    except Exception as e:                                   # noqa: BLE001
        print(f"  ✗ {p.name}: {e}")
print(f"  · B/C/D. sys.path 补了 {n} 个文件")

# interface_mcp 找仓库根的判据：tools/run_paths.py -> tools/core/run_paths.py
MCP = ROOT / "src" / "ask_dao_machine" / "interface_mcp.py"
t = MCP.read_text(encoding="utf-8")
t2 = t.replace('if (p / "tools" / "run_paths.py").exists():',
               'if (p / "tools" / "core" / "run_paths.py").exists() or '
               '(p / "tools" / "run_paths.py").exists():')
if t2 != t:
    MCP.write_text(t2, encoding="utf-8")
    print("  ✓ C. interface_mcp 找仓库根的判据已兼容新目录")

print("\n完成。接着跑 tools_index.py + 验证。")
