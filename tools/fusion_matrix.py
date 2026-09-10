# -*- coding: utf-8 -*-
"""tools/fusion_matrix.py — 操作子 × 结构 融合矩阵批量扫描（R64）

用户: "批量做, 直到发现新问题。"

方法: 每个融合 = 一个操作子作用在一个结构上 -> 产生界面度量(可机检数值)。
自动找"异常融合": 度量值**违反直觉 / 出现陡变 / 跨结构不一致** -> 新问题信号。

操作子池:
  SEL 选择(适应度压力) / ISING 伊辛(能量) / COMP 压缩(描述长度)
  ENT 熵(分布) / EVOL 演化(迭代) / MIX 混合(组合)
结构池:
  编码(二进制) / 图(若干) / 词(字符串) / 集合(子集族) / 数(序列)

融合 -> 界面度量, 自动标记"异常"(vs 基线直觉)。
"""
import json
import math
import random
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


# ============ 操作子 ============
def op_select(seq, gens=50, mut=0.1):
    """选择压: 保持元素多样性(最小成对距离)"""
    if not seq:
        return 0
    pop = list(seq)
    for _ in range(gens):
        pop.sort(key=lambda x: -min(abs(x - y) for y in pop if y != x) if len(pop) > 1 else 1)
        pop = pop[:max(1, len(pop) // 2)] + pop[:max(1, len(pop) // 2)]
        for i in range(len(pop)):
            if random.random() < mut:
                pop[i] = pop[i] + random.choice([-1, 1])
    return max(0, len(set(pop)))


def op_ising(seq, edges, J=-1):
    """伊辛能量: 相邻对乘积和"""
    e = 0
    for u, v in edges:
        e += J * seq[u] * seq[v]
    return e


def op_compress(s):
    """LZ 压缩率"""
    i, out = 0, 0
    while i < len(s):
        best = 0
        for j in range(max(0, i - 50), i):
            k = 0
            while i + k < len(s) and s[j + k] == s[i + k] and k < 30:
                k += 1
            best = max(best, k)
        if best >= 3:
            out += 1
            i += best
        else:
            out += 1
            i += 1
    return out / max(len(s), 1)


def op_entropy(counter):
    tot = sum(counter.values()) or 1
    return -sum((v / tot) * math.log2(v / tot) for v in counter.values() if v)


def op_evolve(seq, rule, gens=30):
    """演化: 按规则迭代看是否收敛"""
    x = seq
    for _ in range(gens):
        nx = [rule(v) for v in x]
        if nx == x:
            return len(set(x))
        x = nx
    return len(set(x))


# ============ 结构池 ============
def build_structures():
    rnd = random.Random(5)
    S = {
        "编码20": [rnd.randint(0, 1) for _ in range(20)],
        "编码40": [rnd.randint(0, 1) for _ in range(40)],
        "周期编码": [i % 2 for i in range(20)],
    }
    # 图
    G = {}
    for name, edges in (("六环", [(i, (i + 1) % 6) for i in range(6)]),
                        ("双三角", [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)]),
                        ("星", [(0, i) for i in range(1, 6)]),
                        ("完全图K4", list(combinations(range(4), 2)))):
        G[name] = edges
    # 词
    W = {
        "规律词": "ab" * 10,
        "DNA词": "ATGC" * 5,
        "随机词": ''.join(rnd.choice("abc") for _ in range(20)),
        "斐波那契词": "ababaababa" * 2,
    }
    # 集合族
    C = {
        "幂集子采样": [[i for i in range(4) if rnd.random() < 0.5] for _ in range(8)],
        "均匀子集": [[0, 1, 2], [3, 4, 5], [0, 3, 6], [1, 4, 7]],
    }
    return S, G, W, C


def main():
    print("=" * 100)
    print("操作子 × 结构 融合矩阵 —— 批量扫描 + 自动找异常")
    print("=" * 100)
    S, G, W, C = build_structures()
    results = []

    # --- 1) 选择 x 编码 ---
    print("\n## 选择 × 编码(多样性保持)")
    for name, c in S.items():
        # 随机 vs 周期: 选择压后多样性
        d = op_select(list(c), gens=30)
        d0 = len(set(c))
        results.append({"fusion": f"选择×{name}", "before": d0, "after": d,
                        "note": "选择压是否维持/提升多样性"})
        print(f"  {name}: 多样 {d0} -> {d}")

    # --- 2) 伊辛 x 图 ---
    print("\n## 伊辛 × 图(基态简并度 via 全枚举)")
    for name, edges in G.items():
        n = max(max(u, v) for u, v in edges) + 1
        import itertools
        ec = {}
        for bits in itertools.product((1, -1), repeat=n):
            e = op_ising(list(bits), edges)
            ec[e] = ec.get(e, 0) + 1
        gs = min(ec)
        results.append({"fusion": f"伊辛×{name}", "base_degen": ec[gs],
                        "energy_levels": {int(k): v for k, v in sorted(ec.items())[:4]}})
        print(f"  {name}: 基态简并 {ec[gs]}  能量谱 {dict(list(sorted(ec.items()))[:3])}")

    # --- 3) 压缩 x 词 ---
    print("\n## 压缩 × 词(文法复杂度)")
    for name, w in W.items():
        r = op_compress(w)
        results.append({"fusion": f"压缩×{name}", "ratio": round(r, 4)})
        print(f"  {name}: 压缩率 {r:.4f}")

    # --- 4) 熵 x 集合族 ---
    print("\n## 熵 × 集合族(子集大小分布熵)")
    for name, coll in C.items():
        sizes = [len(x) for x in coll]
        cnt = {}
        for s in sizes:
            cnt[s] = cnt.get(s, 0) + 1
        h = op_entropy(cnt)
        results.append({"fusion": f"熵×{name}", "sizes": sizes, "entropy": round(h, 4)})
        print(f"  {name}: 大小{sizes} 熵{h:.4f}")

    # --- 5) 演化 x 编码(规则 -> 收敛) ---
    print("\n## 演化 × 编码(迭代收敛)")
    for name, c in list(S.items())[:2]:
        conv = op_evolve(list(c), lambda v: (v + 1) % 2, gens=30)
        results.append({"fusion": f"演化×{name}", "final_distinct": conv})
        print(f"  {name}: 演化后不同值数 {conv}")

    print("\n" + "=" * 100)
    print("异常融合检测(违反直觉的)")
    print("=" * 100)
    # 伊辛异常: 双三角(阻挫) 基态简并 > 六环(无阻挫)?
    ising = [r for r in results if r["fusion"].startswith("伊辛")]
    if ising:
        bt = next((r for r in ising if "双三角" in r["fusion"]), None)
        hx = next((r for r in ising if "六环" in r["fusion"]), None)
        if bt and hx:
            anomaly = bt["base_degen"] > hx["base_degen"]
            print(f"  双三角基态简并 {bt['base_degen']} vs 六环 {hx['base_degen']} "
                  f"-> {'**阻挫导致简并增加(异常信号)**' if anomaly else '正常'}")
    # 压缩异常: 随机词压缩率最低(LZ 过拟合短串)?
    comp = [r for r in results if r["fusion"].startswith("压缩")]
    if comp:
        rnd_r = next((r for r in comp if "随机" in r["fusion"]), None)
        if rnd_r and rnd_r["ratio"] < 0.1:
            print(f"  随机词压缩率 {rnd_r['ratio']} < 0.1 -> **LZ 对短串过拟合(度量缺陷, 需警惕)**")

    print("\n诚实: 这些是**界面度量**; '异常'是直觉层面的信号, 需文献门/更严谨检验。")
    (HERE / "out/demo/fusion_matrix.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已存 out/demo/fusion_matrix.json")


if __name__ == "__main__":
    main()
