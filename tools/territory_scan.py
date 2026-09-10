# -*- coding: utf-8 -*-
"""tools/territory_scan.py — 领地稀疏度实测(LONG_PLAN_V2 Phase 1 的 DoD)

要回答的问题: "参照系稀薄的领地"到底怎么**测**? 不是感觉, 用三个可自动化的量:

  M1 例外稠密度   —— 猜想是否被否证(>5% => 坏问题, 诚实守卫)
  M2 幸存问题数   —— 过守卫、机器结算不了的问题数
  M3 文献沉默代理 —— 例外集的**累计计数序列**是否命中 OEIS。
                     命中 => 该例外集已被文献记录(非沉默); 未命中 => 沉默(代理)。
                     这是"文献门"唯一能自动化的部分, 其余仍需人/联网。

诚实: M3 是**代理**, 不是文献门。未命中 OEIS ≠ 未被文献问过(很多文献不入 OEIS)。
      但"命中率"作为领地间的**相对**比较是有效的。
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src"))
sys.path.insert(0, str(HERE / "tools"))

from oeis_index import OEISIndex              # noqa: E402
from ask_dao_machine.territories import TERRITORIES, CONTROL  # noqa: E402
from ask_dao_machine.territory_engine import run_territory    # noqa: E402

LO, HI = 4, 20000


def exception_count_seq(F, lo, hi, pts=14):
    """例外集的累计计数序列(在 lo..hi 上等距采样)。
    这是 OEIS 里常见的"计数函数"形状, 可用作'该集合是否被记录'的代理。"""
    fs = sorted(F)
    seq = []
    for i in range(1, pts + 1):
        x = lo + (hi - lo) * i // pts
        seq.append(sum(1 for v in fs if v <= x))
    return seq


def main():
    idx = OEISIndex.load()
    rows, all_recs = [], []
    print(f"领地稀疏度实测 (扫描 [{LO},{HI}])\n")
    print(f"{'领地':<16}{'族':<20}{'specs':>6}{'否证':>5}{'幸存问':>6}"
          f"{'沉默代理':>9}{'OEIS命中':>9}")
    print("-" * 76)
    for name in sorted(TERRITORIES):
        t = TERRITORIES[name]
        roots, recs, rep = run_territory(t, LO, HI)
        specs = rep["specs"]
        killed = sum(1 for r in specs if "否证" in r.get("verdict", ""))
        alive = [r for r in specs if "n" in r and r.get("n", 0) > 0
                 and "否证" not in r.get("verdict", "")]
        # M3: 对每个幸存 spec, 用例外累计计数序列反查 OEIS
        silent, hit = 0, 0
        for r in alive:
            # 重建该 spec 的例外集(引擎内部已算, 这里重算以便取序列)
            spec = next(s for s in t.specs() if s.id == r["spec"])
            F = [n for n in range(LO, HI + 1, spec.step) if not spec.holds(n)]
            if not F:
                continue
            seq = exception_count_seq(F, LO, HI)
            h = idx.lookup(seq, max_hits=3)
            strong = [x for x in h if x["matched"] >= min(6, len(seq))]
            if strong:
                hit += 1
                r["oeis_on_exc_seq"] = [x["a"] for x in strong]
            else:
                silent += 1
                r["oeis_on_exc_seq"] = []
        tot = silent + hit
        rate = f"{silent}/{tot}" if tot else "—"
        is_ctrl = " (对照)" if name in CONTROL else ""
        print(f"{name:<16}{t.family[:18]:<20}{len(specs):>6}{killed:>5}{len(recs):>6}"
              f"{rate:>9}{hit:>9}{is_ctrl}")
        rows.append({"territory": name, "family": t.family, "is_control": name in CONTROL,
                     "specs": len(specs), "killed": killed, "questions": len(recs),
                     "silent_proxy": silent, "oeis_hit": hit,
                     "spec_detail": specs})
        for r in specs:
            r["territory"] = name
        all_recs += specs

    cand = [r for r in rows if not r["is_control"]]
    print("\n== 结论 ==")
    for r in cand:
        tot = r["silent_proxy"] + r["oeis_hit"]
        print(f"  {r['territory']:<14} 幸存 {r['questions']:>2} 问 | "
              f"文献沉默代理 {r['silent_proxy']}/{tot}"
              + (" (全部命中 OEIS -> 已记录)" if r["oeis_hit"] and not r["silent_proxy"] else ""))
    for r in rows:
        if r["is_control"]:
            print(f"  {r['territory']:<14}(对照) 产出 {r['questions']} 问 / 否证 {r['killed']} "
                  f"-> {'守卫正常' if r['questions'] <= 2 else '⚠ 守卫可能失灵'}")

    print("\n诚实: '文献沉默代理'只查 OEIS 上的计数序列, **不是文献门**; "
          "未命中 OEIS ≠ 未被文献问过。它只用于领地间的相对比较。")
    (HERE / "out/demo/territory_scan.json").write_text(
        json.dumps({"rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已存 out/demo/territory_scan.json")


if __name__ == "__main__":
    main()
