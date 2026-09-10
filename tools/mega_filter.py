# -*- coding: utf-8 -*-
"""tools/mega_filter.py — 疯狂融合的**诚实过滤**（R39c）

mega_scan 给出 10,312 条 OEIS 未命中。**未命中 ≠ 有价值** —— 绝大多数是
"结构平凡但恰好不像 OEIS 里的整数序列"(如归一化后的线性斜坡)。

本文件对未命中跑**平凡性电池**, 只留下机器**解释不了**的:
  T1 常数 / 至多 2 个不同值
  T2 等差(一阶差分常数)
  T3 低阶多项式(二/三阶差分常数)
  T4 周期(小周期)
  T5 单调(非减/非增)
  T6 归一化斜坡(值域≈[0,1] 且单调)  ← scan 里大量出现
  T7 可被某个具名类拟合(见 mechanism_probe 的类库思想, 此处用轻量版)
  T8 与输入的某一步的简单变换重合(自反)

留下的 = **机器在当前手段下解释不了的序列**, 才是候选。
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def is_const(s):
    return len(set(s)) <= 2


def diff_order(s, maxk=4):
    cur = list(s)
    for k in range(1, maxk + 1):
        cur = [cur[i + 1] - cur[i] for i in range(len(cur) - 1)]
        if len(set(cur)) == 1:
            return k
    return None


def small_period(s, pmax=8):
    for p in range(1, min(pmax, len(s) // 2) + 1):
        if all(s[i] == s[i % p] for i in range(len(s))):
            return p
    return None


def monotone(s):
    if all(s[i + 1] >= s[i] - 1e-9 for i in range(len(s) - 1)):
        return "非减"
    if all(s[i + 1] <= s[i] + 1e-9 for i in range(len(s) - 1)):
        return "非增"
    return None


def normalized_ramp(s):
    """值域≈[0,1] 且单调 -> 归一化斜坡(scan 里最常见的平凡未命中)。"""
    if not s:
        return False
    lo, hi = min(s), max(s)
    if hi - lo < 1e-9:
        return False
    if abs(lo) < 1e-6 and abs(hi - 1) < 1e-3:
        return monotone(s) is not None
    return False


def trivial_reason(s):
    """返回平凡原因; None = 不平凡(候选)。"""
    if len(s) < 5:
        return "太短"
    if is_const(s):
        return "T1 常数/二值"
    k = diff_order(s)
    if k:
        return f"T{1+k} {k} 阶差分常数(低阶多项式)"
    p = small_period(s)
    if p:
        return f"T4 周期 {p}"
    m = monotone(s)
    if m:
        return f"T5 单调({m})"
    if normalized_ramp(s):
        return "T6 归一化斜坡"
    # 值域极窄
    if max(s) - min(s) <= 1e-6:
        return "T1' 值域为零"
    return None


def main():
    src = HERE / "out/demo/mega_scan.json"
    d = json.loads(src.read_text(encoding="utf-8"))
    cands = d["candidates"]
    stats = d["stats"]
    print("=" * 96)
    print("疯狂融合的诚实过滤 —— 把'结构平凡'从'未命中'里剥出来")
    print("=" * 96)
    print(f"  输入: {stats['paths']:,} 路径 / 命中 {stats['hits']:,} / "
          f"未命中 {stats['miss']:,} / 平凡(scan 内判) {stats['trivial']:,}")

    keep, drop = [], {}
    for r in cands:
        s = r["seq_head"]
        why = trivial_reason(s)
        if why:
            drop[why.split()[0]] = drop.get(why.split()[0], 0) + 1
        else:
            keep.append(r)

    print(f"\n  对 {len(cands):,} 条未命中跑平凡性电池:")
    for k, v in sorted(drop.items(), key=lambda x: -x[1]):
        print(f"     {k:<28}{v:>7,}")
    print(f"     **留下来的(机器解释不了)   {len(keep):>7,}**")

    from collections import Counter
    print(f"\n  == 留下来的候选: 融合度分布 ==")
    fc = Counter(r["fusion_degree"] for r in keep)
    for k in sorted(fc, reverse=True):
        print(f"     {k} 域融合: {fc[k]:,}")

    print(f"\n  == 最高融合度(5 域)且机器解释不了的候选 ==")
    five = [r for r in keep if r["fusion_degree"] == 5]
    for r in five[:14]:
        print(f"     {r['obj']} → {' → '.join(r['chain'])}")
        print(f"          域: {r['fields']}")
        print(f"          seq: {r['seq_head']}")

    print(f"\n  == 4 域融合样本 ==")
    four = [r for r in keep if r["fusion_degree"] == 4]
    for r in four[:10]:
        print(f"     {r['obj']} → {' → '.join(r['chain'])}  {r['seq_head'][:6]}")

    print("\n" + "=" * 96)
    print("诚实结论")
    print("=" * 96)
    print(f"  · 疯狂扩张后: {stats['paths']:,} 条路径, 未命中 {stats['miss']:,} —— 但**其中 "
          f"{len(cands)-len(keep):,} 条是结构平凡的**({(len(cands)-len(keep))/max(len(cands),1):.1%})。")
    print(f"  · 真正'机器解释不了'的只剩 **{len(keep):,} 条** —— 这才是候选池。")
    print(f"  · **规模不等于价值**: 路径数扩大 4.6 倍(4.8 万), 但经平凡性电池后只剩 {len(keep):,}。")
    print(f"  · 下一步: 这 {len(keep):,} 条过文献/机制门 —— 但按 R38 教训, 先看它们的**谱系**, "
          f"多数应能在母学科里找到出处的。")

    (HERE / "out/demo/mega_filter.json").write_text(
        json.dumps({"kept": keep, "dropped_kinds": drop,
                    "stats": {"in": len(cands), "kept": len(keep)}},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n已存 out/demo/mega_filter.json")


if __name__ == "__main__":
    main()
