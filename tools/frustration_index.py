# -*- coding: utf-8 -*-
"""tools/frustration_index.py — 图的阻挫指数(融合: 伊辛基态简并度 -> 图度量)

对每个小图, 伊辛模型基态简并度作为"阻挫指数"。
看: 阻挫指数能否给图一个**新分类**(不只是已知的'阻挫/非阻挫'二分)。
"""
import json
import math
import itertools
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def all_graphs(n):
    """枚举 n 顶点全部无向图(用边集位掩码)。返回 (edges_list)。"""
    pairs = list(itertools.combinations(range(n), 2))
    out = []
    for mask in range(2 ** len(pairs)):
        edges = [pairs[i] for i in range(len(pairs)) if mask >> i & 1]
        out.append(edges)
    return out


def frustration(edges, n):
    """伊辛基态简并度 + 基态能量。"""
    ec = {}
    for bits in itertools.product((1, -1), repeat=n):
        e = 0
        for u, v in edges:
            e += -1 * bits[u] * bits[v]   # 铁磁 J=-1
        ec[e] = ec.get(e, 0) + 1
    gs = min(ec)
    return ec[gs], gs, len(ec)


def main():
    print("=" * 100)
    print("图的阻挫指数: 伊辛基态简并度 -> 图的新分类?")
    print("=" * 100)
    for n in (4, 5):
        graphs = all_graphs(n)
        # 按(基态能量, 简并度)分组
        by_sig = {}
        for edges in graphs:
            deg, gs, nlv = frustration(edges, n)
            # 归一: 简并度 + 能级数
            key = (gs, deg, nlv)
            by_sig.setdefault(key, []).append(len(edges))
        print(f"\n  n={n}: {len(graphs)} 个图 -> {len(by_sig)} 个阻挫签名")
        print(f"  {'基态能量':>8}{'简并度':>6}{'能级数':>6}{'图数':>6}  例(边数)")
        for (gs, deg, nlv), cnts in sorted(by_sig.items())[:12]:
            print(f"  {gs:>8}{deg:>6}{nlv:>6}{len(cnts):>6}  {sorted(cnts)[:5]}")

    print("\n" + "=" * 100)
    print("关键: 阻挫指数(简并度)能否细分图?")
    print("=" * 100)
    # n=4 里, 相同边数的图, 简并度是否不同
    graphs = all_graphs(4)
    by_edges = {}
    for edges in graphs:
        deg, gs, nlv = frustration(edges, 4)
        by_edges.setdefault(len(edges), set()).add((gs, deg, nlv))
    print(f"  n=4: 相同边数的图, 阻挫签名是否多样?")
    for e, sigs in sorted(by_edges.items()):
        print(f"    边数 {e}: {len(sigs)} 种签名 {sorted(sigs)}")

    # n=4 分类
    print("\n  诚实: 阻挫指数(简并度/能级数)确实把图细分了(同边数不同签名) ——")
    print("  但这是否是'图的新分类'还是'统计物理已知', 需查证。")
    (HERE / "out/demo/frustration_index.json").write_text(
        json.dumps({"n4": {str(e): sorted(s) for e, s in sorted(by_edges.items())}},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print("  已存 out/demo/frustration_index.json")


if __name__ == "__main__":
    main()
