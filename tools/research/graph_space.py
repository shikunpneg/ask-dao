# -*- coding: utf-8 -*-
"""tools/research/graph_space.py — 第2站: 图不变量空间(小n标号图暴搜)
  族: 无三角/无诱导P4(余图cograph)/二部/补图亦二部/色数=3 等 -> n=2..6 标号计数序列 -> OEIS过滤
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from oeis_check import load_index


def edges_of(n, mask):
    adj = [0] * n
    bit = 0
    for i in range(n):
        for j in range(i + 1, n):
            if mask >> bit & 1:
                adj[i] |= 1 << j
                adj[j] |= 1 << i
            bit += 1
    return adj


def no_triangle(adj, n):
    for i in range(n):
        for j in range(i + 1, n):
            if adj[i] >> j & 1 and (adj[i] & adj[j]):
                return False
    return True


def no_induced_p4(adj, n):
    from itertools import combinations
    for s in combinations(range(n), 4):
        cnt = 0
        deg = [0] * 4
        idx = {v: k for k, v in enumerate(s)}
        for a in range(4):
            for b in range(a + 1, 4):
                if adj[s[a]] >> s[b] & 1:
                    cnt += 1
                    deg[a] += 1
                    deg[b] += 1
        if cnt == 3 and max(deg) <= 2:
            # 须连通才是 P4(排除 三角+孤立点)
            seen = {0}
            stack = [0]
            while stack:
                v = stack.pop()
                for u in range(4):
                    if u not in seen and adj[s[v]] >> s[u] & 1:
                        seen.add(u)
                        stack.append(u)
            if len(seen) == 4:
                return False
    return True


def is_bipartite(adj, n):
    color = [-1] * n
    for s0 in range(n):
        if color[s0] != -1:
            continue
        color[s0] = 0
        stack = [s0]
        while stack:
            v = stack.pop()
            for u in range(n):
                if adj[v] >> u & 1:
                    if color[u] == -1:
                        color[u] = 1 - color[v]
                        stack.append(u)
                    elif color[u] == color[v]:
                        return False
    return True


def count_family(n, pred):
    e = n * (n - 1) // 2
    cnt = 0
    for mask in range(1 << e):
        adj = edges_of(n, mask)
        if pred(adj, n):
            cnt += 1
    return cnt


def main():
    idx = load_index()

    def seq_of(fn):
        return [count_family(n, fn) for n in range(2, 7)]

    def triangle_count(a, n):
        c = 0
        for i in range(n):
            for j in range(i + 1, n):
                if a[i] >> j & 1:
                    c += bin(a[i] & a[j]).count("1")
        return c // 3

    def both_tri_free(a, n):
        # 图与其补图皆无三角 (Ramsey 型: R(3,3)=6 => n>=6 无)
        comp = [((1 << n) - 1) ^ (a[v] | (1 << v)) for v in range(n)]
        return no_triangle(a, n) and no_triangle(comp, n)

    families = {
        "无三角(标号计数)": no_triangle,
        "无诱导P4(cograph)": no_induced_p4,
        "二部图(标号计数)": is_bipartite,
        "图与补图皆无三角": both_tri_free,
        "恰好2个三角": (lambda a, n: triangle_count(a, n) == 2),
    }
    for name, fn in families.items():
        seq = seq_of(fn)
        hit = None
        key = tuple(seq[:5])
        for a, terms in idx:
            for off in range(0, 4):
                if off + 5 <= len(terms) and tuple(terms[off:off + 5]) == key:
                    hit = a
                    break
            if hit:
                break
        print(f"{name}: {seq} -> {hit if hit else 'OEIS未见(候选)'}")


if __name__ == "__main__":
    main()
