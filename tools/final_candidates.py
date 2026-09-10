# -*- coding: utf-8 -*-
"""tools/final_candidates.py — 把猜想生成器的幸存者过完整领地机器(Phase 3c)

输入: `out/demo/conjecture_search.json` 的 57 个幸存猜想
处理: 结构拟合(classify) -> 归约探针(reduction_probes) -> 排序(candidate_rank 同款打分)
输出: 排序后的最终候选清单, 供 Phase 4(人类/文献门)

诚实: 排序只回答"该先送哪几个去查文献", **不回答"是不是新的"**。
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src"))

from ask_dao_machine.territory_engine import (Spec, classify, reduction_probes)  # noqa: E402
from conjecture_search import build_pool, exceptions_fast, LO, HI                 # noqa: E402

CANON_BASES_HINT = ("_b10",)

MODS = (3, 4, 6, 8, 9, 12, 18, 24)


def quadratic_residues(m):
    return sorted({(a * a) % m for a in range(m)})


def augment_with_modular(pool, hi=HI, mods=MODS):
    """自纠错(第 11 次): 类库里原本**没有模类**, 于是机器把"≡2 mod 6"这种
    一眼可见的结构报成"无法描述"。补上模类, 让机器至少能试这些。
    例: Harshad数+三角数 的 38 个例外里 **36 个 ≡2 (mod 6)**(对照: 可表示的 n 模6 均匀)。"""
    out = dict(pool)
    for m in mods:
        for r in range(m):
            out[f"≡{r}(mod {m})"] = {n for n in range(1, hi + 1) if n % m == r}
        # 二次剩余类(自纠错第12次: Harshad+平方数 的例外恰好避开 mod 9 的 QR)
        qr = set(quadratic_residues(m))
        out[f"QR(mod {m})"] = {n for n in range(1, hi + 1) if n % m in qr}
    return out


def make_spec(a, b, F, lo, hi):
    Fs = set(F)

    def holds(n, _F=Fs):
        return n not in _F

    return Spec(id=f"{a}+{b}", claim=f"每个偶数 n 可写成 {a} + {b}",
                holds=holds, classes={}, params={"类A": a, "类B": b},
                step=2, quantity=f"偶数 n ∈ [{lo},{hi}]")


def score(r):
    s, why = 0, []
    if r["kind"] not in ("周期", "无例外(区间内)") and not r["class_fit"]             and not r.get("avoid_fit") and not r["small_bound"]:
        s += 2
        why.append("机器无法描述例外集")
    if 0 < r["density"] < 0.005:
        s += 1
        why.append(f"例外稀疏({r['density']:.3%})")
    if r["probe_extends"]:
        s += 1
        why.append(f"越界仍有新例外(+{r['n_beyond']})")
    if any(k in r["A"] + r["B"] for k in CANON_BASES_HINT):
        pass
    elif any("_b" in x for x in (r["A"], r["B"])):
        s += 1
        why.append("非标准进制")
    if r.get("reduction"):
        s -= 1
        why.append("机器已找到归约")
    return s, why


def main():
    src = HERE / "out/demo/conjecture_search.json"
    surv = json.loads(src.read_text(encoding="utf-8"))["survivors"]
    pool = augment_with_modular(build_pool())

    rows = []
    for r in surv:
        A, B = r["A"], r["B"]
        F = exceptions_fast(sorted(pool[A]), sorted(pool[B]), LO, HI)
        if len(F) != r["n"]:
            print(f"  [警告] {A}+{B} 例外数不一致 {len(F)} vs {r['n']}")
        spec = make_spec(A, B, F, LO, HI)
        info = classify(F, LO, HI, pool)
        red = reduction_probes(spec, LO, HI)
        pi = red.get("perm_invariance")
        row = {"A": A, "B": B, "n": len(F), "density": round(len(F) / len(range(LO, HI + 1, 2)), 5),
               "kind": info.get("kind"), "class_fit": info.get("class_fit"),
               "avoid_fit": info.get("avoid_fit"),
               "small_bound": info.get("small_bound"),
               "period": info.get("period"),
               "probe_extends": (F[-1] >= HI - 4) if F else False,
               "reduction": (pi or {}).get("reduction") if pi and pi.get("invariant") else None,
               "examples": F[:8]}
        row["score"], row["why"] = score(row)
        rows.append(row)

    # 等价去重: 例外集完全相同 => 同一个问题
    seen, ded = {}, []
    for r in sorted(rows, key=lambda x: -x["score"]):
        key = (r["A"], r["B"])
        sig = (r["n"], tuple(r["examples"][:4]), r["kind"])
        if sig in seen:
            continue
        seen[sig] = key
        ded.append(r)
    dup = len(rows) - len(ded)

    ded.sort(key=lambda x: (-x["score"], -x["n"]))
    print(f"输入 {len(surv)} 个幸存猜想 -> 等价去重 {dup} 个 -> **{len(ded)} 个最终候选**\n")
    print(f"{'分':>3}{'例外':>6}{'密度':>9}  {'机器能说的':<20}类对")
    print("-" * 94)
    for r in ded[:18]:
        desc = r["kind"] or "—"
        if r["class_fit"]:
            desc = f"⊆{r['class_fit']['class']}"
        elif r.get("avoid_fit"):
            desc = f"避开{r['avoid_fit']['avoids']}"
        elif r["small_bound"]:
            desc = f"<{r['small_bound']}"
        if r["period"]:
            desc = f"周期{r['period']}"
        print(f"{r['score']:>3}{r['n']:>6}{r['density']:>9.3%}  {desc:<20}{r['A']} + {r['B']}")

    print(f"\n== 详情(前 8) ==")
    for r in ded[:8]:
        print(f"\n[{r['score']}分] {r['A']} + {r['B']}  ({r['n']} 例外, {r['density']:.3%})")
        print(f"  机器能说的: kind={r['kind']} class_fit={r['class_fit']} "
              f"avoid_fit={r.get('avoid_fit')} small={r['small_bound']}")
        print(f"  理由: {'; '.join(r['why']) or '(无)'}")
        if r["reduction"]:
            print(f"  机器归约: {r['reduction'][:90]}")
        print(f"  例外前几个: {r['examples']}")

    print("\n诚实: 排序只回答'该先送哪几个去查文献', **不回答'是不是新的'**。")
    (HERE / "out/demo/final_candidates.json").write_text(
        json.dumps({"input": len(surv), "dup_removed": dup, "candidates": ded},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print("已存 out/demo/final_candidates.json")


if __name__ == "__main__":
    main()
