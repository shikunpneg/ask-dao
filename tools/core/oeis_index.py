# -*- coding: utf-8 -*-
"""tools/core/oeis_index.py — OEIS 离线倒排索引(批量反查用)

问题: 旧 tools/research/oeis_check.py 的 lookup 对每次查询线性扫描 ~40 万条序列, 批量不可用。
本模块: 一次性建索引, 之后每次反查 O(词长)。

索引结构: dict[窗口元组(6项)] -> [A编号,...], 窗口取每条 OEIS 序列的起始位置 0..OFF_MAX。
反查: 对查询序列的每个滑动窗口查表; 命中即候选, 再做对齐验证(支持偏移)。

用法:
    from oeis_index import OEISIndex
    idx = OEISIndex.load()            # 建/读缓存
    idx.lookup([1,2,3,5,8,13,21])     # -> [{'a':..,'offset':..,'terms':..}]
"""
import gzip
import pickle
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "data" / "stripped.gz"
CACHE = HERE / "data" / "oeis_index.pkl"

WIN = 6        # 窗口长度(项)
OFF_MAX = 4    # 索引每条序列的起始位置 0..OFF_MAX-1
MAX_TERMS = 40  # 每条序列最多保留项数


def _parse(path, max_terms=MAX_TERMS):
    """流式读 stripped.gz -> (aid, terms)。"""
    with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if not line.startswith("A"):
                continue
            aid = line[:7]
            body = line[7:].strip()
            if not body:
                continue
            terms = []
            for t in body.split(","):
                t = t.strip()
                if not t:
                    continue
                try:
                    terms.append(int(t))
                except ValueError:
                    break
                if len(terms) >= max_terms:
                    break
            if len(terms) >= WIN:
                yield aid, terms


class OEISIndex:
    def __init__(self, table, seqs):
        self.table = table      # {window_tuple: [aid,...]}
        self.seqs = seqs        # {aid: terms}

    # ---------- 构建 ----------
    @classmethod
    def build(cls, path=DATA, verbose=True):
        t0 = time.time()
        table, seqs = {}, {}
        n = 0
        for aid, terms in _parse(path):
            seqs[aid] = terms
            n += 1
            for p in range(min(OFF_MAX, max(1, len(terms) - WIN + 1))):
                w = tuple(terms[p:p + WIN])
                table.setdefault(w, []).append((aid, p))
            if verbose and n % 100000 == 0:
                print(f"  ... {n} 条", file=sys.stderr)
        if verbose:
            print(f"索引完成: {n} 条序列, {len(table)} 个窗口, {time.time()-t0:.1f}s",
                  file=sys.stderr)
        return cls(table, seqs)

    @classmethod
    def load(cls, path=DATA, cache=CACHE, rebuild=False):
        if cache.exists() and not rebuild:
            with open(cache, "rb") as fh:
                obj = pickle.load(fh)
            if obj.get("win") == WIN and obj.get("off") == OFF_MAX:
                return cls(obj["table"], obj["seqs"])
        idx = cls.build(path)
        try:
            with open(cache, "wb") as fh:
                pickle.dump({"win": WIN, "off": OFF_MAX,
                             "table": idx.table, "seqs": idx.seqs}, fh,
                            protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            print("缓存写入失败(不影响使用):", e, file=sys.stderr)
        return idx

    # ---------- 反查 ----------
    def lookup(self, seq, max_hits=8, min_win=None):
        """查询整数序列在 OEIS 中的命中。
        返回 [{'a','offset','shift','matched'}]，offset=OEIS序列内的对齐位置。"""
        if not seq or len(seq) < WIN:
            return []
        hits, seen = [], set()
        for q in range(len(seq) - WIN + 1):
            w = tuple(seq[q:q + WIN])
            for aid, p in self.table.get(w, ()):
                if aid in seen:
                    continue
                # 对齐验证: 我们的 seq[q] 对应 OEIS 的 terms[p]
                terms = self.seqs[aid]
                shift = p - q
                if shift < 0:
                    continue
                ok, m = 0, 0
                for i, v in enumerate(seq):
                    j = i + shift
                    if j >= len(terms):
                        break
                    m += 1
                    if terms[j] != v:
                        break
                    ok += 1
                need = min(min_win or WIN, len(seq))
                if ok >= need:
                    seen.add(aid)
                    hits.append({"a": aid, "offset": shift, "matched": ok,
                                 "oeis_len": len(terms)})
                    if len(hits) >= max_hits:
                        return hits
        return hits

    def is_known(self, seq, min_win=None):
        return len(self.lookup(seq, max_hits=1, min_win=min_win)) > 0


if __name__ == "__main__":
    print("建索引中(首次约需 1-3 分钟)...")
    idx = OEISIndex.load()
    print("序列数:", len(idx.seqs), "| 窗口数:", len(idx.table))
    # 自检: 用几条已知序列验证索引正确
    checks = {
        "质数 A000040": [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37],
        "斐波那契 A000045": [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89],
        "卡特兰 A000108": [1, 1, 2, 5, 14, 42, 132, 429, 1430, 4862],
        "阶乘 A000142": [1, 1, 2, 6, 24, 120, 720, 5040, 40320],
    }
    for name, s in checks.items():
        print(f"  {name}: {[h['a'] for h in idx.lookup(s)]}")
    # 自检: 一个应未见的人造序列
    fake = [7, 13, 29, 61, 127, 251, 509, 1021]
    print("  人造序列:", idx.lookup(fake), "(应为空或无关)")
