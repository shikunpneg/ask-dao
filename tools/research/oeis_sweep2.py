# -*- coding: utf-8 -*-
"""tools/research/oeis_sweep2.py — 宽容匹配: 起始偏移 0..3, 6项前缀窗, 批量反查 12 个严格未命中项"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from ask_dao_machine import combo_engine as ce
from oeis_check import load_index

HERE = Path(__file__).resolve().parent.parent


def collect_queries():
    combo = json.loads((HERE / "out/demo/problems_combo.json").read_text(encoding="utf-8"))
    q = []
    for p in combo["problems"]:
        if p["honesty"].startswith("R:"):
            b = p["binds"]
            tpl = p["template"]
            if "禁子串" in tpl:
                seq = ce.counts_avoid_word(10, b["禁"])
            elif "最大游程" in tpl:
                seq = ce.counts_maxrun(10, 2, int(b["maxrun"]))
            elif "游走" in tpl:
                seq = ce.counts_walk(12, tuple(b.get("steps") or []))
            else:
                continue
            q.append((p["id"], seq))
    return q


def main():
    idx = load_index()
    queries = collect_queries()
    print("queries:", [x[0] for x in queries])
    # 6项窗 + 偏移0..3 -> 命中集
    key_to_q = {}
    for qi, (pid, seq) in enumerate(queries):
        w = tuple(seq[:6])
        key_to_q.setdefault(w, []).append(qi)
    hits = {qi: [] for qi in range(len(queries))}
    for a, terms in idx:
        for off in range(0, 4):
            if off + 6 > len(terms):
                break
            w = tuple(terms[off:off + 6])
            if w in key_to_q:
                for qi in key_to_q[w]:
                    hits[qi].append(a)
    print("== 宽容命中 ==")
    for qi, pid in enumerate([x[0] for x in queries]):
        if hits[qi]:
            print(" ", pid, "->", hits[qi][:5])
    print("== 宽容仍未见 ==")
    unseen = []
    for qi, (pid, seq) in enumerate(queries):
        if not hits[qi]:
            unseen.append((pid, seq[:6]))
            print(" ", pid, seq[:6])
    # 回写 combo json
    combo = json.loads((HERE / "out/demo/problems_combo.json").read_text(encoding="utf-8"))
    hitmap = {queries[qi][0]: hits[qi][:6] for qi in range(len(queries))}
    for p in combo["problems"]:
        if p["id"] in hitmap:
            p.setdefault("oeis", {})["lenient_ids"] = hitmap[p["id"]]
            p["oeis"]["lenient_unseen"] = not bool(hitmap[p["id"]])
    (HERE / "out/demo/problems_combo.json").write_text(
        json.dumps(combo, ensure_ascii=False, indent=1), encoding="utf-8")
    with (HERE / "docs/novelty_ledger.md").open("a", encoding="utf-8") as f:
        f.write(f"## OEIS 宽容匹配(偏移0..3, 6窗): 宽容未见 {len(unseen)} 项 -> {[u[0] for u in unseen]}\n")
    return unseen


if __name__ == "__main__":
    main()
