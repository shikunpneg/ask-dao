# -*- coding: utf-8 -*-
"""sparse_engine.py — 生成空间切换: 参照系薄的参数化映射族纪录
   S1: x -> (x^2 + c) mod m 的原始循环长 对 m 的序列(按 c 参数化)
   S2: 广义 Collatz: n奇->p*n+q, n偶->n/2, 最大停时对 q 的序列(按 p 参数化)
   产出: 记录 + 提取整数序列 -> 交 OEIS 离线反查(宽容) -> 未见者 = 候选(N2 级, 待 web)"""
import math
from .model import ProblemRecord, TreeRoot

ROOT = TreeRoot("R_sparse", "稀疏生成空间: 参数化映射族", "数学",
                ["参数化映射", "循环/停时纪录"], "参照系薄处: 每个 (c,m)/(p,q) 小参数的纪录表")


def max_cycle_len(c, m, steps=2000):
    best = 0
    for x0 in range(m):
        seen = {}
        x = x0
        s = 0
        while s < steps and x not in seen:
            seen[x] = s
            x = (x * x + c) % m
            s += 1
        if x in seen:
            best = max(best, s - seen[x])
    return best


def max_stop(p, q, N=20000, cap=2000):
    memo = {1: 0}
    best = 0
    for n in range(2, N + 1):
        x = n
        chain = []
        while x != 1 and x not in memo:
            if x > 10 ** 7:
                break
            chain.append(x)
            x = p * x + q if x % 2 else x // 2
            if len(chain) > cap:
                break
        if x == 1 or x in memo:
            steps = 0
            base = memo.get(x, 0)
            for y in reversed(chain):
                base += 1
                memo[y] = base
            best = max(best, memo[n])
        else:
            for y in chain:
                memo[y] = -1
    return best


def run(m_hi=64, q_hi=9):
    out = []

    def add(id_, seed, motifs, template, binds, stmt, judgement, status, tag, edge=None):
        out.append(ProblemRecord(id_, "数学", seed, motifs, template, stmt, judgement,
                                 status=status, honesty=tag, binds=binds,
                                 tree={"parent": ROOT.id, "edge": edge or template}))

    # S1: 对 m=2..64, c=1 的原始循环长度序列(去0)
    s1 = [max_cycle_len(1, m) for m in range(2, m_hi + 1)]
    add("S1", "二次迭代 x→(x²+1) mod m: 最长原始循环随 m 怎么变?",
        ["参数化映射", "循环纪录"], "稀疏模板: 迭代-循环 按 m 序列化",
        {"c": 1, "m": "2..64"},
        f"x→x²+1 mod m 的最长原始循环(去平凡)序列: {s1[:12]}…",
        {"method": "全态迭代", "seq": s1}, "真(纪录表, 机器枚举)",
        "纪录(参数表; 未见OEIS需反查)", "二次迭代循环纪录")
    # S2: 对 p=3,5,7; q=1..9 最大停时序列
    for p in (3, 5, 7):
        seq = [max_stop(p, q) for q in range(1, q_hi + 1)]
        add(f"S2p{p}", f"广义Collatz: n奇→{p}n+q, 最大停时随 q 的变化?",
            ["参数化映射", "停时纪录"], "稀疏模板: 停时-纪录 按 q 序列化",
            {"p": p, "q": "1..9"},
            f"p={p} 最大停时序列(q=1..{q_hi}): {seq}",
            {"method": "带记忆迭代", "seq": seq}, "真(纪录表, 机器枚举)",
            "纪录(参数表; 广义Collatz族部分已知需反查)", f"广义Collatz p={p}")
    return [ROOT], out
