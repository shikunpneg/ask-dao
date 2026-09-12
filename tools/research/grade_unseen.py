# -*- coding: utf-8 -*-
"""tools/research/grade_unseen.py — 对 OEIS 门产出的未见候选做严格分级

从 out/demo/oeis_batch_gate.json 读分级结果, 对 `未见候选` 施加三道硬筛:
  1. 序列长度 >= 6  (太短=信息不足)
  2. 机制检查不是 trivial (去掉 线性/等比/尾部归零 这类平凡结构)
  3. 去重(按前缀)   —— 同一族扫描的重复例外不算独立

输出:
  - 独立未见候选清单(有真实机制、非平凡)
  - 存入 out/demo/grade_unseen.json
  - 追加到 docs/novelty_ledger.md
诚实标注: 这只是"OEIS 沉默 + 机制非平凡", 不是文献门, 更不是显著性证书。
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent.parent
GATE = HERE / "out" / "demo" / "oeis_batch_gate.json"
OUT = HERE / "out" / "demo" / "grade_unseen.json"
LEDGER = HERE / "docs" / "novelty_ledger.md"

# 平凡机制标签: 这些不构成"有结构的发现"
TRIVIAL = {"线性", "等比", "尾部归零", "too_short"}


def trivial(mech):
    return bool(mech) and all(m in TRIVIAL for m in mech)


def main():
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    unseen = [c for c in gate if c["grade"] == "未见候选"]
    # 去重(前缀): 保留序列最长的
    by_pfx = {}
    for c in unseen:
        p = tuple(c["seq"][:6])
        if p not in by_pfx or len(c["seq"]) > len(by_pfx[p]["seq"]):
            by_pfx[p] = c
    uniq = list(by_pfx.values())

    # 硬筛: 长度>=6 且 机制非平凡
    strong = [c for c in uniq if len(c["seq"]) >= 6 and not trivial(c["mechanism"])]
    weak = [c for c in uniq if len(c["seq"]) >= 6 and trivial(c["mechanism"])]
    short = [c for c in uniq if len(c["seq"]) < 6]

    # 按"领域族"(statement 前缀)分组去重: 同族扫描只留一个真独立候选
    def fam(c):
        s = c["statement"] or ""
        if "回文" in s and "素数" in s:
            return "回文+素数覆盖(跨进制)"
        if "质数" in s and ("边形" in s or "素数" in s):
            return "质数+多边形覆盖"
        if "Collatz" in s:
            return "Collatz链长"
        if "D4" in s or "纹样" in s:
            return "D4纹样轨道数"
        if "模" in s and "环" in s:
            return "模迭代环长"
        if "阻挫" in s:
            return "图阻挫比例"
        if "音程" in s:
            return "音集音程向量"
        return s[:12]

    fam_counts = Counter(fam(c) for c in strong)
    by_fam = {}
    for c in strong:
        f = fam(c)
        if f not in by_fam or len(c["seq"]) > len(by_fam[f]["seq"]):
            by_fam[f] = c
    independent = sorted(by_fam.values(), key=lambda x: -len(x["seq"]))

    print("=" * 80)
    print(f"OEIS 未见候选严格分级: 去重后 {len(uniq)} 个")
    print(f"  - 强候选(长度>=6 + 机制非平凡): {len(strong)}")
    print(f"  - 领域族去重后独立候选:          {len(independent)}")
    print(f"  - 弱候选(长度>=6 但平凡机制):   {len(weak)}")
    print(f"  - 太短(<6项, 信息不足):         {len(short)}")
    print(f"  领域族分布: {dict(fam_counts)}")
    print("=" * 80)

    for c in independent:
        print(f"\n  ★ {c['id']} [{c['file']}]  (族: {fam(c)})")
        print(f"    stmt: {c['statement'][:70]}")
        print(f"    seq:  {c['seq']}")
        print(f"    机制: {c['mechanism']}")

    # 存结构化结果
    OUT.write_text(json.dumps({
        "independent": [{k: c[k] for k in ("id", "file", "seq", "mechanism", "statement")} for c in independent],
        "strong_count": len(strong),
        "weak": [{k: c[k] for k in ("id", "file", "seq", "mechanism")} for c in weak],
        "short_count": len(short),
        "fam_counts": dict(fam_counts),
        "note": "OEIS 沉默代理 + 机制非平凡 + 领域族去重; 非文献门, 非显著性证书",
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    # 追加 ledger
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(f"\n## 严格分级(去重后 {len(uniq)}): 强 {len(strong)} → 独立 {len(independent)} / 弱 {len(weak)} / 短 {len(short)}\n")
        f.write(f"领域族: {dict(fam_counts)}\n")
        for c in independent:
            f.write(f"- ★ `{c['id']}` [{c['file']}] {c['statement'][:60]} | seq={c['seq'][:8]} | 机制={c['mechanism']}\n")
    print(f"\n已存 {OUT.name}, 独立候选 {len(independent)} 个写入 ledger")


if __name__ == "__main__":
    main()
