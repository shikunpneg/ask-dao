# -*- coding: utf-8 -*-
"""tools/tri_verifiers.py — 真三域验证器(去名义化)

纪律(来自 03_NEXT_STEPS A1 验收标准):
  每个三域候选必须有独立仿真/数值结果, **且结果随第三域参数变化**。
  只把第三域"挂在句尾"的候选是名义三域 -> 一律判为 nominal, 不计入真三域。

每个验证器签名: f(theta) -> dict, 其中 theta 是**第三域的参数**。
输出必须含 "outputs": [数值...] 供敏感性检验(扰动 theta 看输出是否变化)。
"""
import math

# ---------- 工具 ----------

def _H2(p):
    """二值分布熵(bit)"""
    if p <= 0 or p >= 1:
        return 0.0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)


def _bsc_capacity(eps):
    """BSC(eps) 容量(bit/符号)"""
    if eps <= 0 or eps >= 1:
        return 1.0 if eps <= 0 else 0.0
    return 1 - _H2(eps)


def _bisect(f, lo, hi, iters=200):
    for _ in range(iters):
        mid = (lo + hi) / 2
        if f(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ---------- A. 生物选择 × 数学递推 × 信息熵下界 ----------
def v_bio_math_info(h_min):
    """选择迭代(生物) x 递推不动点(数学) x 熵下界(信息)
    命题: 等位基因频率在纯选择下固定(p->1, H->0);
          若环境要求多样性下界 H(p)>=h_min, 约束不动点 p* 落在 H(p*)=h_min 边界,
          且存在可行性阈值 h_min<=1bit(单一位点最大熵)。
    第三域参数: h_min(熵下界)。
    """
    s = 0.3  # 选择系数(生物)
    p = 0.2
    for _ in range(5000):
        w = 1 + s
        p = p * w / (p * w + (1 - p))
    p_unconstrained = p  # 纯选择不动点

    h_max = _H2(0.5)  # 1.0 bit
    feasible = h_min <= h_max
    if not feasible:
        return {"feasible": False, "h_min": h_min, "p_star": None,
                "p_unconstrained": round(p_unconstrained, 4),
                "note": "h_min 超过单一位点最大熵 1bit -> 约束不可行",
                "outputs": [0.0, 0.0]}
    # H(p) 在 p∈[0.5,1] 单调递减, 求 H(p)=h_min 的解
    p_star = _bisect(lambda x: _H2(x) - h_min, 0.5, 1 - 1e-12)
    return {"feasible": True, "h_min": h_min,
            "p_star": round(p_star, 4),
            "p_unconstrained": round(p_unconstrained, 4),
            "H_at_star": round(_H2(p_star), 4),
            "outputs": [p_star, p_unconstrained]}


# ---------- B. 语言文法 × 工程冗余 × 信息信道 ----------
def v_lang_eng_info(r):
    """文法熵率(语言) x 冗余设计(工程) x 含噪信道容量(信息)
    命题: 源熵率 H_s 经冗余率 r 后有效率 H_s/(1+r);
          可靠传输要求 H_s/(1+r) <= C(eps); 存在最小冗余阈值 r* = H_s/C - 1。
    第三域参数: r(冗余率, 工程)。
    """
    H_s = 1.0            # Dyck 型无歧义文法达字母表上界 1 bit/符号(语言)
    eps = 0.10           # 信道误码率(信息)
    C = _bsc_capacity(eps)
    eff = H_s / (1 + r)
    reliable = eff <= C
    r_star = H_s / C - 1  # 最小冗余
    return {"r": r, "effective_rate": round(eff, 4), "capacity": round(C, 4),
            "reliable": reliable, "r_star": round(r_star, 4),
            "outputs": [eff, float(reliable)]}


# ---------- C. 心理信念修正 × 数学迭代 × 信息信道 ----------
def _belief_T(q_true, q_hat, T, seed):
    import random
    rnd = random.Random(seed)
    p = 0.5
    for _ in range(T):
        bit = 1 if rnd.random() < q_true else 0
        lik1 = q_hat if bit == 1 else (1 - q_hat)
        lik0 = (1 - q_hat) if bit == 1 else q_hat
        den = lik1 * p + lik0 * (1 - p)
        p = lik1 * p / den if den else p
    return p


def v_psy_math_info(q_hat):
    """信念修正(心理) x 迭代(数学) x 含噪信道(信息)
    命题: 有限证据 T 下, 信念后验受建模者假定的信道质量 q_hat 支配;
          存在临界样本量 T*(q_hat): T>T* 后真值主导, 偏差<0.01。
          q_hat=0.5(假定纯噪声) => 永不学习, T*=inf。
    第三域参数: q_hat(建模者假定的信道质量)。
    """
    q_true = 0.70
    T0 = 10
    seeds = (1, 2, 3, 4, 5)
    post = sum(_belief_T(q_true, q_hat, T0, s) for s in seeds) / len(seeds)
    # 临界样本量: 偏差(1-p) < 0.01
    T_star = None
    if q_hat > 0.5:
        for T in (10, 20, 40, 80, 160, 320, 640, 1280):
            pavg = sum(_belief_T(q_true, q_hat, T, s) for s in seeds) / len(seeds)
            if 1 - pavg < 0.01:
                T_star = T
                break
    return {"q_hat": q_hat, "T": T0, "posterior": round(post, 4),
            "bias": round(1 - post, 4),
            "capacity_true": round(_bsc_capacity(q_true), 4),
            "T_star": T_star if T_star is not None else float("inf"),
            "outputs": [post, float(T_star) if T_star is not None else 9999.0]}


# ---------- D. 物理对称 × 数学极值 × 信息熵 ----------
def v_phys_math_info(n):
    """离散对称(物理) x 极值/计数(数学) x 最大熵(信息)
    命题: n 位微观态在 Z_n 轮换对称约束下, 最大熵分布均匀于轮换轨道;
          可达熵 = log2(轨道数) = log2(Burnside 计数) = log2((1/n)Σ φ(d) 2^{n/d}),
          对称约束的熵代价 ≈ log2(n) bit(相对于无约束的 n bit)。
    第三域参数: n(对称群阶)。
    """
    def phi(k):
        res, m = k, k
        d = 2
        while d * d <= m:
            if m % d == 0:
                while m % d == 0:
                    m //= d
                res -= res // d
            d += 1
        if m > 1:
            res -= res // m
        return res

    orbits = sum(phi(d) * 2 ** (n // d) for d in range(1, n + 1) if n % d == 0) / n
    H = math.log2(orbits)
    cost = n - H  # 对称约束的熵代价
    return {"n": n, "orbits": round(orbits, 2), "entropy_bit": round(H, 4),
            "unconstrained_bit": float(n), "symmetry_cost_bit": round(cost, 4),
            "outputs": [H, cost]}


# ---------- 注册表: (域三元组) -> (验证器, 第三域参数名, 参数网格) ----------
TRI_REGISTRY = {
    ("生物", "数学", "信息"): {
        "fn": v_bio_math_info, "third": "信息", "param": "h_min",
        "grid": [0.1, 0.3, 0.6, 0.9, 1.2],
        "obj": "等位基因频率的熵约束不动点 p*",
        "quant": "熵下界 h_min ∈ (0,1.2] bit",
        "crit": "约束不动点 p* 的位置与可行性阈值(h_min>1bit 不可行)",
        "statement": "纯选择把等位基因频率推向固定(H→0); 若环境要求多样性下界 H(p)≥h_min, "
                     "约束不动点 p* 是否落在 H(p*)=h_min 边界, 可行性阈值是否为 1 bit?",
    },
    ("语言", "工程", "信息"): {
        "fn": v_lang_eng_info, "third": "工程", "param": "r",
        "grid": [0.0, 0.1, 0.2, 0.5, 1.0],
        "obj": "冗余率 r 下的有效源熵率 H_s/(1+r)",
        "quant": "冗余率 r ∈ [0,1], 信道误码 eps=0.10",
        "crit": "可靠传输判据 H_s/(1+r)≤C(eps) 与最小冗余阈值 r*",
        "statement": "文法熵率 H_s 的源经冗余率 r 编码后, 有效率 H_s/(1+r) 可靠传输的条件; "
                     "最小冗余阈值 r* 如何随信道误码率与源熵率变化?",
    },
    ("心理", "数学", "信息"): {
        "fn": v_psy_math_info, "third": "信息", "param": "q_hat",
        "grid": [0.55, 0.65, 0.70, 0.80, 0.90],
        "obj": "有限证据下信念后验的偏差与临界样本量 T*",
        "quant": "建模信道质量 q_hat ∈ [0.55,0.90], 真信道 q=0.70, T=10",
        "crit": "后验偏差 |1-p| 与临界样本量 T*(偏差<0.01 所需证据量)",
        "statement": "信念修正迭代在真实信道 q=0.70 下, 若建模者假定 q_hat≠q, "
                     "有限证据下的后验偏差与临界样本量 T* 如何随 q_hat 变化?",
    },
    ("物理", "数学", "信息"): {
        "fn": v_phys_math_info, "third": "物理", "param": "n",
        "grid": [4, 6, 8, 10, 12],
        "obj": "轮换对称约束下的最大熵分布",
        "quant": "对称群阶 n ∈ {4,6,8,10,12}",
        "crit": "可达熵 log2(轨道数) 与对称约束的熵代价 n-H",
        "statement": "n 位微观态在 Z_n 轮换对称约束下最大熵分布的轨道数; "
                     "对称约束的熵代价是否 ≈ log2(n) bit?",
    },
}


def sensitivity(entry, tol=1e-9):
    """跑第三域参数网格, 判定输出是否随第三域参数变化。
    返回 (is_sensitive, table)。"""
    fn = entry["fn"]
    table = []
    for th in entry["grid"]:
        res = fn(th)
        table.append({"theta": th, "outputs": res.get("outputs", []), "res": res})
    outs = [t["outputs"] for t in table]
    changed = any(any(abs(a - b) > tol for a, b in zip(outs[0], o)) for o in outs[1:])
    return changed, table


if __name__ == "__main__":
    for key, entry in TRI_REGISTRY.items():
        ok, table = sensitivity(entry)
        print(f"{key} 第三域={entry['third']} 参数={entry['param']} 敏感性={ok}")
        for t in table:
            print(f"   {entry['param']}={t['theta']:<6} outputs={[round(x,4) for x in t['outputs']]}")
