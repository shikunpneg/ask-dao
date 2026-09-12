# -*- coding: utf-8 -*-
"""修复 alias 脚本的越界替换：把 `X as Y.method()` 还原成 `Y.method()`。

损坏成因：别名脚本的正则里用了 `\\s`（能匹配换行），把 `from . import _console`
之后的调用行也吞了进去，产出 `ui_console as _console.setup()` 这种语法错误。
形态完全统一（9 处），所以按字面精确还原即可，不做泛化替换。
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BAD = re.compile(r"\b(\w+) as (\w+)\.(\w+)\(\)")


def main():
    n = 0
    for p in sorted((ROOT / "src" / "ask_dao_machine").glob("*.py")):
        t = p.read_text(encoding="utf-8")
        t2, k = BAD.subn(lambda m: f"{m.group(2)}.{m.group(3)}()", t)
        if k:
            p.write_text(t2, encoding="utf-8")
            n += k
            print(f"  修 {p.name}  （{k} 处）")
    print(f"\n共修 {n} 处")
    # 复核：不应再有 `as X.` 形态
    left = []
    for p in sorted(ROOT.rglob("*.py")):
        if any(s in p.parts for s in (".git", "__pycache__", "out", "data", "handoff")):
            continue
        try:
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if re.search(r"\w+ as \w+\.", line):
                    left.append(f"{p.relative_to(ROOT)}:{i}  {line.strip()[:80]}")
        except Exception:
            continue
    print("残留:", left or "无")


if __name__ == "__main__":
    main()
