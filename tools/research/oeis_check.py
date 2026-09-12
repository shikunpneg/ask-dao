# -*- coding: utf-8 -*-
"""tools/research/oeis_check.py — 离线 OEIS 反查: 用序列前缀在 stripped.gz 中找 A 编号
用法: 传入若干 (名字, 前缀list), 输出命中 A id (无名字文件, 给出编号供查)"""
import gzip
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "stripped.gz"


def load_index(max_terms=12):
    if not DATA.exists():
        raise FileNotFoundError(
            f"OEIS 参照系缺失: {DATA}\n"
            f"  取数据: python -m ask_dao_machine data fetch   (约 32MB, 来自 oeis.org)\n"
            f"  或手动下载 https://oeis.org/stripped.gz 放到 {DATA}")
    idx = []
    with gzip.open(DATA, "rt", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if not line.startswith("A"):
                continue
            a = line[:7]
            rest = line[7:].strip()
            if "," not in rest:
                continue
            terms = [int(t) for t in rest.split(",")[:max_terms] if t.lstrip("-").isdigit()]
            if terms:
                idx.append((a, terms))
    return idx


def lookup(prefix, idx, offset_tol=3):
    hits = []
    plen = len(prefix)
    for a, terms in idx:
        for off in range(offset_tol):
            if off + plen <= len(terms) and terms[off:off + plen] == prefix:
                hits.append((a, off))
                break
    return hits


def main():
    from ask_dao_machine import combo_engine as ce
    idx = load_index()
    print("indexed sequences:", len(idx))
    queries = {
        "CB04 禁010": ce.counts_avoid_word(8, "010"),
        "CB06 禁0101": ce.counts_avoid_word(8, "0101"),
        "CB08 禁0000": ce.counts_avoid_word(8, "0000"),
        "MR4 maxrun4": ce.counts_maxrun(8, 2, 4),
    }
    for name, seq in queries.items():
        hits = lookup(seq, idx)
        print(f"{name}: 前缀{seq} -> {[h[0] for h in hits[:6]]}")


if __name__ == "__main__":
    main()
