# -*- coding: utf-8 -*-
"""tools/iterate.py — P4 迭代环 v1: combo 的 R/边界项 -> 子代(变异约束 + 扩界) -> 分类存活率
lineage: parent(combo id) -> children(变异约束, 扩界n)"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from ask_dao_machine import combo_engine as ce


def flip_words(w):
    out = []
    for i in range(len(w)):
        b = "0" if w[i] == "1" else "1"
        nw = w[:i] + b + w[i + 1:]
        if nw != w:
            out.append(nw)
    return out


def main(in_path="out/demo/problems_combo.json", out_path="out/demo/iteration_gen2.json",
         nmax_child=120):
    data = json.loads(Path(in_path).read_text(encoding="utf-8"))
    children = []
    parents = []
    for p in data["problems"]:
        if not p["honesty"].startswith("R:"):
            continue
        parents.append(p["id"])
        j = p["judgement"]
        m = p["binds"].get("method", p.get("template", ""))
        if p["template"] and "禁子串" in p["template"]:
            w = p["binds"].get("禁")
            for nw in flip_words(w)[:4]:
                c = ce.counts_avoid_word(nmax_child, nw)
                kind, seedname = ce.classify(c)
                children.append({
                    "parent": p["id"], "gen": 2, "op": f"变异禁子串 {w}->{nw}",
                    "kind": kind, "seed": seedname,
                    "tail_ratio": round(c[-1] / c[-2], 4) if c[-2] else None})
        elif p["template"] and "最大游程" in p["template"]:
            mr = int(p["binds"].get("maxrun", 3))
            for mr2 in (mr + 1, mr + 2):
                c = ce.counts_maxrun(nmax_child, 2, mr2)
                kind, seedname = ce.classify(c)
                children.append({
                    "parent": p["id"], "gen": 2, "op": f"扩maxrun {mr}->{mr2}",
                    "kind": kind, "seed": seedname,
                    "tail_ratio": round(c[-1] / c[-2], 4) if c[-2] else None})
    survive = sum(1 for ch in children if ch["kind"] == "R")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps({
        "note": "R项->子代(变异/扩界), kind=R 表示扩到nmax_child后仍不在本地种子表",
        "parents_count": len(parents), "children_count": len(children),
        "R_survive": survive,
        "children": children[:40]}, ensure_ascii=False, indent=1), encoding="utf-8")
    print({"parents": len(parents), "children": len(children),
           "R_survive_children": survive})


if __name__ == "__main__":
    main()
