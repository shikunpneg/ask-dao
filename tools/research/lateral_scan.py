# -*- coding: utf-8 -*-
"""tools/research/lateral_scan.py — 侧向矩阵大扫描（R39）

## 用户指令
"计算范围包括生长范围还是太小了" · "多个领域融合也行" · "树生长的还不够多不够长"

## 三个扩张
  **更广**: 对象池 18 → **48**(跨 12 个领域);  方法池 6 → **24**(跨 8 个领域)
  **更融合**: 显式区分 **同域格**(对象与方法同域) 与 **跨域格**(融合) ——
      R38 的证据: `诗律×信息论` 已被占(朱银儿), 但 `音级集合×熵` 看起来是空的。
      **跨域格才是机器相对人类研究者的比较优势**: 人不可能同时精通乐理与信息论。
  **更长**: 层数 L0–L5 → **L0–L7**。新增
      L6 元层: **解空间本身的结构**(不是答案是什么, 而是答案的集合长什么样)
      L7 迁移: 该结论能否**搬到同方法的其他对象**上

## 纪律
矩阵是**候选生成器**, 不是结论。每格都要过: 可算吗(machine) / 文献有吗(lit)。
本文件只做**可算性**的机器判定; 文献状态留空待查(诚实)。
"""
import json
import math
import sys
import time
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src"))

# ==================================================================
# 一、对象池（48 个，跨 12 域）
# ==================================================================
OBJECTS = {
    # ---- 数论 ----
    "素数": ("数论", "int"), "平方数": ("数论", "int"), "三角数": ("数论", "int"),
    "半素数": ("数论", "int"), "Harshad数": ("数论", "int"), "完全幂": ("数论", "int"),
    "回文数_b10": ("数论", "int"), "回文数_b2": ("数论", "int"), "数位单调不减": ("数论", "int"),
    "斐波那契": ("数论", "int"),
    # ---- 组合 ----
    "排列": ("组合", "perm"), "划分": ("组合", "set"), "二元串": ("组合", "str"),
    "标号图": ("组合", "graph"), "树图": ("组合", "graph"), "多联骨牌": ("组合", "grid"),
    "拉丁方": ("组合", "grid"), "禁构族": ("组合", "str"), "集合族": ("组合", "set"),
    # ---- 代数 ----
    "有限群": ("代数", "group"), "多项式": ("代数", "poly"), "有限域": ("代数", "field"),
    "线性递推": ("代数", "seq"),
    # ---- 动力系统 ----
    "二次迭代轨道": ("动力", "seq"), "元胞自动机": ("动力", "ca"), "符号动力学": ("动力", "str"),
    "逻辑斯蒂映射": ("动力", "seq"),
    # ---- 几何/拓扑 ----
    "格点路径": ("几何", "seq"), "平铺": ("几何", "grid"), "纽结": ("拓扑", "knot"),
    "单纯复形": ("拓扑", "complex"),
    # ---- 信息/语言 ----
    "形式语言": ("语言", "lang"), "正则语言": ("语言", "lang"), "自然语料": ("语言", "text"),
    "编码族": ("信息", "str"),
    # ---- 音乐/艺术 ----
    "音级集合": ("音乐", "set"), "音程序列": ("音乐", "seq"), "旋律轮廓": ("音乐", "seq"),
    "平仄格局": ("诗律", "str"), "词牌长短句": ("诗律", "str"), "周期纹样": ("纹样", "grid"),
    # ---- 社会/生物 ----
    "亲属称谓": ("人类学", "graph"), "谱系树": ("生物", "graph"), "种群等位频率": ("生物", "seq"),
    "博弈策略": ("博弈", "set"), "减法博弈": ("博弈", "seq"),
    # ---- 物理/化学 ----
    "自旋构型": ("物理", "grid"), "分子图": ("化学", "graph"), "晶体对称型": ("物理", "group"),
}

# ==================================================================
# 二、方法池（24 个，跨 8 域）
# ==================================================================
METHODS = {
    # ---- 群论 ----
    "对称群与轨道计数": ("群论", "group"),
    "Burnside/Pólya": ("群论", "group"),
    "置换表示": ("群论", "group"),
    # ---- 信息论 ----
    "香农熵": ("信息论", "entropy"),
    "熵率": ("信息论", "entropy"),
    "信道容量": ("信息论", "entropy"),
    "柯氏复杂度": ("信息论", "entropy"),
    # ---- 组合/生成函数 ----
    "生成函数": ("组合", "genfun"),
    "渐近分析": ("组合", "asymp"),
    "递推与DP": ("组合", "recur"),
    # ---- 分析/谱 ----
    "谱与特征值": ("分析", "spectral"),
    "测度与遍历": ("分析", "measure"),
    # ---- 概率统计 ----
    "分布与极限定理": ("概率", "prob"),
    "假设检验": ("统计", "stat"),
    # ---- 逻辑/计算 ----
    "可判定性": ("逻辑", "decide"),
    "复杂度类": ("逻辑", "decide"),
    "自动机": ("逻辑", "auto"),
    # ---- 代数 ----
    "表示论": ("代数", "rep"),
    "同调/不变量": ("代数", "homol"),
    "序与格": ("代数", "order"),
    # ---- 拓扑 ----
    "拓扑不变量": ("拓扑", "topo"),
    # ---- 形式文法 ----
    "文法层级": ("文法", "grammar"),
    "泵引理": ("文法", "grammar"),
    # ---- 动力 ----
    "迭代与不动点": ("动力", "iterate"),
}

# 需要"整数序列"这个载体的方法(可直接套现有管线)
SEQ_METHODS = {"生成函数", "渐近分析", "递推与DP", "谱与特征值", "分布与极限定理",
               "假设检验", "熵率", "香农熵", "迭代与不动点"}


# ==================================================================
# 三、树加深: L0–L7
# ==================================================================
LAYERS_V2 = {
    0: ("L0 计数", "有多少 / 列出"),
    1: ("L1 刻画", "充要条件是什么"),
    2: ("L2 渐近", "增长率/极限/密度"),
    3: ("L3 机制", "为什么是这个结构"),
    4: ("L4 规范", "哪些是禁忌/劣品"),
    5: ("L5 反事实", "实际中哪些从不出现"),
    6: ("L6 元层", "**解空间本身的结构**是什么样的(不是答案, 而是答案的集合)"),
    7: ("L7 迁移", "该结论能否**搬到同方法的其他对象**上"),
}
ASCEND_V2 = {
    0: ("L1", "{o} 的充要刻画是什么"),
    1: ("L2", "{o} 的规模→∞ 时密度/极限是什么"),
    2: ("L3", "为什么 {o} 的极限是那个值"),
    3: ("L4", "{o} 中哪些应判为禁忌/劣品"),
    4: ("L5", "真实材料中哪些 {o} 从不出现"),
    5: ("L6", "{o} 的**解空间**结构是什么(解的集合本身长什么样)"),
    6: ("L7", "{o} 的结论能否迁移到同方法的其他对象"),
}


def fusion_kind(obj, method):
    """同域格 vs 跨域格。**跨域格 = 融合**, 是机器相对人类的比较优势。"""
    of, mf = OBJECTS[obj][0], METHODS[method][0]
    return "同域" if of == mf else f"跨域({of}×{mf})"


def computable(obj, method):
    """机器现在能否真的算这一格? 返回 (可算级别, 需要的载体)。"""
    kind = OBJECTS[obj][1]
    mf = METHODS[method][1]
    if mf == "entropy":
        return ("可算", "枚举该对象族, 统计分布/熵")
    if mf in ("genfun", "asymp", "recur"):
        return ("可算", "生成前 N 项 → 拟合/递推")
    if mf in ("spectral", "prob", "stat", "iterate"):
        return ("可算", "数值计算")
    if mf in ("group",):
        return ("可算" if kind in ("perm", "set", "grid", "group", "poly") else "需建模",
                "构造对称群作用")
    if mf in ("grammar", "auto"):
        return ("可算" if kind in ("str", "lang") else "需建模", "构造形式语言")
    if mf in ("decide",):
        return ("需建模", "定义判定问题")
    if mf in ("topo", "homol", "rep", "measure", "order"):
        return ("需建模", "需专门构造")
    return ("未知", "")


def build_matrix():
    rows = []
    for o in OBJECTS:
        for m in METHODS:
            lvl, need = computable(o, m)
            rows.append({"obj": o, "obj_field": OBJECTS[o][0],
                         "method": m, "method_field": METHODS[m][0],
                         "fusion": fusion_kind(o, m),
                         "computable": lvl, "needs": need})
    return rows


# ==================================================================
# 四、真算几个跨域格（不能只画表, 要出数）
# ==================================================================
def compute_sample():
    """对若干**跨域**格真算一遍, 看能不能出东西。"""
    out = []

    # (1) 元胞自动机 × 香农熵 —— 时空构型的熵
    def ca_entropy(rule, n=200, T=200):
        cells = [0] * n
        cells[n // 2] = 1
        hist = []
        for _ in range(T):
            hist.append(sum(cells))
            new = [0] * n
            for i in range(n):
                l, c, r = cells[(i - 1) % n], cells[i], cells[(i + 1) % n]
                idx = (l << 2) | (c << 1) | r
                new[i] = (rule >> idx) & 1
            cells = new
        tot = T * n
        h = 0.0
        p = sum(hist) / tot
        for q in (p, 1 - p):
            if q > 0:
                h -= q * math.log2(q)
        return round(h, 4), sum(hist)

    ca = {f"rule {r}": ca_entropy(r) for r in (30, 90, 110, 150)}
    out.append({"cell": "元胞自动机 × 香农熵", "fusion": "跨域(动力×信息论)",
                "result": ca, "note": "全局密度熵; 已知结论: rule 90/150 分形, 30 混沌"})

    # (2) 有限群 × 香农熵 —— 乘法表的熵
    def group_table_entropy(n, els, mul):
        idx = {e: i for i, e in enumerate(els)}
        cnt = {}
        for a in els:
            for b in els:
                v = mul(a, b)
                cnt[v] = cnt.get(v, 0) + 1
        tot = n * n
        H = -sum((c / tot) * math.log2(c / tot) for c in cnt.values())
        return round(H, 4)

    def z_n(n):
        return list(range(n)), lambda a, b: (a + b) % n

    def s3():
        els = [(a, b) for a in range(3) for b in range(2)]
        def mul(x, y):
            a, b = x; c, d = y
            return ((a + c) % 3, (b + d) % 2)
        return els, mul

    g = {}
    for n in (4, 5, 6, 7, 8):
        els, mul = z_n(n)
        g[f"Z_{n}"] = group_table_entropy(n, els, mul)
    els, mul = s3()
    g["S_3"] = group_table_entropy(6, els, mul)
    out.append({"cell": "有限群 × 香农熵", "fusion": "跨域(代数×信息论)",
                "result": g,
                "note": "群的乘法表作为均匀分布源: Z_n 熵 = log2(n)(均匀), S_3 = log2(6)。"
                        "⇒ 平凡: 群表每行都是置换, 分布恒均匀"})

    # (3) 排列 × 谱 —— 排列的循环结构
    def cycle_types(n):
        import itertools
        from collections import Counter
        c = Counter()
        for p in itertools.permutations(range(n)):
            seen = [False] * n
            lens = []
            for i in range(n):
                if not seen[i]:
                    L, j = 0, i
                    while not seen[j]:
                        seen[j] = True
                        j = p[j]
                        L += 1
                    lens.append(L)
            c[tuple(sorted(lens, reverse=True))] += 1
        return c

    ct = cycle_types(5)
    out.append({"cell": "排列 × 谱", "fusion": "跨域(组合×分析)",
                "result": {str(k): v for k, v in sorted(ct.items())[:5]},
                "note": "排列的循环型分布 = 无符号斯特林数; **已知**(经典)"})

    # (4) 平仄格局 × 群论 —— 对/粘 作为 Z2 作用
    def prosody_z2():
        # 五言四律句, 看"对"(签名取反)是否构成 Z2 作用
        PING, ZE = 0, 1
        base = {"A": (ZE, ZE, PING, PING, ZE), "B": (PING, PING, ZE, ZE, PING),
                "C": (PING, PING, PING, ZE, ZE), "D": (ZE, ZE, ZE, PING, PING)}
        sg = {k: (v[1], v[3]) for k, v in base.items()}
        flip = lambda t: tuple(1 - x for x in t)
        pairs = sum(1 for k in sg if any(sg[j] == flip(sg[k]) for j in sg))
        orbits = len({frozenset([sg[k], flip(sg[k])]) for k in sg})
        return {"签名": {k: list(v) for k, v in sg.items()}, "取反配对数": pairs, "轨道数": orbits}

    out.append({"cell": "平仄格局 × 对称群", "fusion": "跨域(诗律×群论)",
                "result": prosody_z2(),
                "note": "对 = 签名取反, 是 Z2 作用; 4 律句分成 2 个 Z2-轨道 ⇒ 商掉对偶后只剩 2 类"})

    # (5) 拉丁方 × 熵
    def latin_entropy(n):
        import itertools, random
        rnd = random.Random(7)
        Hs = []
        for _ in range(60):
            # 随机拉丁方: 随机置换的行
            rows = []
            base = list(range(n))
            perms = [list(p) for p in itertools.permutations(base)]
            rnd.shuffle(perms)
            # 贪心构造
            used_cols = [set() for _ in range(n)]
            ok = True
            for p in perms:
                if len(rows) == n:
                    break
                if all(p[c] not in used_cols[c] for c in range(n)):
                    rows.append(p)
                    for c in range(n):
                        used_cols[c].add(p[c])
            if len(rows) < n:
                continue
            # 符号对的联合熵
            cnt = {}
            for r in rows:
                for c in range(n):
                    cnt[(r[c], c)] = cnt.get((r[c], c), 0) + 1
            tot = sum(cnt.values())
            H = -sum((v / tot) * math.log2(v / tot) for v in cnt.values())
            Hs.append(H)
        return {"均值": round(sum(Hs) / len(Hs), 4) if Hs else None,
                "log2(n^2)": round(math.log2(n * n), 4)}

    out.append({"cell": "拉丁方 × 香农熵", "fusion": "跨域(组合×信息论)",
                "result": latin_entropy(5),
                "note": "拉丁方的行列符号对分布: 恒为均匀 ⇒ 熵 = log2(n²)"})

    # (6) 纽结 × 多项式(不变量) —— 用 Alexander 多项式的系数
    def knot_quick():
        # 用几个标准纽结的 Alexander 多项式系数(已知值), 问"系数序列"的性质
        known = {"3_1": [1, -1, 1], "4_1": [1, -3, 1], "5_1": [1, -1, 1, -1, 1],
                 "5_2": [1, -2, 2, -2, 1], "6_1": [1, -3, 3, -3, 1]}
        return {"已知系数": known,
                "note": "机器**无纽结数据**(需拓扑输入) ⇒ 本格当前不可算"}

    out.append({"cell": "纽结 × 同调/不变量", "fusion": "跨域(拓扑×代数)",
                "result": knot_quick(),
                "note": "需拓扑数据输入"})

    # (7) 形式语言 × 熵率 —— 已知(ling 引擎已做)
    out.append({"cell": "形式语言 × 熵率", "fusion": "跨域(语言×信息论)",
                "result": {"禁bb正则": 0.481, "Dyck(无歧义CFG)": 1.0},
                "note": "**已知**: ling 引擎已验; 上界 log|Σ|"})

    # (8) 谱系树 × 信息熵 —— 树的形状熵
    def tree_entropy(n):
        import itertools
        # 标号树的度分布熵(Cayley: n^{n-2} 棵树)
        if n > 6:
            return None
        from collections import Counter
        # Prufer 序列枚举
        Hs = []
        for seq in itertools.product(range(n), repeat=max(0, n - 2)):
            deg = [1] * n
            for x in seq:
                deg[x] += 1
            cnt = Counter(deg)
            tot = sum(cnt.values())
            H = -sum((v / tot) * math.log2(v / tot) for v in cnt.values())
            Hs.append(H)
        return {"均值度熵": round(sum(Hs) / len(Hs), 4), "n": n,
                "树数": len(Hs)}

    out.append({"cell": "谱系树 × 香农熵", "fusion": "跨域(生物×信息论)",
                "result": tree_entropy(6),
                "note": "标号树的度分布熵; 机器可枚举(Prufer)"})

    return out


def main():
    t0 = time.time()
    print("=" * 100)
    print("侧向矩阵大扫描 —— 对象池 × 方法池")
    print("=" * 100)
    n_o, n_m = len(OBJECTS), len(METHODS)
    print(f"  对象池: {n_o} 个(跨 {len(set(v[0] for v in OBJECTS.values()))} 域)")
    print(f"  方法池: {n_m} 个(跨 {len(set(v[0] for v in METHODS.values()))} 域)")
    print(f"  矩阵:   {n_o} × {n_m} = **{n_o*n_m}** 格")

    rows = build_matrix()
    from collections import Counter
    fus = Counter(r["fusion"].split("(")[0] for r in rows)
    print(f"\n  融合分布: 同域 {fus['同域']} 格 / **跨域(融合) {fus['跨域']} 格**")
    comp = Counter(r["computable"] for r in rows)
    print(f"  可算性:   可算 {comp['可算']} / 需建模 {comp['需建模']} / 未知 {comp['未知']}")

    # 跨域且可算的格 —— 机器现在就打得动的
    hot = [r for r in rows if r["fusion"].startswith("跨域") and r["computable"] == "可算"]
    print(f"\n  **跨域且可算(机器现在就能打) = {len(hot)} 格**")

    print("\n" + "=" * 100)
    print("跨域且可算的格 —— 按 (对象域 × 方法域) 汇总")
    print("=" * 100)
    pair = Counter((r["obj_field"], r["method_field"]) for r in hot)
    for (of, mf), c in pair.most_common(20):
        print(f"  {of:<8}× {mf:<8}{c:>4} 格")

    print("\n" + "=" * 100)
    print("实测: 真算几个跨域格（不能只画表）")
    print("=" * 100)
    samp = compute_sample()
    for s in samp:
        print(f"\n  ▸ {s['cell']}   [{s['fusion']}]")
        print(f"    结果: {json.dumps(s['result'], ensure_ascii=False)[:110]}")
        print(f"    判读: {s['note'][:100]}")

    print("\n" + "=" * 100)
    print("树加深: L0 → L7")
    print("=" * 100)
    for k, (name, ask) in LAYERS_V2.items():
        nxt = ASCEND_V2.get(k, (None, ""))[0] or "—"
        print(f"  {name:<10}{ask:<52}→ {nxt}")
    print("\n  L6(元层) 与 L7(迁移) 是**新增的两层**, 原树只到 L5。")
    print("  L6: 不问'答案是什么', 问'**答案的集合**长什么样'(解空间的结构)")
    print("  L7: 不问'这个对象如何', 问'结论能否**搬到**同方法的其他对象'")

    print(f"\n扫描耗时 {time.time()-t0:.1f}s")
    print("\n诚实: 矩阵是**候选生成器**, 不是结论。每格还须过文献门; 本文件只做可算性判定。")
    out = HERE / "out/demo/lateral_scan.json"
    out.write_text(json.dumps({
        "objects": {k: v for k, v in OBJECTS.items()},
        "methods": {k: v for k, v in METHODS.items()},
        "matrix": rows, "sample_computed": samp,
        "layers": {k: v for k, v in LAYERS_V2.items()},
        "stats": {"cells": len(rows), "cross": fus["跨域"], "same": fus["同域"],
                  "hot": len(hot), "computable": comp["可算"]},
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"已存 {out}")


if __name__ == "__main__":
    main()
