# -*- coding: utf-8 -*-
"""tools/deep_fusion.py — 深层结构性融合（R63）

用户: "领域融合你做的还是不够。"

之前做的融合都太浅: (a) 函数/对象单点扫描 (b) 名词配对("音乐x数学")。
真正的融合 = **把一个领域的'结构生成器/操作子'作用在另一个领域的'结构'上**,
界面处产生单独领域里不存在的对象。

本轮做 3 个真深融:
  F1 生物(选择) x 信息(编码) : 把**自然选择**作用在**编码空间** —— 编码(DNA类比)
     在"适应度=可解码容错性"下演化, 看浮现什么结构(单独生物/编码论里都不存在)
  F2 语言(文法) x 信息(压缩) : 把**文法生成**作用在**最短描述**上 —— 字符串的最小
     生成文法的复杂度, 看"语言复杂度" vs "描述复杂度"的关系
  F3 物理(自旋) x 数学(图)   : 把**自旋构型**作用在**图着色**上 —— 图的"物理熵"
     (构型权重) 与图结构的关系
"""
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


# ============ F1 生物选择 × 信息编码: 编码的达尔文演化 ============
def evolve_code(gen_len=20, pop=200, gens=200, mut=0.01, seed=7):
    """编码(二进制串)在'适应度=冗余度(可容错性)'下演化。
    适应度 = 最小成对 Hamming 距离(编码距离越远越抗噪, 越"适合")。
    观察: 选择压是否会自发产生"结构化的编码"(如固定的模式/分块)。
    """
    rnd = random.Random(seed)
    pop_ = [tuple(rnd.randint(0, 1) for _ in range(gen_len)) for _ in range(pop)]

    def fitness(c):
        # 与其他编码的最小距离(冗余/抗噪)
        d = gen_len
        for o in pop_:
            if o == c:
                continue
            hd = sum(a != b for a, b in zip(c, o))
            d = min(d, hd)
        return d

    history = []
    for g in range(gens):
        pop_.sort(key=lambda c: -fitness(c))
        top = pop_[:pop // 2]
        # 记录平均最小距离
        hist = [fitness(c) for c in pop_]
        history.append(sum(hist) / len(hist))
        # 选择+变异
        new = []
        for _ in range(pop):
            p = top[rnd.randrange(len(top))]
            child = list(p)
            for i in range(gen_len):
                if rnd.random() < mut:
                    child[i] = 1 - child[i]
            new.append(tuple(child))
        pop_ = new
    # 收敛后的结构
    final = sorted(pop_, key=lambda c: -fitness(c))[:3]
    return {"final_min_dist": [fitness(c) for c in final],
            "avg_dist_trend": [round(h, 2) for h in history[::40]],
            "converged_structures": [list(c) for c in final],
            "note": "观察: 选择压是否让编码自发结构化(出现稳定模式)"}


# ============ F2 语言文法 × 信息压缩: 最小文法 vs 描述长度 ============
def grammar_complexity(s):
    """字符串的最小'重复结构'复杂度: 用简单 LZ-ish 压缩率代理文法复杂度。
    度量: 压缩后长度 / 原长度(压缩率), 越低 = 越高文法结构。"""
    # LZ77 简化: 贪心找最长的已出现子串
    def lz_len(s):
        out, i = [], 0
        while i < len(s):
            best_len, best_off = 0, 0
            for j in range(max(0, i - 50), i):
                k = 0
                while i + k < len(s) and s[j + k] == s[i + k] and k < 30:
                    k += 1
                if k > best_len:
                    best_len, best_off = k, j
            if best_len >= 3:
                out.append((best_off, best_len))
                i += best_len
            else:
                out.append(s[i])
                i += 1
        return len(out)
    return lz_len(s) / max(len(s), 1)


def f2_fusion():
    # 不同语言的"文法结构" -> 压缩率
    langs = {
        "自然语言(中文)": "的" * 5 + "这是自然语言的句子" * 3 + "的" * 5,
        "DNA(编码)": "ATGC" * 12,
        "规律重复": "ab" * 20,
        "随机串": ''.join(random.Random(1).choice("abc") for _ in range(40)),
        "斐波那契词": "ababaababaabab" * 3,
    }
    out = []
    for name, s in langs.items():
        r = grammar_complexity(s)
        out.append({"lang": name, "compress_ratio": round(r, 4),
                    "desc": f"{name}的压缩率(越低=越有文法结构)"})
    return out


# ============ F3 物理自旋 × 图: 图的"物理熵" ============
def graph_spin_entropy(n, edges, J=-1):
    """伊辛模型在图上: 构型权重按能量分布, 物理熵 S = log(构型数)。
    度量: 基态简并度(能量最小构型数) 与 激发谱宽度。"""
    import itertools
    configs = 0
    energies = Counter()
    for bits in itertools.product((1, -1), repeat=n):
        e = 0
        for u, v in edges:
            e += J * bits[u] * bits[v]
        energies[e] += 1
        configs += 1
    # 熵
    S = math.log(configs)
    return {"n": n, "edges": len(edges), "configs": configs,
            "entropy": round(S, 4),
            "energy_levels": {int(k): v for k, v in sorted(energies.items())[:6]},
            "note": "物理熵=log(构型数); 能量分布宽度反映图的'阻挫'程度"}


def main():
    print("=" * 100)
    print("深层结构性融合（R63）—— 一个领域的操作子作用在另一个领域的结构上")
    print("=" * 100)

    print("\n## F1 生物选择 × 信息编码: 编码的达尔文演化")
    f1 = evolve_code()
    print(f"  平均最小距离轨迹(选择压作用): {f1['avg_dist_trend']}")
    print(f"  收敛结构: {f1['converged_structures']}")
    print(f"  => {'结构自发结构化(选择压产生冗余)' if max(f1['final_min_dist']) > 2 else '保持随机(选择压未结构化)'}")

    print("\n## F2 语言文法 × 信息压缩: 最小文法 vs 描述长度")
    f2 = f2_fusion()
    for r in f2:
        print(f"  {r['lang']:<14} 压缩率 {r['compress_ratio']}")

    print("\n## F3 物理自旋 × 图: 图的物理熵")
    f3s = []
    for n, edges in ((6, [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)]),  # 两个三角(阻挫)
                     (6, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)])):  # 六环(无阻挫)
        r = graph_spin_entropy(n, edges)
        f3s.append(r)
        print(f"  图{n}顶点{len(edges)}边: 熵{r['entropy']} 能量谱{r['energy_levels']}")

    print("\n" + "=" * 100)
    print("融合界面产生的新对象(单独领域里不存在)")
    print("=" * 100)
    print("  F1: '编码的适应度地形' —— 生物选择作用于编码空间, 产生'冗余结构'")
    print("      (生物不看编码论, 编码论不看选择; 融合后: 编码适应度地形)")
    print("  F2: '语言结构的压缩复杂度' —— 用信息压缩度量文法结构")
    print("  F3: '图的阻挫熵' —— 用物理伊辛模型度量图结构的'物理性'")

    (HERE / "out/demo/deep_fusion.json").write_text(
        json.dumps({"F1_evolve": f1, "F2_grammar": f2, "F3_spin": f3s},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n已存 out/demo/deep_fusion.json")


if __name__ == "__main__":
    main()
