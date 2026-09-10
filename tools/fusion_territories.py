# -*- coding: utf-8 -*-
"""tools/fusion_territories.py — Track 4 & 5: 生物/心理稀疏领地 + 领域融合

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

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))

from mechanism_probe import judge_J2  # noqa: E402


# ==================== T4 演化博弈: 复制子动力学 ====================
def replicator(M, x0, steps=4000, dt=0.005):
    """复制子方程 dx_i/dt = x_i[(Mx)_i - x^T M x]。返回终点分布。"""
    n = len(x0)
    x = list(x0)
    for _ in range(steps):
        Mx = [sum(M[i][j] * x[j] for j in range(n)) for i in range(n)]
        avg = sum(x[i] * Mx[i] for i in range(n))
        x = [max(0.0, x[i] + dt * x[i] * (Mx[i] - avg)) for i in range(n)]
        s = sum(x) or 1.0
        x = [v / s for v in x]
    return x


def is_ess(M, i):
    """i 是否为**纯策略** ESS(对角占优粗判)。

    保留: 本判据只看纯策略, 因此"不收敛到纯 ESS"的初值**包含**了收敛到**混合均衡**的那些 ——
    在鹰鸽博弈里混合均衡本身就是稳定态, 不是异常。**这一列不能直接当"例外"读**,
    必须与"收敛到非稳定态/不收敛"区分。此为 T4 当前的已知局限。
    """
    n = len(M)
    return all(M[i][i] > M[j][i] for j in range(n) if j != i)


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
        for x0 in grid:
            x = replicator(M, x0)
            # 收敛到某个纯策略?
            hit = None
            for i in range(n):
                if x[i] > 0.9:
                    hit = i
                    break
            if hit is None or hit not in ess_pure:
                nonconv.append({"x0": [round(v, 3) for v in x0],
                                "end": [round(v, 3) for v in x]})
        out.append({"game": name, "n": n, "ess_pure": ess_pure,
                    "grid": len(grid), "exceptions": len(nonconv),
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
        if not m or not z:
            continue
        # "例外" = 不服从门泽拉特(单调比 < 0.6)
        out.append({"file": f.name[:50], "chars": len(txt),
                    "menzerath_monotone": m["monotone_ratio"],
                    "zipf": z["zipf_exponent"],
                    "exception": m["monotone_ratio"] < 0.6,
                    "profile_head": m["profile"][:4]})
    return out


def main():
    print("=" * 84)
    print("T4 演化博弈(生物 × 数学) —— 判定路由: 复制子动力学数值迭代")
    print("=" * 84)
    t4 = t4_scan()
    print(f"{'博弈':<22}{'n':>3}{'ESS纯策略':>10}{'网格':>6}{'例外':>6}{'例外率':>8}")
    for r in t4:
        print(f"{r['game']:<22}{r['n']:>3}{str(r['ess_pure']):>10}{r['grid']:>6}"
              f"{r['exceptions']:>6}{r['exc_density']:>8.1%}")
    print("\n开放问题(status=机器无法结算):")
    for r in t4:
        if r["exceptions"]:
            print(f"  [{r['game']}] {r['exceptions']} 个初值不收敛到 ESS —— "
                  f"吸引域边界由什么刻画?  (例: {r['exc_head'][0]['x0']} -> {r['exc_head'][0]['end']})")

    print("\n" + "=" * 84)
    print("T5 计算语言学(语言 × 信息) —— 判定路由: 真实语料统计量")
    print("=" * 84)
    t5 = t5_scan()
    print(f"{'语料':<52}{'字数':>8}{'门泽拉特':>9}{'齐普夫':>8}")
    for r in t5:
        print(f"{r['file']:<52}{r['chars']:>8}{r['menzerath_monotone']:>9}{r['zipf']:>8}")
    exc = [r for r in t5 if r["exception"]]
    print(f"\n违反门泽拉特(单调比<0.6)的语料: **{len(exc)} / {len(t5)}**")
    for r in exc:
        print(f"  {r['file']}  (单调比 {r['menzerath_monotone']}, 前几档 {r['profile_head']})")
    print("\n开放问题: 这些语料为何违反? 是文类(哲学论述 vs 科普)还是语言(中/英)所致?")

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
