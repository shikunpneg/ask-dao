# -*- coding: utf-8 -*-
"""tools/station3.py — 第3站: 极小构造纪录
 S3a: 二元字含每个2长模式>=t次的最小长 L_min(t), t=1..5 (双 de Bruijn 型)
 S3b: 最小奇数 n 使 r2(n)/4 = k (两平方表示数恰为k), k=1..12
两者 -> OEIS 宽容过滤, 幸存=候选纪录"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from oeis_check import load_index


def word_ok(word, L, t):
    cnt = [0] * 4
    for i in range(L - 1):
        idx = ((word >> i) & 3)
        cnt[idx] += 1
        if cnt[idx] >= t:
            pass
    return all(c >= t for c in cnt)


def min_double_debruijn(t, maxL=26):
    for L in range(2 * t + 1, maxL + 1):
        need = 4 * t
        if L - 1 < need:
            continue
        for word in range(1 << L):
            if word_ok(word, L, t):
                return L
    return None


def build_d1m3(M):
    d = [0] * (M + 1)
    for r in range(1, M + 1, 4):
        for m in range(r, M + 1, r):
            d[m] += 1
    for r in range(3, M + 1, 4):
        for m in range(r, M + 1, r):
            d[m] -= 1
    return d


def main():
    idx = load_index()

    def chk(seq):
        for off in range(0, 4):
            key = tuple(seq[:5])
            for a, terms in idx:
                if off + 5 <= len(terms) and tuple(terms[off:off + 5]) == key:
                    return a
        return None

    # S3a
    seq_a = [min_double_debruijn(t) for t in range(1, 6)]
    print("S3a L_min(t) t=1..5:", seq_a, "->", chk(seq_a) or "OEIS未见(候选)")
    # S3b
    M = 3000000
    d = build_d1m3(M)
    seq_b = []
    for k in range(1, 13):
        n_found = None
        for n in range(1, M + 1, 2):
            if d[n] == k:  # r2/4 = d1 - d3
                n_found = n
                break
        seq_b.append(n_found)
    print("S3b 最小奇n(r2/4=k):", seq_b, "->", chk([x for x in seq_b if x]) or "OEIS未见(候选)")
    with (Path(__file__).resolve().parent.parent / "docs/novelty_ledger.md").open("a", encoding="utf-8") as f:
        f.write(f"## 第3站 极小构造\n- S3a L_min(t): {seq_a} -> {chk(seq_a)}\n- S3b 最小奇n: {seq_b} -> {chk([x for x in seq_b if x])}\n")


if __name__ == "__main__":
    main()
