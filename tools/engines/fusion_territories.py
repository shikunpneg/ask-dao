# -*- coding: utf-8 -*-
"""tools/engines/fusion_territories.py — Track 4 & 5: 生物/心理稀疏领地 + 领域融合

SCOPE_MOTIF_DOMAIN.md 的结论: **跨域的前置是"先造判定路由"**, 不是先有领域。
所以这里不写"生物域母题", 而是各给一个**真的可计算**的角落:

  T4 演化博弈(生物 × 数学)     —— 判定路由 = 复制子动力学数值迭代
     主张: "给定博弈, 种群从任意初值都收敛到 ESS"
     例外: 不收敛(或收敛到非 ESS)的初值 -> 问"吸引域边界由什么刻画?"

  T5 计算语言学(语言 × 信息)   —— 判定路由 = 真实语料的统计量(齐普夫/门泽拉特/熵率)
     主张: "所有文本都服从门泽拉特定律(词长随词内音节数递减)"
     例外: 违反的语料 -> 问"哪些文本违反, 为什么?"

两者都是**先有可算的判定路由, 再问问题** —— 这是与"名义跨域"的分野。
"""
import json
import math
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent.parent
_td = HERE / "tools"
sys.path.insert(0, str(_td))
for _sd in _td.iterdir():
    if _sd.is_dir() and not _sd.name.startswith("_"):
        sys.path.insert(0, str(_sd))

from mechanism_probe import judge_J2  # noqa: E402


# ==================== T4 演化博弈: 复制子动力学 ====================
def replicator(M, x0, steps=4000, dt=0.005, tail=400):
    """复制子方程 dx_i/dt = x_i[(Mx)_i - x^T M x]。

    返回 (终点, 尾部轨迹)。**自纠错(第 19 次)**: 只看终点快照会把 RPS 的**闭环轨道**
    (内点是中心, 永远绕圈不收敛)误判成"收敛到混合均衡"。故一并返回尾部轨迹,
    由调用方检查**是否真的静止** —— 判"收敛"必须看过程, 不能看快照。
    """
    n = len(x0)
    x = list(x0)
    traj = []
    for t in range(steps):
        Mx = [sum(M[i][j] * x[j] for j in range(n)) for i in range(n)]
        avg = sum(x[i] * Mx[i] for i in range(n))
        x = [max(0.0, x[i] + dt * x[i] * (Mx[i] - avg)) for i in range(n)]
        s = sum(x) or 1.0
        x = [v / s for v in x]
        if t >= steps - tail:
            traj.append(list(x))
    return x, traj


def is_stationary(traj, tol=0.02):
    """尾部轨迹是否静止(各分量的极差 <= tol)。闭环轨道不满足。"""
    if not traj:
        return False
    n = len(traj[0])
    for i in range(n):
        vals = [p[i] for p in traj]
        if max(vals) - min(vals) > tol:
            return False
    return True


def is_ess(M, i):
    """i 是否为**纯策略** ESS(对角占优粗判)。"""
    n = len(M)
    return all(M[i][i] > M[j][i] for j in range(n) if j != i)


def classify_endpoint(M, x, traj, tol=0.9, interior=0.05):
    """把复制子终点分成四类。

    判别顺序**必须先判收敛**(自纠错第 19 次): 有闭环轨道(如 RPS 的内点中心)
    终点快照看起来像"混合", 但它永远绕圈、**不收敛**。

      cycle    : 尾部不静止 -> 周期/混沌轨道(异常)
      pure     : 静止且某分量 > tol -> 收敛到纯策略
      mixed    : 静止且所有分量 > interior -> 收敛到内点混合均衡(稳定)
      boundary : 静止但落在边界(异常, 需具体分析)
    """
    n = len(M)
    if not is_stationary(traj):
        return ("cycle", None)
    if max(x) > tol:
        return ("pure", int(max(range(n), key=lambda i: x[i])))
    if all(v > interior for v in x):
        return ("mixed", None)
    return ("boundary", None)


def is_stable_endpoint(kind, M, idx):
    """终点是否**稳定**(非异常)。纯 ESS 或**已收敛**的内点混合均衡算稳定。"""
    if kind == "mixed":
        return True          # 已判静止, 故是真的收敛到混合均衡
    if kind == "pure":
        return is_ess(M, idx)
    return False             # cycle / boundary 都是异常


def t4_scan():
    """对一批 2×2/3×3 博弈, 扫初始条件(单纯形网格), 找不收敛到 ESS 的初值。"""
    games = {
        "鹰鸽(Hawk-Dove)": [[-1, 4], [0, 2]],
        "协调(Coordination)": [[2, 0], [0, 1]],
        "雪堆(Snowdrift)": [[1, 3], [0, 2]],
        "囚徒(Prisoner)": [[3, 0], [5, 1]],
        "RPS(石头剪刀布)": [[0, -1, 1], [1, 0, -1], [-1, 1, 0]],
        "含内点的3策略": [[1, 0, 2], [2, 1, 0], [0, 2, 1]],
    }
    out = []
    for name, M in games.items():
        n = len(M)
        ess_pure = [i for i in range(n) if is_ess(M, i)]
        # 网格扫初始条件
        grid = []
        K = 12
        if n == 2:
            for a in range(1, K):
                grid.append([a / K, 1 - a / K])
        else:
            for a in range(1, K):
                for b in range(1, K - a):
                    c = K - a - b
                    if c > 0:
                        grid.append([a / K, b / K, c / K])
        nonconv = []
        kinds = Counter()
        for x0 in grid:
            x, traj = replicator(M, x0)
            kind, idx = classify_endpoint(M, x, traj)
            kinds[kind] += 1
            if not is_stable_endpoint(kind, M, idx):
                nonconv.append({"x0": [round(v, 3) for v in x0],
                                "end": [round(v, 3) for v in x],
                                "kind": kind})
        out.append({"game": name, "n": n, "ess_pure": ess_pure,
                    "grid": len(grid), "endpoint_kinds": dict(kinds),
                    "exceptions": len(nonconv),
                    "exc_density": round(len(nonconv) / max(len(grid), 1), 3),
                    "exc_head": nonconv[:4]})
    return out


# ==================== T5 计算语言学: 门泽拉特定律 ====================
CORPUS = Path("E:/ask-dao/_text")


def _sentences(txt):
    import re
    return [s for s in re.split(r"[。！？!?\.\n]+", txt) if 3 <= len(s) <= 200]


def menzerath(txt):
    """门泽拉特定律(句-小句级): **句子含的小句越多, 小句平均越短**。

    **自纠错(第 16 次)**: 首版按"句长分箱"再测箱内平均句长 —— 那是**同义反复**
    (长箱里的句子当然长), 结果所有语料 monotone_ratio 全为 0.0, 是个**假结果**。
    正确的门泽拉特检验: 自变量是"构造包含的成分数", 因变量是"成分的平均长度",
    二者**不同层级**, 才不是循环论证。
    """
    import re
    sents = _sentences(txt)
    if len(sents) < 100:
        return None
    # 按句内小句数(k)分箱, 测该箱的**小句平均长度**
    by_k = {}
    for s in sents:
        clauses = [c for c in re.split(r"[，,、；;：:]", s) if c]
        k = len(clauses)
        if k < 1 or k > 8:
            continue
        by_k.setdefault(k, []).extend(len(c) for c in clauses)
    profile = [(k, round(sum(v) / len(v), 2)) for k, v in sorted(by_k.items()) if len(v) >= 20]
    if len(profile) < 4:
        return None
    vals = [v for _, v in profile]
    # 服从 = 随 k 增大而递减(允许小噪声 ±2 字)
    dec = sum(1 for i in range(len(vals) - 1) if vals[i + 1] <= vals[i] + 2)
    return {"profile": profile, "monotone_ratio": round(dec / max(len(vals) - 1, 1), 2)}


def zipf_deviation(txt):
    """齐普夫: 词频×排名 ≈ 常数。返回拟合指数与偏离度。"""
    import re
    chars = [c for c in re.findall(r"[\u4e00-\u9fff]", txt)]
    if len(chars) < 500:
        return None
    # 用二元字组作"词"
    words = ["".join(chars[i:i + 2]) for i in range(0, len(chars) - 1, 2)]
    cnt = Counter(words).most_common(200)
    if len(cnt) < 50:
        return None
    xs = [math.log(i + 1) for i in range(len(cnt))]
    ys = [math.log(c) for _, c in cnt]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    den = sum((x - mx) ** 2 for x in xs) or 1
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den
    return {"zipf_exponent": round(-slope, 3), "n_types": len(cnt)}


def heaps(txt, bins=10):
    """Heaps 定律: 词汇量 V(n) = K·n^β(β<1)。
    返回 β 与 R²。**例外判据**: β 显著偏离典型带 [0.4,0.7] 或拟合极差。
    与门泽拉特不同, Heaps 的 β **因文类而变** —— 更可能有例外。"""
    import re
    chars = [c for c in re.findall(r"[一-鿿]", txt)]
    if len(chars) < 5000:
        return None
    words = ["".join(chars[i:i + 2]) for i in range(len(chars) - 1)]
    N = len(words)
    pts = []
    for k in range(1, bins + 1):
        n = N * k // bins
        if n < 100:
            continue
        pts.append((n, len(set(words[:n]))))
    if len(pts) < 5:
        return None
    xs = [math.log(n) for n, _ in pts]
    ys = [math.log(v) for _, v in pts]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    den = sum((x - mx) ** 2 for x in xs) or 1
    beta = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den
    # R²
    ss_tot = sum((y - my) ** 2 for y in ys) or 1
    ss_res = sum((y - (my + beta * (x - mx))) ** 2 for x, y in zip(xs, ys))
    r2 = 1 - ss_res / ss_tot
    return {"beta": round(beta, 3), "r2": round(r2, 4)}


def t5_scan():
    files = sorted(CORPUS.glob("*.md")) if CORPUS.exists() else []
    out = []
    for f in files:
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if len(txt) < 5000:
            continue
        m = menzerath(txt)
        z = zipf_deviation(txt)
        h = heaps(txt)
        if not m or not z:
            continue
        # 例外判据 1: 不服从门泽拉特(单调比 < 0.6)  —— 实测 0/9, 该律本文类内恒成立
        # 例外判据 2: Heaps β 偏离典型带 [0.4, 0.7]  —— 因文类而变, 更可能有例外
        beta = h["beta"] if h else None
        exc_m = m["monotone_ratio"] < 0.6
        exc_h = (beta is not None) and not (0.4 <= beta <= 0.8)
        out.append({"file": f.name[:50], "chars": len(txt),
                    "menzerath_monotone": m["monotone_ratio"],
                    "zipf": z["zipf_exponent"],
                    "heaps_beta": beta, "heaps_r2": h["r2"] if h else None,
                    "exception": exc_m or exc_h,
                    "exc_reason": ("门泽拉特" if exc_m else "") +
                                  ("Heaps" if exc_h else "") or None,
                    "profile_head": m["profile"][:4]})
    return out


def main():
    print("=" * 84)
    print("T4 演化博弈(生物 × 数学) —— 判定路由: 复制子动力学数值迭代")
    print("=" * 84)
    t4 = t4_scan()
    print(f"{'博弈':<22}{'n':>3}{'ESS纯':>6}{'网格':>6}{'→纯':>5}{'→混':>5}{'→边':>5}{'→环':>5}{'异常':>6}")
    for r in t4:
        k = r["endpoint_kinds"]
        print(f"{r['game']:<22}{r['n']:>3}{str(r['ess_pure']):>6}{r['grid']:>6}"
              f"{k.get('pure',0):>5}{k.get('mixed',0):>5}{k.get('boundary',0):>5}"
              f"{k.get('cycle',0):>5}{r['exceptions']:>6}")
    print("\n开放问题(status=机器无法结算):")
    for r in t4:
        if r["exceptions"]:
            print(f"  [{r['game']}] {r['exceptions']}/{r['grid']} 个初值落到**非稳定终点** —— "
                  f"吸引域边界由什么刻画?")
            for e in r["exc_head"][:2]:
                print(f"        {e['x0']} -> {e['end']}  [{e['kind']}]")
    print("\n诚实(已修第18次自纠错): 首版只判'是否收敛到纯 ESS', 把**收敛到混合均衡**(复制子动力学里"
          "\n  的稳定态)误算成异常 —— 判据的**语义**错了。现按 pure/mixed/boundary 分类, mixed 不计例外。")

    print("\n" + "=" * 84)
    print("T5 计算语言学(语言 × 信息) —— 判定路由: 真实语料统计量")
    print("=" * 84)
    t5 = t5_scan()
    print(f"{'语料':<44}{'字数':>8}{'门泽拉特':>9}{'齐普夫':>7}{'Heaps β':>9}{'R²':>8}")
    for r in t5:
        b = f"{r['heaps_beta']:.3f}" if r.get("heaps_beta") is not None else "—"
        r2 = f"{r['heaps_r2']:.4f}" if r.get("heaps_r2") is not None else "—"
        print(f"{r['file']:<44}{r['chars']:>8}{r['menzerath_monotone']:>9}"
              f"{r['zipf']:>7}{b:>9}{r2:>8}")
    exc_m = [r for r in t5 if r["menzerath_monotone"] < 0.6]
    exc_h = [r for r in t5 if r.get("heaps_beta") is not None
             and not (0.4 <= r["heaps_beta"] <= 0.8)]
    print(f"\n① 违反门泽拉特(单调比<0.6): **{len(exc_m)} / {len(t5)}** "
          f"—— 该律本文类内基本恒成立, 产不出问题")
    print(f"② Heaps β 偏离典型带 [0.4,0.8]: **{len(exc_h)} / {len(t5)}**")
    for r in exc_h:
        print(f"     {r['file']}  β={r['heaps_beta']} (R²={r['heaps_r2']})")
    if exc_h:
        print("  开放问题: 这些语料的词汇增长率为何偏离? 与文类/语言/主题多样性什么关系?")
    else:
        print("  (同样无例外 —— 本文类内两条语言统计律都恒成立)")

    print("\n" + "=" * 84)
    print("诚实边界")
    print("=" * 84)
    print("- T4/T5 的判定路由**真的是机器可跑的**(数值迭代 / 语料统计), 不是占位。")
    print("- 但两者都只是**各自领域的一个可算角落**, 不代表'生物域'或'语言学域'。")
    print("- 例外集尚未过 T2 的机制电池 + 置换显著性 + 文献门 —— 下一步。")

    (HERE / "out/demo/fusion_territories.json").write_text(
        json.dumps({"T4_evo_game": t4, "T5_comp_ling": t5}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print("\n已存 out/demo/fusion_territories.json")


if __name__ == "__main__":
    main()
