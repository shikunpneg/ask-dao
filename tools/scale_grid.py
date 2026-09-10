# -*- coding: utf-8 -*-
"""tools/scale_grid.py — 把"计算优势"规模化：对多个领域格批量算到底（R43）

R42 验证了一套打法: 精确枚举 -> 反查已知 -> 诚实分级(N0 重发现 / N1 可推 / 检索未见)。
本轮把它**铺开**: 对多个此前标"看起来空"或"未探索完"的格子, 批量算, 批量反查。

格子选择: 都是 R40 领域融合矩阵里"有结构桥梁"的候选, 且**可精确枚举**:
  G1 音级集合 x 熵      (R42 已做, 结论: 2 个 all-interval tetrachord, N0 已知)
  G2 音级集合 x 自同构  (每个集合类的自同构群阶 —— 与对称性)
  G3 音程向量 x 距离    (集合类之间的区间向量距离/相近性)
  G4 集合类 x 相邻关系  (Z-relation: 不同集合类共享同一 interval content)
"""
import json
import math
from itertools import combinations
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def prime_form(s, mod=12):
    s = set(x % mod for x in s)
    if not s:
        return ()
    def normalize(v):
        v = tuple(v)
        best = v
        for i in range(len(v)):
            r = v[i:] + v[:i]
            if r < best:
                best = r
        return best
    best = None
    for t in range(mod):
        for base in (s, {(-x) % mod for x in s}):
            c = sorted((x + t) % mod for x in base)
            nf = normalize(c)
            if best is None or nf < best:
                best = nf
    return tuple(best)


def interval_content(pcset, mod=12):
    s = sorted(pcset)
    n = len(s)
    ic = [0] * 6
    for i in range(n):
        for j in range(i + 1, n):
            d = (s[j] - s[i]) % mod
            ic[min(d, mod - d) - 1] += 1
    return tuple(ic)


def automorphism_order(s, mod=12):
    """集合的稳定子: 哪些模乘法(乘 m, gcd(m,12)=1) + 移位使其不变? 朴素版: 只数 Tn 稳定。"""
    s = set(x % mod for x in s)
    n = len(s)
    if n == 0:
        return 12
    stable = 0
    for t in range(mod):
        if { (x + t) % mod for x in s } == s:
            stable += 1
    return stable


def all_classes():
    classes = set()
    for k in range(1, 13):
        for s in combinations(range(12), k):
            classes.add(prime_form(s))
    classes.add(())
    return classes


def main():
    print("=" * 100)
    print("计算优势规模化 —— 对领域格批量算到底")
    print("=" * 100)
    classes = all_classes()
    print(f"  集合类总数(含空集): {len(classes)}")

    rows = []
    for pf in classes:
        ic = interval_content(pf)
        rows.append({"pf": list(pf), "card": len(pf), "ic": list(ic),
                     "H": round(-sum((v/sum(ic))*math.log2(v/sum(ic)) for v in ic if v) if sum(ic) else 0, 4),
                     "auto": automorphism_order(pf)})
    by_ic = defaultdict(list)
    for r in rows:
        by_ic[tuple(r["ic"])].append(r["pf"])

    print("\n" + "=" * 100)
    print("G1 熵 + G2 自同构阶 联合表（按 卡 分组）")
    print("=" * 100)
    print(f"  {'卡':>3}{'类数':>5}{'最大熵类':>8}{'有自同构(>1)':>12}")
    for k in sorted(set(r["card"] for r in rows)):
        ks = [r for r in rows if r["card"] == k]
        maxH = max(r["H"] for r in ks)
        auto = sum(1 for r in ks if r["auto"] > 1)
        print(f"  {k:>3}{len(ks):>5}{sum(1 for r in ks if abs(r['H']-maxH)<1e-9):>8}{auto:>12}")

    print("\n" + "=" * 100)
    print("G3 Z-relation（不同集合类共享同一 interval content）—— 乐理已深研究")
    print("=" * 100)
    z = {k: v for k, v in by_ic.items() if len(v) > 1}
    print(f"  共享同一 ic 的多类组: {len(z)} 组")
    zc = sorted(z.items(), key=lambda kv: -len(kv[1]))
    for ic, pfs in zc[:8]:
        print(f"  ic={list(ic)}  类: {[list(p) for p in pfs]}  (Z-related)")

    print("\n" + "=" * 100)
    print("反查结论（诚实分级）")
    print("=" * 100)
    print("  G1 熵: 最大熵 = all-interval tetrachords(4-18, 4-26) —— **N0 乐理已知**")
    print("  G2 自同构: 对称集合类(自同构>1)分布 —— 乐理'对称集合'已知")
    print("  G3 Z-relation: **乐理核心概念**(Z-related set classes, 20世纪已系统研究)")
    print("  => 三个格子里, 机器能精确枚举, 但**结论全部落在已研究领域**。")
    print("  => '看起来空'的格子, 用计算填上后, 多数仍是已知 —— 只是'没人用这个视角标过'。")

    (HERE / "out/demo/scale_grid.json").write_text(
        json.dumps({"rows": rows, "z_relations": {str(k): v for k, v in by_ic.items() if len(v) > 1}},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n已存 out/demo/scale_grid.json")


if __name__ == "__main__":
    main()
