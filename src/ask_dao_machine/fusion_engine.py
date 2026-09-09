# -*- coding: utf-8 -*-
"""fusion_engine.py — 跨域融合实验室(真判定版):
  把'别域母题'(信息度量/动力学机制) 组合到 数学对象(质数/因子和/间隙)上,
  生成可被数值判定的交叉候选 —— 不是填槽演示, 是带出处链的真判定记录。
  无法当场判定的域(生物/认知/物理实验) 仍走 judge_blueprints(前问题态)。
"""
import math
from .judges_math import sieve
from .model import ProblemRecord, TreeRoot

ROOT = TreeRoot("R_fusion", "跨域融合实验室: 别域母题 × 数学对象(可数值判定)", "数学",
                ["信息-熵/均匀性", "动力学-随机游走", "质数", "因子和"], "把别域的'眼睛'放到数学对象上会看到什么?")


def run(N: int = 1000000, gapN: int = 300000):
    ps = sieve(N)
    primes = [i for i in range(2, N) if ps[i]]
    primes_gap = [i for i in range(2, gapN) if ps[i]]
    out = []

    def add(id_, seed, motifs, template, binds, stmt, judgement, status, tag, edge=None):
        out.append(ProblemRecord(id_, "数学", seed, motifs, template, stmt, judgement,
                                 status=status, honesty=tag, binds=binds,
                                 tree={"parent": ROOT.id, "edge": edge or template}))

    # ============ F1: 信息母题(熵/均匀性) × 质数对象(余数分布) ============
    # 对模 m, 统计 p mod m 的计数 -> 信息熵 H 与均匀熵 log m 的差 / 最大偏差
    devs = []
    ent_note = {}
    for m in range(3, 41):
        if m % 2 == 0 or m % 3 == 0:
            continue  # 平凡偏置(与 2/3 同余可整除), 剔除
        cnt = [0] * m
        tot = 0
        for p in primes:
            if p <= m:
                continue  # 小质数(<m)不进统计, 避免 p mod m 覆盖小类
            cnt[p % m] += 1
            tot += 1
        if tot == 0:
            continue
        # 只在互素余类(与 m 互质)内评估均匀性
        cop = [r for r in range(m) if math.gcd(r, m) == 1]
        expect = tot / len(cop)
        H = 0.0
        for r in cop:
            c = cnt[r]
            q = c / tot
            H -= q * math.log(q)
        maxdev = max(abs(cnt[r] - expect) for r in cop)
        devs.append((m, round(H, 3), round(maxdev, 1), round(maxdev / expect, 3)))
    m_big = max(devs, key=lambda x: x[2])
    add("F1", "用'信息熵'看质数: 质数在模 m 的余数分布有多接近均匀?",
        ["质数", "信息-熵/均匀性"], "跨域模板F1: 信息度量 × 质数余数分布",
        {"模": "3..40", "质数上限": N}, f"质数 mod m 的分布: 均匀熵 log m vs 实测熵(最大偏差在 m={m_big[0]})",
        {"method": "计数+熵/偏差", "range": f"质数≤{N}, m=3..40",
         "max_bias_mod": m_big[0], "max_bias_ratio": round(m_big[3], 3),
         "sample": devs[:5]},
        "真(实测纪录) + 已知理论: Dirichlet 均匀(强形式); 小模偏置=Chebyshev 类",
        "已知-著名(均匀性定理); 偏差细刻画需查证",
        "模3..40 熵-偏差表(纪录)")

    # Chebyshev 偏置具体化: 4k+1 vs 4k+3 质数
    c1 = c3 = 0
    for p in primes:
        if p <= 2:
            continue
        r = p % 4
        if r == 1:
            c1 += 1
        elif r == 3:
            c3 += 1
    add("F2", "质数更喜欢 4k+3 还是 4k+1? (同余偏置)",
        ["质数", "同余类", "信息-偏置"], "跨域模板F1b: 偏置符号统计",
        {"上限": N}, f"≤{N} 的质数中, 4k+1 与 4k+3 型的计数差(Chebyshev 偏置方向)",
        {"method": "计数", "range": f"≤{N}", "count_1mod4": c1, "count_3mod4": c3,
         "diff_3minus1": c3 - c1},
        "真(实测纪录)", "已知-著名(Chebyshev 偏置, 未证但普遍相信)",
        "4k+1 vs 4k+3 偏置")

    # ============ F2: 动力学母题(随机游走/纪录) × 质数间隙 ============
    gaps = [primes_gap[i + 1] - primes_gap[i] for i in range(len(primes_gap) - 1)]
    # 游走: 从0出发, 步长 = 间隙符号交替? 用间隙奇偶 -> ±1 随机游走
    walk = 0
    maxd = 0
    n_ret = 0
    pos_hist = {}
    for k, g in enumerate(gaps, 1):
        walk += 1 if g % 2 == 0 else -1  # 偶间隙 +1, 奇间隙 -1
        maxd = max(maxd, abs(walk))
        pos_hist[walk] = pos_hist.get(walk, 0) + 1
        if walk == 0:
            n_ret += 1
    add("F3", "把质数间隙的奇偶当随机游走的±1步, 轨迹会怎样?",
        ["质数", "随机游走(动力学)"], "跨域模板F2: 质数间隙奇偶 -> 游走",
        {"步数": len(gaps), "规则": "偶间隙+1/奇间隙-1"}, "质数间隙奇偶游走: 最大偏移与回到原点次数",
        {"method": "模拟", "steps": len(gaps), "max_displacement": maxd,
         "returns_to_zero": n_ret},
        "真(实测纪录); 模式是否普适=悬置", "纪录-需查证(模式问题)",
        "间隙奇偶游走纪录")

    # 纪录间隙 vs Cramér 比值
    best = (0, 0, 0.0)
    rec = []
    for i in range(len(primes_gap) - 1):
        p = primes_gap[i]
        g = primes_gap[i + 1] - p
        if p > 3:
            r = g / (math.log(p) ** 2)
            if r > best[2]:
                best = (p, g, r)
                rec.append((p, g, round(r, 3)))
    add("F4", "质数间隙相对 (log p)² 的纪录能多大? (Cramér 视角)",
        ["质数", "间隙", "尺度分析"], "跨域模板F3: 间隙/log²p 纪录",
        {"上限": gapN}, f"≤{gapN} 的质数间隙 / log²p 最大纪录(位置 p={best[0]}, 间隙 {best[1]})",
        {"method": "纪录扫描", "range": f"≤{gapN}", "best": best,
         "records_head": rec[:6]},
        "真(实测纪录) + 上界开放", "已知-著名(上界 O(log²p); Cramér 猜想未证)",
        "Cramér 比值纪录")
    return [ROOT], out
