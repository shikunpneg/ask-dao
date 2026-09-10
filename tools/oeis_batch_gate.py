# -*- coding: utf-8 -*-
"""tools/oeis_batch_gate.py — 批量 OEIS 门: 全库序列候选 -> 自动分级

对 out/demo 下所有含"可转整数序列"evidence 的候选批量过本地 stripped.gz 门:
  - 提取候选的整数序列(evidence.exceptions / found / seq / count 序列)
  - 前缀(6项, 偏移容忍 0..3) 命中 OEIS -> 已知/疑似
  - 未命中 -> 未见(机制检查候选)
  - 自动回写 docs/novelty_ledger.md
诚实标注: 本地索引(39.9万) 是"文献沉默代理", 非文献门。
"""
import gzip
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "data" / "stripped.gz"
OUT_LEDGER = HERE / "docs" / "novelty_ledger.md"


def load_index(max_terms=12):
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


def extract_seq(item):
    """从 candidate dict 提取整数序列(优先 evidence 各字段)。返回 (seq, field_name)。"""
    if not isinstance(item, dict):
        return None, None
    ev = item.get("evidence")
    if not isinstance(ev, dict):
        return None, None
    for key in ("exceptions", "exc", "found", "seq", "counts", "vals"):
        v = ev.get(key)
        if isinstance(v, list) and v and all(isinstance(x, (int, float)) and float(x).is_integer() for x in v):
            return [int(x) for x in v], key
    return None, None


def lookup(prefix, idx, offset_tol=3):
    hits = []
    plen = len(prefix)
    for a, terms in idx:
        for off in range(min(offset_tol, len(terms) - plen + 1)):
            if terms[off:off + plen] == prefix:
                hits.append((a, off))
                break
    return hits


def mechanism_check(seq):
    """简单机制检查: 差值稳定/比例稳定/回文/线性/二次/指数 信号。返回标签列表。"""
    if len(seq) < 4:
        return ["too_short"]
    tags = []
    diffs = [seq[i + 1] - seq[i] for i in range(len(seq) - 1)]
    if all(d == diffs[0] for d in diffs[1:4]):
        tags.append("线性")
    dd = [diffs[i + 1] - diffs[i] for i in range(len(diffs) - 1)]
    if len(dd) >= 3 and all(d == dd[0] for d in dd[1:3]):
        tags.append("二次")
    if seq and seq[0] and all(abs(seq[i + 1] / seq[i] - seq[1] / seq[0]) < 1e-9 for i in range(min(3, len(seq) - 1))):
        tags.append("等比")
    if seq == seq[::-1] and len(seq) >= 4:
        tags.append("回文")
    if all(seq[i] == 0 for i in range(2, len(seq))):
        tags.append("尾部归零")
    if not tags:
        tags.append("无简单机制")
    return tags


def main():
    idx = load_index()
    print(f"索引 {len(idx)} 条 OEIS 序列")

    # 收集全库候选
    candidates = []
    seen_ids = set()
    for jf in sorted((HERE / "out" / "demo").glob("*.json")):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  skip {jf.name}: {e}")
            continue
        items = data if isinstance(data, list) else data.get("problems", [])
        if not isinstance(items, list):
            continue
        for it in items:
            if not isinstance(it, dict):
                continue
            seq, field = extract_seq(it)
            if seq is None:
                continue
            pid = it.get("id", f"{jf.stem}:{len(candidates)}")
            key = (pid, tuple(seq))
            if key in seen_ids:
                continue
            seen_ids.add(key)
            candidates.append({"file": jf.name, "id": pid, "seq": seq, "field": field,
                               "statement": it.get("statement", ""), "item": it})

    print(f"候选(带整数序列): {len(candidates)} 个")
    print("=" * 90)

    graded = []
    for c in candidates:
        hits = lookup(c["seq"][:6], idx)
        c["oeis_hits"] = [h[0] for h in hits[:5]]
        c["mechanism"] = mechanism_check(c["seq"])
        if hits:
            c["grade"] = "已知/疑似"
        else:
            c["grade"] = "未见候选"
        graded.append(c)

    byg = Counter(c["grade"] for c in graded)
    print(f"分级: {dict(byg)}")

    for g in ("已知/疑似", "未见候选"):
        sub = [c for c in graded if c["grade"] == g]
        print(f"\n== {g} ({len(sub)}) ==")
        for c in sub[:30]:
            print(f"  [{c['file'][:20]:20s}] {c['id']:20s} seq={c['seq'][:6]} mech={c['mechanism']}"
                  + (f" -> {c['oeis_hits'][:3]}" if c["oeis_hits"] else ""))
        if len(sub) > 30:
            print(f"  ... 共 {len(sub)} 个")

    # 回写 ledger
    seen = [c for c in graded if c["grade"] == "未见候选"]
    OUT_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with OUT_LEDGER.open("a", encoding="utf-8") as f:
        f.write(f"\n## 批量 OEIS 门 ({len(graded)} 候选)\n")
        f.write(f"本地索引 {len(idx)} 条; 已知/疑似 {byg.get('已知/疑似',0)}; 未见 {len(seen)}\n")
        for c in seen[:40]:
            f.write(f"- `{c['id']}` [{c['file']}] {c['statement'][:70]}\n"
                    f"  seq={c['seq'][:8]} 机制={c['mechanism']}\n")
        if len(seen) > 40:
            f.write(f"- ... 共 {len(seen)} 个未见候选\n")
    print(f"\n已回写 {OUT_LEDGER.name}: 未见候选 {len(seen)} 个")

    # 存结构化结果
    (HERE / "out" / "demo" / "oeis_batch_gate.json").write_text(
        json.dumps(graded, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已存 out/demo/oeis_batch_gate.json")


if __name__ == "__main__":
    main()
