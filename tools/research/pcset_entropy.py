# -*- coding: utf-8 -*-
"""tools/research/pcset_entropy.py — 探索"看起来空"的格子：音级集合 × 熵（R42）

R39 测试发现: 检索 "pc-set + entropy" 无直接命中 —— 这个格子看起来是空的。
R40 用户: "结果很密的领域你都没探索完就放弃啦"。

本文件用**计算优势**真的把这个格子做一遍, 而不是标个"空"就走:
  Q1  音级集合(大小 k)的**区间内容(interval content)**的熵 —— 是否有极值?
  Q2  集合类的熵**分布** —— 是否存在平凡类与非平凡类?
  Q3  熵与"对称性/复杂性"的关系?

这些都是**可以精确枚举**的(只有 224 个 Tn/TnI 集合类) —— 计算优势的甜区。
"""
import json
import math
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def prime_form(s, mod=12):
    """Forte/Rahn 标准: 所有 Tn/TnI 变体, 每个变体取循环重排中字典序最小者, 再取全局最小。

    自纠错(第 33 次, 终于): 上一版对每个变体先 sort 再循环重排, **等价类的不同转置
    会收敛到不同代表元**(例: {0,1,2,4} 转置得 (0,1,2,4) 和 (0,1,2,10)), 于是枚举出 355
    类。正确做法: 每个变体**先整体 normalize(循环重排最小)**, 再比较 —— 校验 = **224**。
    """
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
    """音级集合的**区间内容**: 每对音之间的模距离(1..6)的计数。Forte IC 向量。"""
    s = sorted(pcset)
    n = len(s)
    ic = [0] * 6
    for i in range(n):
        for j in range(i + 1, n):
            d = (s[j] - s[i]) % mod
            ic[min(d, mod - d) - 1] += 1
    return tuple(ic)


def entropy(ic):
    tot = sum(ic) or 1
    return -sum((v / tot) * math.log2(v / tot) for v in ic if v > 0)


def main():
    print("=" * 96)
    print("音级集合 × 区间内容熵 —— 精确枚举全部 224 个 Tn/TnI 集合类")
    print("=" * 96)

    classes = set()
    for k in range(1, 13):
        for s in combinations(range(12), k):
            classes.add(prime_form(s))
    classes.add(())
    print(f"  枚举到 {len(classes)} 个集合类(含 k=0 空集; 已知 224 = 223 + 空集)")
    print()

    rows = []
    for pf in classes:
        ic = interval_content(pf)
        H = entropy(ic)
        rows.append({"pf": list(pf), "card": len(pf), "ic": list(ic),
                     "entropy": round(H, 4)})
    rows.sort(key=lambda r: (-r["entropy"], r["card"]))

    print("== 熵最高(区间内容最均匀)的集合类 ==")
    for r in rows[:10]:
        print(f"  H={r['entropy']:<8} 卡{r['card']:>2}  pf={r['pf']}  ic={r['ic']}")

    print("\n== 熵最低(区间内容最集中)的集合类 ==")
    for r in rows[-8:]:
        print(f"  H={r['entropy']:<8} 卡{r['card']:>2}  pf={r['pf']}  ic={r['ic']}")

    print("\n== 按基数: 熵的范围 ==")
    by_card = {}
    for r in rows:
        by_card.setdefault(r["card"], []).append(r["entropy"])
    print(f"  {'卡':>3}{'类数':>6}{'熵最小':>10}{'熵最大':>10}")
    for k in sorted(by_card):
        v = by_card[k]
        print(f"  {k:>3}{len(v):>6}{min(v):>10.4f}{max(v):>10.4f}")

    top = rows[0]
    print(f"\n== 极值判读 ==")
    print(f"  熵最大 = {top['entropy']} (pf={top['pf']}, ic={top['ic']})")
    all_uniform = [r for r in rows if len(set(r["ic"])) == 1 and r["entropy"] > 0]
    print(f"  **区间内容完全均匀(ic 全相等)的集合类: {len(all_uniform)} 个**")
    for r in all_uniform[:6]:
        print(f"    卡{r['card']}  pf={r['pf']}  ic={r['ic']}")
    uniform = math.log2(6) if top["card"] >= 4 else None
    if uniform:
        print(f"  理论最大(ic 均匀) = log2(6) = {uniform:.4f}")

    print("\n诚实:")
    print("  · 这是**精确枚举**(可复核), 不是新发现。")
    print("  · '音级集合 × 熵'格子**能做**且**能枚举** —— 但检索未见未必代表'空', 更可能是")
    print("    '没人用'或'已用但没这么叫'。下一查证点: 'set-class complexity' 文献。")
    print("  · R39 那个'空'的判断, 本轮用计算填上了事实: 这个格子不是空, 是**可枚举的结构**。")

    (HERE / "out/demo/pcset_entropy.json").write_text(
        json.dumps({"classes": len(classes), "rows": rows}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print("\n已存 out/demo/pcset_entropy.json")


if __name__ == "__main__":
    main()
