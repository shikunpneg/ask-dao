# -*- coding: utf-8 -*-
"""make_ledger.py — P4.5 novelty_ledger 台账: 汇总所有域问题集的裁判/状态分布 + R + 晋升,
每轮追加进 docs/novelty_ledger.md"""
import json
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DEMO = HERE / "out/demo"


def collect():
    rows = []
    for f in sorted(DEMO.glob("problems_*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        nc = {"N0": 0, "N1": 0, "N2": 0, "N3": 0, "无": 0}
        st = {"真": 0, "假": 0, "悬置": 0, "待实验": 0}
        for p in d.get("problems", []):
            v = (p.get("novelty_judge") or {}).get("verdict", "")
            k = v.split(" ")[0] if v else "无"
            nc[k] = nc.get(k, 0) + 1
            s = p.get("status", "")
            if s.startswith("真"):
                st["真"] += 1
            elif s.startswith("假"):
                st["假"] += 1
            elif s.startswith("悬置"):
                st["悬置"] += 1
            else:
                st["待实验"] += 1
        rows.append((f.name, len(d.get("problems", [])), st, nc))
    r_count = None
    gpath = DEMO / "grown_motifs.json"
    if gpath.exists():
        g = json.loads(gpath.read_text(encoding="utf-8"))
        r_count = {"confirmed": sum(1 for x in g if x.get("stage") == "confirmed"),
                   "needs_extend": sum(1 for x in g if x.get("stage") == "needs_extend"),
                   "hypothesis": sum(1 for x in g if x.get("stage") == "hypothesis")}
    return rows, r_count


def append(entry_text):
    p = HERE / "docs" / "novelty_ledger.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text("# novelty_ledger\n\n", encoding="utf-8")
    with p.open("a", encoding="utf-8") as fh:
        fh.write(entry_text + "\n")


def main():
    rows, r_count = collect()
    lines = [f"## {datetime.now().isoformat(timespec='seconds')}"]
    for name, n, st, nc in rows:
        lines.append(f"- {name}: {n}题 | 状态{st} | 裁判{nc}")
    if r_count:
        lines.append(f"- grown_motifs: {r_count}")
    body = "\n".join(lines)
    append(body)
    print(body)
    return body


if __name__ == "__main__":
    main()
