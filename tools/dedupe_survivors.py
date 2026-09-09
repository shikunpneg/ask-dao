# -*- coding: utf-8 -*-
"""tools/dedupe_survivors.py — 258幸存去重(按 topic+双极唯一) 供 LLM 分级"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def main():
    surv = json.loads((HERE / "out/demo/method3_unified_shortlist.json").read_text(encoding="utf-8"))
    uniq = {}
    for s in surv:
        m = re.search(r"['\"]([^'\"]+)['\"].*?['\"]([^'\"]+)['\"]", s["statement"])
        key = (s["topic"], m.group(1) if m else s["statement"][:12])
        if key not in uniq or s["H"] > uniq[key]["H"]:
            uniq[key] = s
    us = sorted(uniq.values(), key=lambda x: -x["H"])
    out = HERE / "out/demo/method3_unique.json"
    out.write_text(json.dumps(us, ensure_ascii=False, indent=1), encoding="utf-8")
    print("去重后唯一候选:", len(us))
    for s in us[:24]:
        print(s["H"], "|", s["topic"], "|", s["statement"][:80])


if __name__ == "__main__":
    main()
