# -*- coding: utf-8 -*-
"""tools/candidate_rank.py — Phase 3 (Axis S): 规模化 + 候选排序

排序的依据不是"新颖"(机器判不了), 而是**机器自己离答案有多远** —— 这是机器**能**诚实算的量:
  +2 机器**无法描述**例外集(无周期 / 无类库拟合 / 无小界) —— 机器连"它像什么"都说不出
  +1 例外稀疏(密度 < 0.5%) —— 是特殊对象而非"猜想本身假"
  +1 探针越界后仍见新例外 —— 不是小 n 假象
  +1 非十进制 / 非标准进制 —— 领地更稀疏(少人做)
  -1 机器已找到归约(置换不变) —— 更容易被解, 也更可能已有人解

诚实: 分高 **不等于新**。排序只回答"该先送哪几个去文献门", 不回答"是不是新的"。
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src"))
sys.path.insert(0, str(HERE / "tools"))

from ask_dao_machine.territories import TERRITORIES, CONTROL   # noqa: E402
from ask_dao_machine.territory_engine import run_territory      # noqa: E402

LO, HI = 4, 20000
CANON_BASES = {10}   # 标准进制(不算稀疏加成)


def score(spec_report, territory):
    s, why = 0, []
    kind = spec_report.get("kind", "")
    cf = spec_report.get("class_fit")
    sb = spec_report.get("small_bound")
    red = (spec_report.get("reductions") or {}).get("perm_invariance")
    dens = spec_report.get("density", 0.0)

    if kind and kind != "无例外(区间内)" and not cf and not sb and kind != "周期":
        s += 2
        why.append("机器无法描述例外集")
    if 0 < dens < 0.005:
        s += 1
        why.append(f"例外稀疏({dens:.3%})")
    if spec_report.get("probe_extends"):
        s += 1
        why.append(f"越界仍有新例外(+{spec_report.get('n_beyond')})")
    b = (spec_report.get("params") or {}).get("进制")
    if b and b not in CANON_BASES:
        s += 1
        why.append(f"非标准进制 b={b}")
    if red and red.get("invariant"):
        s -= 1
        why.append("机器已找到归约")
    return s, why


def main():
    rows, allq = [], []
    for name in sorted(TERRITORIES):
        if name in CONTROL:
            continue
        t = TERRITORIES[name]
        roots, recs, rep = run_territory(t, LO, HI)
        for r in rep["specs"]:
            if "n" not in r or r.get("n", 0) == 0 or "否证" in r.get("verdict", "") \
               or r.get("implied_by"):
                continue
            sc, why = score(r, t)
            rows.append({"territory": name, "spec": r["spec"], "claim": r["claim"],
                         "n": r["n"], "density": r.get("density"),
                         "kind": r.get("kind"), "score": sc, "why": why})
        allq += [{"id": p.id, "territory": name, "statement": p.statement}
                 for p in recs]

    rows.sort(key=lambda x: -x["score"])
    print(f"规模化后: 幸存 spec {len(rows)} 个 / 开放问题 {len(allq)} 个\n")
    print(f"{'分':>3}  {'领地':<12}{'spec':<24}{'例外':>6}{'密度':>9}  理由")
    print("-" * 96)
    for r in rows[:20]:
        print(f"{r['score']:>3}  {r['territory']:<12}{r['spec']:<24}{r['n']:>6}"
              f"{r['density']:>9.3%}  {'; '.join(r['why'])}")
    if len(rows) > 20:
        print(f"  … 其余 {len(rows)-20} 个(分数 ≤ {rows[20]['score']})")

    print("\n诚实: 分高 **不等于新** —— 排序只回答'该先送哪几个去文献门'。")
    (HERE / "out/demo/candidate_rank.json").write_text(
        json.dumps({"ranked": rows, "questions": allq}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print("已存 out/demo/candidate_rank.json")


if __name__ == "__main__":
    main()
