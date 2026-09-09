# -*- coding: utf-8 -*-
"""tools/oeis_sweep.py — 用离线 OEIS 索引反查 combo 全部 R 项 + 迭代子代,
输出 OEIS-level 未见清单(这才是真正值得 web/人工核的集合)。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from ask_dao_machine import combo_engine as ce
from oeis_check import load_index, lookup

HERE = Path(__file__).resolve().parent.parent


def main():
    idx = load_index()
    print("indexed:", len(idx))
    combo = json.loads((HERE / "out/demo/problems_combo.json").read_text(encoding="utf-8"))
    unseen, seen = [], []
    for p in combo["problems"]:
        if not p["honesty"].startswith("R:"):
            continue
        b = p["binds"]
        tpl = p["template"]
        try:
            if "禁子串" in tpl:
                seq = ce.counts_avoid_word(10, b["禁"])
            elif "最大游程" in tpl:
                seq = ce.counts_maxrun(10, 2, int(b["maxrun"]))
            elif "游走" in tpl or "步集" in tpl:
                steps = tuple(b.get("steps") or [])
                seq = ce.counts_walk(12, steps)
            else:
                continue
        except Exception as e:
            print("skip", p["id"], e)
            continue
        hits = lookup(seq, idx)
        p.setdefault("oeis", {})["ids"] = [h[0] for h in hits[:6]]
        if hits:
            seen.append((p["id"], p["statement"][:40], hits[0][0]))
        else:
            unseen.append((p["id"], p["statement"][:40]))
    (HERE / "out/demo/problems_combo.json").write_text(
        json.dumps(combo, ensure_ascii=False, indent=1), encoding="utf-8")
    print("== OEIS 命中 ==")
    for x in seen:
        print(" ", x)
    print("== OEIS 未命中(R 真实候选) ==")
    for x in unseen:
        print(" ", x)
    note = (f"- OEIS全量反查: 命中{len(seen)}, 未命中{len(unseen)} (未命中清单: {[u[0] for u in unseen]})\n")
    with (HERE / "docs/novelty_ledger.md").open("a", encoding="utf-8") as f:
        f.write("## OEIS sweep\n" + note)
    return unseen


if __name__ == "__main__":
    main()
