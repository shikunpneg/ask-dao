# -*- coding: utf-8 -*-
"""tools/research/sparse_expand.py — S2 参数扩张扫荡 + OEIS 过滤"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ask_dao_machine import sparse_engine
from oeis_check import load_index


def chk(seq, idx):
    key = tuple(seq[:6])
    for a, terms in idx:
        for off in range(0, 4):
            if off + 6 <= len(terms) and tuple(terms[off:off + 6]) == key:
                return a
    return None


def main():
    idx = load_index()
    surv = []
    for p in (3, 5, 7, 11, 13, 15, 17):
        vals = [sparse_engine.max_stop(p, q) for q in range(1, 22, 2)]
        hit = chk(vals, idx)
        print(f"p={p} 奇q1..21 seq{vals[:8]} -> {hit if hit else 'OEIS未见(候选)'}")
        if not hit:
            surv.append(p)
    seq1 = [sparse_engine.max_stop(p, 1) for p in (3, 5, 7, 11, 13, 15, 17)]
    print("q=1 p索引:", seq1, "->", chk(seq1, idx))
    with (Path(__file__).resolve().parent.parent / "docs/novelty_ledger.md").open("a", encoding="utf-8") as f:
        f.write(f"## S2 扩张\n- OEIS未见 p: {surv}; q=1 p索引命中情况见上\n")
    return surv


if __name__ == "__main__":
    main()
