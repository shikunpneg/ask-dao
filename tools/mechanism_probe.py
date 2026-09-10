# -*- coding: utf-8 -*-
"""tools/mechanism_probe.py — J2「机制追问」的**机器化**(LLM 裁判协议的核心必填项)

## 为什么需要它
`llm_judge_pass.py` 定的协议里, J2(机制)是**必填**: "例外集的结构能否用机器已有的原语解释?"
但 R32 的教训是 —— 当时那个 J2 答案(避开 QR mod 18)是**我在脑子里想到的**, 机器并没有自动去问。
**没被机器自动问的必填项 = 形同虚设。**

本模块把 J2 **机器化**: 对任何例外集, 自动跑一个**结构假设电池**, 返回所有能拟合的解释。
于是机器每次都必须"问一遍机制", 并把答案与**类库完备性**一起报告(R33 判据⑥)。

## 电池(每条都带实质性判据, 不许废话式拟合)
  E1 周期        : F 恰为某组模 m 剩余类
  E2 类包含      : F ⊆ C (|F\C| ≤ 3)
  E3 类规避      : F ∩ C = ∅ 且 |C|/区间 ≥ 10%   ← R33 新增, 正是揭穿 QR 的那类
  E4 二次剩余     : F 避开 / 含于 QR(m)          ← R33 新增
  E5 小界        : F ⊆ [lo, T], T ≤ hi/10
  E6 置换不变     : F 在数位置换下封闭(归约到数位多重集)
  E7 密度稳定     : 分窗密度尾部稳定(极限存在的证据)
  E8 两类并集     : F ⊆ C1 ∪ C2
  E9 两类交集     : C1 ∩ C2 ⊆ F
  E10 差分/比例   : F 的差分或比值序列命中某个具名类

返回按"解释力"排序; 全不拟合 ⇒ 机器确实解释不了(**这才是真信号**)。
"""
import sys
from itertools import combinations
from math import gcd
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src"))

MODS = (3, 4, 5, 6, 7, 8, 9, 10, 12, 16, 18, 24, 36)


def _qr(m):
    return sorted({(a * a) % m for a in range(m)})


def _classes(pool, lo, hi):
    """具名类(含模类与二次剩余), 供 E2/E3/E4/E8/E9 用"""
    out = dict(pool)
    for m in MODS:
        for r in range(m):
            out[f"≡{r}(mod {m})"] = {n for n in range(lo, hi + 1) if n % m == r}
        out[f"QR(mod {m})"] = {n for n in range(lo, hi + 1) if n % m in _qr(m)}
    return out


def _period_fit(F, lo, hi, mmax=72):
    fs = set(F)
    for m in range(2, mmax + 1):
        res = {x % m for x in F}
        if res and {n for n in range(lo, hi + 1) if n % m in res} == fs:
            return m, sorted(res)
    return None


def _density_windows(F, lo, hi, k=10):
    out, a = [], lo
    step = max(1, (hi - lo) // k)
    while a < hi:
        b = min(a + step, hi)
        tot = len(range(a, b)) or 1
        out.append(sum(1 for x in F if a <= x < b) / tot)
        a = b
    return out


def probe(F, lo, hi, pool, span_frac=0.10, eps=3, ns=None):
    """跑完整电池。返回 (explanations, unexplained_flag)。

    **自纠错(第 15 次)**: "覆盖率"的分母必须是**实际扫描域**, 不是全体整数。
    首版用 hi-lo+1, 于是 `F ⊆ ≡0(mod 4) ∪ ≡2(mod 4)`(就是"n 是偶数")算出 50% 覆盖率 ——
    但我们**只扫偶数**, 它实际覆盖 100% 扫描域, 又是个恒真式。
    """
    F = sorted(F)
    cls = _classes(pool, lo, hi)
    scan = sorted(ns) if ns is not None else list(range(lo, hi + 1))
    span = max(1, len(scan))
    scan_set = set(scan)
    def _cov(C):
        return len(C & scan_set) / span
    exps = []

    # E1 周期
    pf = _period_fit(F, lo, hi)
    if pf:
        exps.append({"E": "E1 周期", "detail": f"恰为模 {pf[0]} 的剩余类 {pf[1]}",
                     "strength": 1.0})

    # E2 类包含 / E3 类规避 / E4 二次剩余(由类名区分)
    # **自纠错(第 13 次)**: 首版无"实质性"下限, 于是把 `F ⊆ QR(3) ∪ ≡2(3)` 当成解释 ——
    # 但 QR(3)={0,1} 与 ≡2(3)={2} 的并集**就是全体整数**, 这是**恒真式, 解释了等于没解释**。
    # 判据: 一个解释若要算数, 其"覆盖空间"必须**明显小于全体**(否则先验概率≈1, 无信息量)。
    COVER_MAX = 0.60
    for name, C in sorted(cls.items()):
        cov = _cov(C)
        outside = [n for n in F if n not in C]
        if len(outside) <= eps:
            if cov <= COVER_MAX:
                exps.append({"E": "E2 类包含", "detail": f"F ⊆ {name}(该类覆盖 {cov:.0%})" +
                             (f" ∪ {outside}" if outside else ""),
                             "strength": round(1 - cov, 3), "coverage": round(cov, 3)})
            else:
                exps.append({"E": "E2' 弱包含(近乎恒真, 不计)", "detail":
                             f"F ⊆ {name} 但该类覆盖 {cov:.0%}(≥{COVER_MAX:.0%}) -> 无信息量",
                             "strength": 0.0, "vacuous": True})
        if F and 0.10 <= cov <= COVER_MAX and all(n not in C for n in F):
            tag = "E4 二次剩余" if name.startswith("QR(") else "E3 类规避"
            exps.append({"E": tag, "detail": f"F 与 {name} 不相交(该类覆盖 {cov:.0%})",
                         "strength": round(cov, 3), "coverage": round(cov, 3)})

    # E5 小界
    T = max(F) if F else 0
    if T <= hi // 10:
        exps.append({"E": "E5 小界", "detail": f"F 全部 < {T}(扫描上界 {hi})", "strength": 0.8})

    # E6 置换不变 / 数位多重集归约(抽样检验, 见 R28 perm_invariance)
    # **自纠错(第 14 次)**: 首版 `if len(d) > 6: continue` 使 base-2 下几乎所有数被跳过,
    # 于是"没找到反例"被报告成"置换不变" —— 又一个**空检查通过**(本项目反复出现的同一类错)。
    # 判据: 必须记录**实际检验次数**, 少于阈值不许下结论。
    def _perm_stable(base, min_tests=40):
        from itertools import permutations
        def to_base(n):
            d = []
            while n:
                d.append(n % base)
                n //= base
            return d or [0]
        def from_base(d):
            v = 0
            for x in reversed(d):
                v = v * base + x
            return v
        tested = 0
        for n in F[:60] + F[-60:]:
            d = to_base(n)
            if len(d) > 6:
                continue
            for p in set(permutations(d)):
                m = from_base(list(p))
                if m < lo or m > hi:
                    continue
                tested += 1
                if m not in Fs_ref:
                    return False, tested
        return (tested >= min_tests), tested

    Fs_ref = set(F)
    for b in (10, 2):
        stable, tested = _perm_stable(b)
        if stable:
            exps.append({"E": "E6 置换不变", "detail":
                         f"F 在 base-{b} 数位置换下封闭(实测 {tested} 次) ⇒ 归约到数位多重集",
                         "strength": 0.75, "tested": tested})
            break

    # E7 密度稳定
    d = _density_windows(F, lo, hi)
    tail = d[len(d) // 2:] or [0]
    if tail and (max(tail) - min(tail)) <= 0.01 and 0 < sum(tail) / len(tail) < 0.9:
        exps.append({"E": "E7 密度稳定", "detail":
                     f"尾部密度稳定在 {sum(tail)/len(tail):.4f}", "strength": 0.6})

    # E8 两类并集 / E9 两类交集 (只在候选中体量足够时试)
    big = [(n, C) for n, C in cls.items() if _cov(C) >= 0.05 and _cov(C) < 0.995]
    big.sort(key=lambda kv: -len(kv[1]))
    big = big[:24]
    Fs = set(F)
    best_union = None
    for (n1, C1), (n2, C2) in combinations(big, 2):
        U = C1 | C2
        cov = len(U & scan_set) / span
        if Fs <= U and cov <= 0.60:          # 同样要过实质性: 并集不得近乎全空间
            if best_union is None or cov < best_union[0]:
                best_union = (cov, n1, n2)
    if best_union:
        cov, n1, n2 = best_union
        exps.append({"E": "E8 两类并集", "detail": f"F ⊆ {n1} ∪ {n2}(并集覆盖 {cov:.0%})",
                     "strength": round(1 - cov, 3), "coverage": round(cov, 3)})
    for (n1, C1), (n2, C2) in combinations(big, 2):
        inter = C1 & C2
        if inter and inter <= Fs and len(inter) >= max(3, len(F) // 2):
            icov = len(inter & scan_set) / span
            exps.append({"E": "E9 两类交集", "detail":
                         f"{n1} ∩ {n2} ⊆ F(交集覆盖 {icov:.0%})",
                         "strength": round(1 - icov, 3), "coverage": round(icov, 3)})
            break

    # E10 差分/比值命中具名类
    if len(F) >= 6:
        diff = [F[i + 1] - F[i] for i in range(len(F) - 1)]
        for name, C in list(cls.items())[:60]:
            if all(v in C or v <= 0 for v in diff) and len(set(diff)) > 2:
                exps.append({"E": "E10 差分模式", "detail": f"相邻差 ⊆ {name}", "strength": 0.5})
                break

    real = [e for e in exps if not e.get("vacuous")]
    vac = [e for e in exps if e.get("vacuous")]
    real.sort(key=lambda e: -e["strength"])
    if vac:
        real.append(vac[0])          # 保留一条虚空例示, 供审计
    return real, (len([e for e in real if not e.get("vacuous")]) == 0)


def judge_J2(F, lo, hi, pool, ns=None):
    """J2 的机器答案: 机器能解释吗? 用什么解释?"""
    exps, unexplained = probe(F, lo, hi, pool, ns=ns)
    if unexplained:
        return {"explained": False, "explanations": [],
                "verdict": "机器无法解释(**真信号**, 但须先确认类库完备性)"}
    real = [e for e in exps if not e.get("vacuous")]
    top = (real or exps)[0]
    return {"explained": True, "explanations": exps,
            "verdict": f"机器可解释: {top['E']} —— {top['detail']}"}


if __name__ == "__main__":
    import json
    sys.path.insert(0, str(HERE / "tools"))
    from conjecture_search import build_pool, LO, HI
    from significance_vs_random import exceptions_with

    pool = build_pool()
    cands = json.loads((HERE / "out/demo/final_candidates.json").read_text(encoding="utf-8"))["candidates"]
    ns = list(range(LO, HI + 1, 2))
    rows = []
    for c in cands:
        F = exceptions_with(pool[c["A"]], pool[c["B"]], ns, LO, HI)
        r = judge_J2(F, LO, HI, pool, ns=ns)
        r["candidate"] = f"{c['A']} + {c['B']}"
        r["n"] = len(F)
        rows.append(r)

    expl = [r for r in rows if r["explained"]]
    print(f"J2 机制追问(机器自动化) —— {len(rows)} 个候选\n")
    print(f"机器可解释: {len(expl)} / {len(rows)};  机器无法解释: {len(rows)-len(expl)}\n")
    print(f"{'候选':<26}{'例外':>6}  机器给出的机制")
    print("-" * 92)
    for r in sorted(rows, key=lambda x: (x["explained"], x["n"])):
        m = r["verdict"][:56] if r["explained"] else "**无法解释**"
        print(f"{r['candidate']:<26}{r['n']:>6}  {m}")

    un = [r for r in rows if not r["explained"]]
    if un:
        print(f"\n== 机器**无法解释**的候选(R33 判据⑥要求连同类库完备性一起报告) ==")
        for r in un:
            print(f"  {r['candidate']}  ({r['n']} 例外)")
        print("  ⚠️ 报告时必须声明: 这是**当前类库下**无法解释, 不等于无结构。")
    else:
        print("\n(全部候选机器均可解释 —— 与 R33 结论一致: 补足原语后'无法描述'消失)")

    (HERE / "out/demo/mechanism_probe.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n已存 out/demo/mechanism_probe.json")
