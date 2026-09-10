# -*- coding: utf-8 -*-
"""tools/field_forge.py — 领域锻造：造**真的新领域**（Track 5 的攻关）

## 为什么 Track 5 之前失败(R35)
计算语言学用的 9 个语料**全是哲学/科学文本** —— 同质。两条语言统计律(门泽拉特 0/9、Heaps
全部落在同一带)都恒成立, 于是产不出例外。**同质语料 = 没有边界 = 没有新问题。**

## "新领域"的**操作定义**(不是词藻)
一个领域 F = (对象, 方法, 问题式), 其中:
  ① **对象是载体**(可枚举/可计算)   —— 否则是概念词
  ② **方法给判定路由**(可跑)         —— 否则产不出可判问题
  ③ 对象×方法的**配对**产生母域都不问的问题式
  ④ 该配对在文献中未见
⇒ 造新领域 = **找一个尚未配对的 (对象, 方法)**, 且两者都满足①②。

## 关键判据: **异质性是燃料**
R35 的教训: 同质语料没有边界。**新领域的价值来自"两个原本不相干的结构被迫相遇"** ——
艺术(对称/格律)与信息论(熵)原本不相干; 让它们相遇, 界面就是新问题。

## 本文件实例化两个领域(都用**真实艺术形式**, 非合成噪声)
  F1 **计算诗律学** (诗学 × 形式语言 × 信息论)
     对象: 近体诗格律(平仄/对粘/押韵) —— 真实艺术形式, 规则有典
     方法: 形式文法枚举 + 熵率
     F1 无需新数据: **格律本身就是一套形式语言**, 可直接枚举
  F2 **计算纹样学** (装饰艺术 × 对称群 × 信息论)
     对象: 周期纹样(窗棂/几何纹) —— 真实艺术形式
     方法: 对称群计算 + 局部纹理熵枚举
"""
import json
import math
import sys
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


# ==================================================================
# F1 计算诗律学：格律是一套形式语言
# ==================================================================
# 平 = 0, 仄 = 1
PING, ZE = 0, 1
# 五言四个基本律句(标准"二四分明"式)
WU_BASE = {
    "A": (ZE, ZE, PING, PING, ZE),      # 仄仄平平仄
    "B": (PING, PING, ZE, ZE, PING),    # 平平仄仄平
    "C": (PING, PING, PING, ZE, ZE),    # 平平平仄仄
    "D": (ZE, ZE, ZE, PING, PING),      # 仄仄仄平平
}


def to_seven(wu):
    """七言 = 前面加两个与首二字相反的音。"""
    prefix = tuple(1 - wu[0] for _ in range(2))
    return prefix + tuple(wu)


def sig(line, seven=False):
    """二四(六)分明: 取位置 1,3(,5) 的音(0-indexed)。"""
    idx = (1, 3, 5) if seven else (1, 3)
    return tuple(line[i] for i in idx)


def rhyme_ok(line):
    """押韵: 句末为平。"""
    return line[-1] == PING


def build_valid_poems(n_lines, seven=False):
    """用 对/粘/押韵 生成全部合律的篇式。

    对: 一联内两行 二四(六) 相反;  粘: 联间(2-3行) 二四(六) 相同;
    押韵: 偶数句末为平。
    """
    bases = {k: (to_seven(v) if seven else v) for k, v in WU_BASE.items()}
    # 每个"二四签名"对应的律句
    by_sig = defaultdict(list)
    for k, v in bases.items():
        by_sig[sig(v, seven)].append(k)

    poems = []
    # 首句可取任意律句(首句入韵与否都是合法篇式)
    for start in bases:
        seq = [start]
        ok = True
        for i in range(1, n_lines):
            prev = bases[seq[-1]]
            prev_sig = sig(prev, seven)
            if i % 2 == 1:      # 奇数行(0-indexed 的 1,3,5..) = 联内第二句 -> 对
                want = tuple(1 - x for x in prev_sig)
            else:               # 偶数行(2,4,..) = 下一联首句 -> 粘
                want = prev_sig
            cands = by_sig.get(want, [])
            if i % 2 == 1:      # 偶数句押韵
                cands = [c for c in cands if rhyme_ok(bases[c])]
            if not cands:
                ok = False
                break
            # 对/粘 只定签名, 同签名内可能有多个律句 -> 分支
            seq.append(cands[0])
            # 记下分支(为计数, 用组合展开, 见下)
        if ok:
            poems.append(seq)
    # 上面的贪心只取第一条; 真正的计数用**签名级枚举**(同签名句可替换)
    return bases, by_sig, poems


def _dp_count(n_lines, by_sig, seven):
    """DP 计数(自纠错第 20 次: 首版用显式路径枚举, 七言律诗直接爆掉)。
    state = 上一行的音串; 逐行转移计数。"""
    cur = Counter()
    for s, lines in by_sig.items():
        for v in lines:
            cur[v] += 1
    for i in range(1, n_lines):
        nxt = Counter()
        for prev, ways in cur.items():
            ps = sig(prev, seven)
            want = tuple(1 - x for x in ps) if i % 2 == 1 else ps
            for v in by_sig.get(want, ()):
                if i % 2 == 1 and not rhyme_ok(v):
                    continue
                nxt[v] += ways
        cur = nxt
    return sum(cur.values()), cur


def count_poems(n_lines, seven=False):
    """精确计数合律篇式(同签名内多句可替换)。"""
    bases = {k: (to_seven(v) if seven else v) for k, v in WU_BASE.items()}
    by_sig = defaultdict(list)
    for k, v in bases.items():
        by_sig[sig(v, seven)].append(v)
    total, _ = _dp_count(n_lines, by_sig, seven)
    return total, bases


def laxity_test(n_lines, seven=False):
    """**一三五不论** 是否为真? 放开位置 1,3(,5), 看合法篇式如何膨胀。"""
    bases = {k: (to_seven(v) if seven else v) for k, v in WU_BASE.items()}
    free_idx = (0, 2, 4) if seven else (0, 2)

    by_sig = defaultdict(set)
    for k, v0 in bases.items():
        for combo in product((PING, ZE), repeat=len(free_idx)):
            v = list(v0)
            for pos, tone in zip(free_idx, combo):
                v[pos] = tone
            by_sig[sig(tuple(v), seven)].add(tuple(v))
    total, _ = _dp_count(n_lines, by_sig, seven)
    return total


def field1_prosody():
    print("=" * 88)
    print("F1 计算诗律学 —— 对象: 近体诗格律(真实艺术形式) × 方法: 形式文法枚举 + 熵率")
    print("=" * 88)
    rows = []
    for seven in (False, True):
        tag = "七言" if seven else "五言"
        for n_lines, form in ((4, "绝句"), (8, "律诗")):
            strict, bases = count_poems(n_lines, seven)
            lax = laxity_test(n_lines, seven)
            H = math.log2(strict) if strict else 0
            rows.append({"体": tag + form, "严格合律篇式": strict,
                         "格律熵(bit)": round(H, 3),
                         "放开一三五后": lax,
                         "膨胀倍率": round(lax / strict, 1) if strict else None})
            print(f"  {tag}{form}: 严格合律 **{strict}** 式 | 格律熵 {H:.3f} bit | "
                  f"放开一三五后 {lax} 式 (膨胀 {lax/strict:.1f}×)")

    print("\n  机器可提出、且自己答不出的问题:")
    print("    Q1 「一三五不论」**精确**成立吗? 放开后多出来的篇式, 是全部合法, 还是含'孤平/三平调'等病?")
    print("       (机器只能枚举放松规则后的篇式, 判不了'哪些被诗律学视为禁忌' —— 那是规范判断)")
    print("    Q2 格律熵随篇长的增长率: 是收敛到某个常数, 还是线性增长? 极限是什么?")
    print("    Q3 哪些**理论合律**的篇式在实际诗集中从不出现? (需语料; 见下)")
    return rows


# ==================================================================
# F2 计算纹样学：对称群 × 局部纹理熵
# ==================================================================
def d4_symmetry_order(grid, n):
    """n×n 二值纹样在 D4(旋转+镜像)下的稳定子群阶。"""
    def rot(g):
        return [[g[n - 1 - c][r] for c in range(n)] for r in range(n)]

    def mir(g):
        return [row[::-1] for row in g]

    cur = grid
    seen = set()
    order = 0
    for _ in range(4):
        for t in (cur, mir(cur)):
            key = tuple(tuple(r) for r in t)
            if key not in seen:
                seen.add(key)
            if key == tuple(tuple(r) for r in grid):
                order += 1
        cur = rot(cur)
    return order


def _canon(b, block=2):
    """2×2 块在自身 D4 下的**无序**代表元(用于稳健性检验)。"""
    idx = [(i, j) for i in range(block) for j in range(block)]
    forms = []
    for k in range(4):
        rot = tuple(b[(k * (block - 1) + (i if k % 2 == 0 else j) * 1) % len(b)]
                    for i, j in idx)
        forms.append(rot)
    # 简化: 用全部旋转+镜像
    g = [[b[i * block + j] for j in range(block)] for i in range(block)]
    outs = []
    cur = g
    for _ in range(4):
        outs.append(tuple(v for row in cur for v in row))
        outs.append(tuple(v for row in [r[::-1] for r in cur] for v in row))
        cur = [[cur[block - 1 - c][r] for c in range(block)] for r in range(block)]
    return min(outs)


def local_entropy(grid, n, block=2, oriented=True):
    """局部纹理熵: 2×2 块分布的经验熵(bit)。

    oriented=True  : 窗口按**位置序**计(旋转/镜像后的块算不同)
    oriented=False : 窗口按**无序块**计(旋转/镜像后的块合并)
    —— 头版只报了 oriented, 需两者并报才诚实(见 R36)。
    """
    cnt = Counter()
    for r in range(n - block + 1):
        for c in range(n - block + 1):
            b = tuple(grid[r + i][c + j] for i in range(block) for j in range(block))
            cnt[b if oriented else _canon(b, block)] += 1
    tot = sum(cnt.values()) or 1
    H = 0.0
    for v in cnt.values():
        p = v / tot
        H -= p * math.log2(p)
    return H


def field2_ornament(n=4):
    print("\n" + "=" * 88)
    print(f"F2 计算纹样学 —— 对象: {n}×{n} 周期纹样(真实装饰艺术) × 方法: D4 对称群 + 局部纹理熵")
    print("=" * 88)
    print(f"  枚举全部 2^{n*n} = {2**(n*n)} 个纹样 ...")
    by_order = defaultdict(list)
    for bits in range(2 ** (n * n)):
        g = [[(bits >> (r * n + c)) & 1 for c in range(n)] for r in range(n)]
        s = d4_symmetry_order(g, n)
        by_order[s].append((local_entropy(g, n, oriented=True),
                            local_entropy(g, n, oriented=False)))

    print(f"\n  {'对称阶':>6}{'纹样数':>9}   {'有序块熵 最小/平均/最大':>28}{'无序块熵最大':>13}")
    frontier = []
    for s in sorted(by_order):
        v = by_order[s]
        o = [a for a, _b in v]
        u = [b for _a, b in v]
        print(f"  {s:>6}{len(v):>9}   {min(o):>8.3f}{sum(o)/len(o):>10.3f}{max(o):>9.3f}"
              f"{max(u):>13.3f}")
        frontier.append({"symmetry": s, "count": len(v),
                         "H_min": round(min(o), 3), "H_max": round(max(o), 3),
                         "H_unoriented_max": round(max(u), 3)})

    # 关键问题: 高对称纹样能否同时高局部熵?
    hi_o = max(f["H_max"] for f in frontier if f["symmetry"] >= 4)
    lo_o = max(f["H_max"] for f in frontier if f["symmetry"] == 1)
    hi_u = max(f["H_unoriented_max"] for f in frontier if f["symmetry"] >= 4)
    lo_u = max(f["H_unoriented_max"] for f in frontier if f["symmetry"] == 1)
    print(f"\n  **发现**: 高对称(阶≥4)局部熵上限 = {hi_o:.4f}(有序)/{hi_u:.4f}(无序)")
    print(f"            低对称(阶=1)局部熵上限 = {lo_o:.4f}(有序)/{lo_u:.4f}(无序)")
    print(f"  => 有序口径**两者相同** ⇒ **对称性不牺牲局部复杂度**: 全 D4 对称的纹样(4×4 中央 2×2 方块),")
    print(f"     其 9 个 2×2 窗口**全部不同**, 达上界 log2(9)={math.log2(9):.4f}")
    print(f"  => 无序口径下高对称略低({hi_u:.3f} vs {lo_u:.3f}) —— 这是**计数口径**的效应, 并报以免夸大")
    print("\n  机器可提出、且自己答不出的问题:")
    print("    Q1 对称阶与局部纹理熵是否存在**硬上界关系**? 还是可同时取高值?")
    print("       (n=4 枚举可看趋势; 一般 n 的定理机器证不了)")
    print("    Q2 真实窗棂/几何纹样落在该 (对称, 熵) 平面的什么位置? 是 Pareto 前沿还是内部?")
    print("       (需真实纹样数据 —— 当前没有)")
    return frontier


def main():
    f1 = field1_prosody()
    f2 = field2_ornament(4)
    print("\n" + "=" * 88)
    print("领域锻造的诚实边界")
    print("=" * 88)
    print("- F1 的**对象是真实的**(近体诗格律), 方法可跑, 问题是机器答不出的(规范/极限/语料)。")
    print("- F1 **不需要新数据**: 格律本身就是形式语言 —— 这是本轮的关键发现。")
    print("- F2 的**对象是真实的**(装饰纹样), 但当前**无真实纹样数据**, 只在合成网格上枚举。")
    print("- 两个领域都**尚未过文献门** —— '造出新领域'与'该领域里有新问题'是两件事。")
    print("- 已写到 +: 需人工/联网确认该配对是否真的未见。")
    (HERE / "out/demo/field_forge.json").write_text(
        json.dumps({"F1_prosody": f1, "F2_ornament": f2}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print("\n已存 out/demo/field_forge.json")


if __name__ == "__main__":
    main()
