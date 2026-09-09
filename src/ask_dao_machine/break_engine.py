# -*- coding: utf-8 -*-
"""break_engine.py — 纪录突破型 v0 (P4 突围路线2)
   原则: 不依赖'序列是否在册', 依赖'纪录是否被破/与官方纪录是否一致'。
   v0 两类: B1 Collatz 停时纪录(锚: 官方已知 ≤1e6 纪录 837799/524)
            B2 质数最大间隙纪录(锚: ≤1e6 间隙114@492113; ≤1e7 间隙154@4652353)
   输出: 复核=与锚一致; 突破=候选值超过锚纪录。
"""
import math
from .judges_math import sieve
from .model import ProblemRecord, TreeRoot

ROOT = TreeRoot("R_break", "纪录突破实验室 v0", "数学",
                ["纪录与极值", "质数间隙", "Collatz停时"], "用'破纪录'而非'未见序列'当新颖代理")


def collatz_len_memo(N):
    memo = {1: 0}
    best = (1, 0)
    for n in range(2, N + 1):
        steps = 0
        x = n
        chain = []
        while x not in memo:
            chain.append(x)
            x = 3 * x + 1 if x % 2 else x // 2
            steps += 1
        rem = memo[x]
        for i, y in enumerate(reversed(chain)):
            memo[y] = rem + i + 1
        if memo[n] > best[1]:
            best = (n, memo[n])
    return best


def max_prime_gap(N):
    ps = sieve(N)
    prev = 0
    best_g = 0
    best_p = 0
    for p in range(2, N + 1):
        if ps[p]:
            if prev:
                g = p - prev
                if g > best_g:
                    best_g = g
                    best_p = prev
            prev = p
    return best_p, best_g


def run():
    out = []

    def add(id_, seed, motifs, template, binds, stmt, judgement, status, tag, edge=None):
        out.append(ProblemRecord(id_, "数学", seed, motifs, template, stmt, judgement,
                                 status=status, honesty=tag, binds=binds,
                                 tree={"parent": ROOT.id, "edge": edge or template}))

    n_best, l_best = collatz_len_memo(1000000)
    anchor = (837799, 524)
    ok = (n_best == anchor[0] and l_best == anchor[1])
    add("B1", "Collatz 总停时纪录(≤10^6) 与官方纪录一致吗?",
        ["Collatz3n+1", "纪录与极值"], "纪录复核模板: 停时最大值",
        {"上限": 1000000, "官方锚": anchor},
        f"≤10^6 停时纪录 n={n_best}, 步数={l_best}",
        {"method": "带记忆迭代", "best_n": n_best, "best_len": l_best,
         "anchor": anchor, "match": ok},
        "真(复核)" if ok else "真(纪录) + 锚不一致待查",
        "已知-官方纪录复核" if ok else "纪录(锚不一致·需查证)", "Collatz 停时纪录")
    b1_match = ok

    gp1 = max_prime_gap(1000000)
    a1 = (492113, 114)
    ok1 = (gp1[0] == a1[0] and gp1[1] == a1[1])
    gp2 = max_prime_gap(10000000)
    a2 = (4652353, 154)
    ok2 = (gp2[0] == a2[0] and gp2[1] == a2[1])
    add("B2", "质数最大间隙纪录与官方纪录一致吗? (两个规模锚)",
        ["质数", "间隙与纪录"], "纪录复核模板: 最大间隙",
        {"锚1": ("1e6", a1), "锚2": ("1e7", a2)},
        f"≤1e6 间隙{gp1[1]}@{gp1[0]}; ≤1e7 间隙{gp2[1]}@{gp2[0]}",
        {"method": "筛法扫描", "gap1e6": list(gp1), "anchor1": list(a1), "m1": ok1,
         "gap1e7": list(gp2), "anchor2": list(a2), "m2": ok2},
        "真(双锚复核)" if (ok1 and ok2) else "真(纪录) + 锚不一致待查",
        "已知-官方纪录复核" if (ok1 and ok2) else "纪录(锚不一致·需查证)", "质数最大间隙")
    b2_match = ok1 and ok2
    return [ROOT], out
