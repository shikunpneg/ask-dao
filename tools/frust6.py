# -*- coding: utf-8 -*-
"""tools/frust6.py — n=6 全部 6-边图的阻挫签名分类(大规模)"""
import itertools, json
from collections import Counter, defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent

pairs = list(itertools.combinations(range(6), 2))  # 15 对

def frust(edges):
    ec = {}
    for bits in itertools.product((1,-1), repeat=6):
        e = 0
        for u,v in edges:
            e += -1*bits[u]*bits[v]
        ec[e] = ec.get(e,0)+1
    gs = min(ec)
    return gs, ec[gs], len(ec)

def triangles(edges):
    se = set(tuple(sorted(e)) for e in edges)
    t=0
    for tri in itertools.combinations(range(6),3):
        if all(tuple(sorted((tri[a],tri[b]))) in se for a,b in itertools.combinations(range(3),2)):
            t+=1
    return t

# 枚举全部 6-边图(5005 个)
sig_of = defaultdict(list)
for mask in range(2**15):
    edges = [pairs[i] for i in range(15) if (mask>>i)&1]
    if len(edges) != 6: continue
    gs,deg,nlv = frust(edges)
    tri = triangles(edges)
    sig_of[(gs,deg,nlv,tri)].append(edges)

print(f"n=6 全部 6-边图: {sum(len(v) for v in sig_of.values())} 个, 分成 {len(sig_of)} 种(能量,简并,能级,三角数)签名")
print("\n== 按(简并度, 三角数)聚类 ==")
by = defaultdict(int)
for (gs,deg,nlv,tri), gs_ in sig_of.items():
    by[(deg,tri)] += len(gs_)
for k,v in sorted(by.items()):
    print(f"  简并度={k[0]} 三角数={k[1]}: {v} 个图")
