# -*- coding: utf-8 -*-
"""direction_engine.py — 方向级组合引擎 v0 (P2.2):
  "L3 方向的典型问法模板" x "载体(对象/算子/参数族)" 自动实例化并数值判定。
  v0 覆盖: 分布偏置 / 表示阈值 / 间隙纪录 / 动力收敛 —— 每类一个数值探针, 产出已判 ProblemRecord。
"""
import math
from .judges_math import sieve
from .model import ProblemRecord, TreeRoot

ROOT = TreeRoot("R_dir", "方向级组合引擎 v0: 方向模板 × 载体", "数学",
                ["L3方向模板", "对象载体", "数值判定路由"], "研究方向的'典型问法'套到具体对象上会判出什么?")


def run(N: int = 400000, gapN: int = 200000):
    ps = sieve(N)
    primes = [i for i in range(2, N) if ps[i]]
    primes_gap = [i for i in range(2, gapN) if ps[i]]
    oddcomp = [x for x in range(9, N, 2) if not ps[x]]
    oc = set(oddcomp)
    out = []

    def add(id_, seed, motifs, template, binds, stmt, judgement, status, tag, edge=None):
        out.append(ProblemRecord(id_, "数学", seed, motifs, template, stmt, judgement,
                                 status=status, honesty=tag, binds=binds,
                                 tree={"parent": ROOT.id, "edge": edge or template}))

    # D1 方向: 数论-分布与均匀性 x 载体 质数 mod m
    dev = []
    for m in range(5, 32):
        if m % 2 == 0 or m % 3 == 0:
            continue
        cnt = [0] * m
        tot = 0
        for p in primes:
            if p <= m:
                continue
            cnt[p % m] += 1
            tot += 1
        cop = [r for r in range(m) if math.gcd(r, m) == 1]
        expect = tot / len(cop)
        maxd = max(abs(cnt[r] - expect) for r in cop) if cop else 0
        dev.append((m, round(maxd / expect, 3)))
    m0, r0 = max(dev, key=lambda x: x[1])
    add("D1", "质数在模 m 各互素余类是否均匀? (分布方向 × 质数)",
        ["分布与均匀性(数论-L3)", "质数(载体)", "模m(算子)"],
        "方向模板: 分布-均匀性 × 载体 质数",
        {"载体": "质数", "算子": "mod m", "m范围": "5..31"},
        f"质数 mod m 的互素类最大相对偏差(模 m={m0})",
        {"method": "计数+偏差", "m": m0, "rel_dev": r0, "sample": dev[:6]},
        "真(实测纪录)", "已知理论(Dirichlet均匀) 的数值复核; 偏差细分布需查证",
        "分布方向 × 质数模类")
    # D2 方向: 数论-表示计数 x 载体 奇合数+奇合数(阈值)
    f = []
    for n in range(6, N + 1, 2):
        if not any(a < n and (n - a) in oc for a in oddcomp):
            f.append(n)
    th = (max(f) + 2) if f else 6
    add("D2", "每个足够大的偶数 = 两个奇合数之和? (表示方向 × 奇合数)",
        ["表示计数(数论-L3)", "奇合数(载体)", "两项和(规则)"],
        "方向模板: 表示-覆盖阈值 × 载体 奇合数",
        {"载体": "奇合数", "上界": N},
        f"所有 ≥{th} 的偶数是两个奇合数之和(反例集 {f[:10]})",
        {"method": "覆盖扫描", "threshold": th, "fails_head": f[:10], "scan": N},
        f"真(阈值{th}, 验证到{N})", "已知-小定理(文献大概率已有)",
        "表示方向 × 奇合数")
    # D3 方向: 数论-间隙与纪录 x 载体 质数间隙(Cramér 比值)
    best = (0, 0, 0.0)
    for i in range(len(primes_gap) - 1):
        p = primes_gap[i]
        g = primes_gap[i + 1] - p
        if p > 3:
            r = g / (math.log(p) ** 2)
            if r > best[2]:
                best = (p, g, round(r, 4))
    add("D3", "质数间隙相对 (log p)² 的纪录(间隙方向 × 质数)",
        ["间隙与纪录(数论-L3)", "质数(载体)", "尺度分析(L2)"],
        "方向模板: 间隙-纪录 × 载体 质数",
        {"载体": "质数", "上界": gapN},
        f"≤{gapN} 的质数间隙/log²p 纪录在 p={best[0]} (间隙 {best[1]}, 比值 {best[2]})",
        {"method": "纪录扫描", "best": best, "scan": gapN},
        "真(纪录) + 上界开放", "已知(Cramér 猜想开放; 上界 O(log²p) 已证)",
        "间隙方向 × 质数")
    # D4 方向: 动力-收敛与周期 x 载体 3n+k 族
    res4 = {}
    for k in range(1, 8):
        esc = cyc = 0
        for start in range(2, 4001):
            x = start
            seen = {}
            steps = 0
            while steps < 300:
                if x == 1:
                    break
                if x > 500000:
                    esc += 1
                    break
                if x in seen:
                    clen = len(seen) - seen[x]
                    if clen not in (1, 2):
                        cyc += 1
                    break
                seen[x] = steps
                x = 3 * x + k if x % 2 else x // 2
                steps += 1
            else:
                esc += 1
        res4[k] = {"escape": esc, "nontrivial_cycles": cyc}
    evenk = {k: v for k, v in res4.items() if k % 2 == 0}
    add("D4", "3n+k 映射族: 哪些 k 让奇数全部逃逸?(收敛方向 × 递推族)",
        ["收敛与周期(动力-L3)", "3n+k 递推(载体)", "参数族(变异)"],
        "方向模板: 动力-收敛/周期 × 载体 3n+k",
        {"k": "1..7", "起始": "2..4000"},
        f"3n+k: k 偶数 ⇒ 奇数恒奇(3·奇+k=奇)必然逃逸; 数值逃逸数 {evenk}",
        {"method": "迭代扫描", "per_k": res4},
        "真(结构论证+数值验证)", "已知-易证(偶k恒奇); 奇k的环结构属 3n+k 文献",
        "收敛方向 × 3n+k")
    return [ROOT], out
