# -*- coding: utf-8 -*-
"""counterex_engine.py — 反例驱动的问题制造器(生成侧, 本项目的"甜区")

理论依据(02_CONTEXT 第3节, 此前从未实现):
  "发现(第一猜想)不可程序化; **反例→新问题 可程序化**(机器甜区)"

与其它引擎的根本区别 —— 本引擎**只提它自己答不出来的问题**:
  其它引擎: 先算判定, 再写陈述(陈述与判定同生) -> 产出的是"计算", 不是问题。
  本引擎:   先算**反例集**, 再把反例集的**结构**变成问题; 机器无法结算这些问题
            (它的全部本事是"扫到上界" —— 扫不出"是否有限", 也扫不出"为什么是这些数")。
            -> status = UNRESOLVED("开放(机器无法结算)"), 不带判定。

流程:
  1. 对每个猜想(两类对象 A+B 覆盖偶数域)算出**完整反例集** F 与扫描区间 [lo,hi]
  2. 结构拟合: 周期(m,剩余类 R) / 有限性 / 密度
  3. **诚实探针(B节)**: 把"扫描窗"当任意选择 —— 向 hi 之外延伸, 看是否有新例外。
     有新例外 => "有限"只是"到 hi 为止没例外", 这是机器自己必须承认的边界。
  4. 产出开放问题(带反例证据, 无判定)

自纠错记录: 首版用 set 迭代 + `if x>=n: break` 遍历加数, 因集合无序而漏掉较小的加数,
假造出 16166 个"例外"(实际猜想几乎处处成立)。改为排序遍历后与 records_engine 的
fail_count 完全吻合(质数+三角数 66, 质数+平方数 75)。
"""
import json
from pathlib import Path
from typing import List

from .judges_math import sieve
from .model import ProblemRecord, TreeRoot, UNRESOLVED

ROOT = TreeRoot("R_counterex", "反例驱动: 从例外集的结构里长出问题", "数学",
                ["反例", "例外集结构", "有限性/密度"],
                "机器算出的例外集, 它的结构是什么? —— 这是机器自己答不出的问题")

CONJECTURES = [
    ("质数", "三角数"), ("质数", "平方数"), ("质数", "半素数"),
    ("奇合数", "平方数"), ("奇合数", "三角数"), ("奇合数", "半素数"),
    ("半素数", "平方数"), ("回文数", "平方数"),
]


def _classes(N):
    ps = sieve(N)
    primes = [i for i in range(2, N) if ps[i]]
    primeset = set(primes)
    oddcomp = set(x for x in range(9, N, 2) if not ps[x])
    squares = set(x * x for x in range(1, int(N ** 0.5) + 1))
    tri = set(t for t in (i * (i + 1) // 2 for i in range(1, int((2 * N) ** 0.5) + 2)) if t <= N)
    fib = [1, 1]
    while fib[-1] + fib[-2] < N:
        fib.append(fib[-1] + fib[-2])
    pals = set(x for x in range(2, N) if str(x) == str(x)[::-1])
    semis = set()
    for i, p in enumerate(primes):
        if p * p > N:
            break
        for q in primes[i:]:
            if p * q >= N:
                break
            semis.add(p * q)
    return {"质数": primeset, "奇合数": oddcomp, "平方数": squares, "三角数": tri,
            "斐波那契数": set(fib), "回文数": pals, "半素数": semis}


def scan(cls, a, b, lo, hi):
    """完整反例集: [lo,hi] 内的偶数 n 不能写成 A+B。

    自纠错: A 必须**排序**后遍历 —— 集合无序, 提前 break 会漏掉较小的加数。
    """
    A, B = sorted(cls.get(a, set())), cls.get(b, set())
    F = []
    for n in range(lo, hi + 1, 2):
        ok = False
        for x in A:
            if x >= n:
                break
            if (n - x) in B:
                ok = True
                break
        if not ok:
            F.append(n)
    return F


def period_fit(F, lo, hi, mmax: int = 60):
    """找最小周期 m: F 在 [lo,hi] 内**恰好**等于某组剩余类。返回 (m, residues) 或 None。"""
    fs = set(F)
    for m in range(2, mmax + 1):
        residues = {x % m for x in F}
        if not residues:
            continue
        pred = {n for n in range(lo, hi + 1, 2) if (n % m) in residues}
        if pred == fs:
            return m, sorted(residues)
    return None


def density_windows(F, lo, hi, span: int = 2000):
    out = []
    a = lo
    while a < hi:
        b = min(a + span, hi)
        tot = len(range(a, b, 2)) or 1
        out.append(round(sum(1 for x in F if a <= x < b) / tot, 4))
        a = b
    return out


def classify(F, lo, hi):
    if not F:
        return {"kind": "空", "n": 0}
    pf = period_fit(F, lo, hi)
    d = density_windows(F, lo, hi)
    tail = d[len(d) // 2:] or [0.0]
    info = {"n": len(F), "first": min(F), "last": max(F),
            "at_boundary": max(F) >= hi - 4,
            "density_all": d, "density_tail_stable": (max(tail) - min(tail)) <= 0.01,
            "density_tail": round(sum(tail) / len(tail), 4)}
    if pf:
        info["kind"] = "周期"
        info["period"], info["residues"] = pf
    elif len(F) <= 40:
        info["kind"] = "有限稀疏"
    else:
        info["kind"] = "非周期(疑似无限/稠密)"
    return info


def probe(cls, a, b, lo, hi):
    """诚实探针: 向 hi 之外延伸扫描。有新例外 => '有限'主张不被支持。"""
    ext_lo, ext_hi = hi + 2, hi + (hi - lo)
    F_ext = scan(cls, a, b, ext_lo, ext_hi)
    return {"ext_range": [ext_lo, ext_hi], "n_beyond": len(F_ext),
            "beyond_head": F_ext[:5], "extends": len(F_ext) > 0}


def questions_from(a, b, info, lo, hi, pr):
    """把反例集的结构变成问题。机器无法结算 => UNRESOLVED。"""
    qs = []
    head = f"偶数 n 写成 {a}+{b} 的例外集"
    # 1) 刻画(核心): 对每个非空例外集都问
    if info["kind"] == "周期":
        m, R = info["period"], info["residues"]
        stmt = (f"{head} 在 [{lo},{hi}] 内**恰好**是模 {m} 的剩余类 {R}"
                f"(共 {info['n']} 个)。这个刻画是精确的吗——为什么恰好是这些剩余类?")
        crit = f"证明对该模 {m} 的所有剩余类成立, 或给出刻画之外的例外"
    else:
        stmt = (f"{head} 在 [{lo},{hi}] 内共 {info['n']} 个, 最大者 {info['last']}"
                f"(前几个: {info.get('examples', [])[:6]})。**是什么刻画了这个例外集**?")
        crit = "给出例外集的精确刻画(同余类/代数条件)并证明, 或指出刻画不存在的理由"
    qs.append({"id": f"CX_{a}_{b}_char", "statement": stmt, "crit": crit,
               "quant": f"[{lo},{hi}] 内偶数"})
    # 2) 有限性: 贴边界 或 延伸后仍有新例外
    if info["at_boundary"] or pr["extends"]:
        ev = (f"最后例外在 {info['last']}(扫描上界 {hi}); 延伸到 {pr['ext_range'][1]} 又见 "
              f"{pr['n_beyond']} 个新例外" if pr["extends"] else
              f"最后例外在 {info['last']}, 紧贴扫描上界 {hi}")
        qs.append({"id": f"CX_{a}_{b}_finite",
                   "statement": f"{head}: {ev}。例外集是**有限**的吗? "
                                f"(机器的全部本事是'扫到上界', 扫不出这个问题)",
                   "crit": "证明例外有限并给出可证上界, 或构造扫描上界之外的新例外",
                   "quant": f"扫描上界 {hi}; 延伸至 {pr['ext_range'][1]}"})
    # 3) 密度: 尾部密度稳定且未饱和
    if info["kind"] == "非周期(疑似无限/稠密)" and info["density_tail_stable"] \
            and 0 < info["density_tail"] < 0.9:
        qs.append({"id": f"CX_{a}_{b}_density",
                   "statement": f"{head} 尾部密度稳定在 {info['density_tail']}"
                                f"(逐窗 {info['density_all'][-4:]})。密度极限是否存在? 极限值是多少?",
                   "crit": "证明密度极限存在并定值, 或证明其不存在",
                   "quant": f"分窗跨度 2000; 区间 [{lo},{hi}]"})
    return qs


def run(N: int = 80000, lo: int = 6, hi: int = 40000):
    cls = _classes(N)
    recs, report = [], []
    for a, b in CONJECTURES:
        F = scan(cls, a, b, lo, hi)
        if not F:
            report.append({"pair": [a, b], "verdict": "无例外(猜想在区间内成立, 无可问)"})
            continue
        info = classify(F, lo, hi)
        info["examples"] = F[:10]
        pr = probe(cls, a, b, lo, hi)
        qs = questions_from(a, b, info, lo, hi, pr)
        for q in qs:
            recs.append(ProblemRecord(
                q["id"], "数学",
                f"机器扫出 {a}+{b} 的例外集后, 反例自身的结构成了新问题",
                ["反例", "例外集结构", info["kind"]],
                f"反例驱动({info['kind']})",
                q["statement"],
                {"method": "反例集结构拟合(机器枚举)", "examples": F[:10],
                 "count": info["n"], "period": info.get("period"),
                 "residues": info.get("residues"), "scan": [lo, hi],
                 "probe": pr, "settleable_by_machine": False,
                 "crit": q["crit"], "quant": q["quant"]},
                status=UNRESOLVED, honesty="机器提出·未结算(需证明或反例)",
                binds={"类A": a, "类B": b, "扫描": f"{lo}..{hi}"},
                tree={"parent": ROOT.id, "edge": f"{a}+{b} 例外集"}))
        report.append({"pair": [a, b], "n": info["n"], "kind": info["kind"],
                       "period": info.get("period"), "last": info["last"],
                       "at_boundary": info["at_boundary"],
                       "probe_extends": pr["extends"], "n_beyond": pr["n_beyond"],
                       "verdict": f"产出 {len(qs)} 个开放问题"})
    return [ROOT], recs, report


def main():
    roots, recs, report = run()
    print(f"反例驱动生成: {len(recs)} 个**开放问题**(机器无法结算)\n")
    print(f"{'猜想':<14}{'例外数':>6}  {'类型':<18}{'贴边界':>6}{'延伸有新例外':>12}  产出")
    for r in report:
        if "n" not in r:
            print(f"{r['pair'][0]}+{r['pair'][1]:<8} {r['verdict']}")
            continue
        print(f"{r['pair'][0]}+{r['pair'][1]:<8}{r['n']:>6}  {r['kind']:<18}"
              f"{str(r['at_boundary']):>6}{str(r['probe_extends']):>12}  {r['verdict']}")
    print("\n== 开放问题原文 ==")
    for p in recs:
        print(f"\n[{p.id}]\n  {p.statement}")
        print(f"  判据: {p.judgement['crit']}")
    Path("out/demo/problems_counterex.json").parent.mkdir(parents=True, exist_ok=True)
    Path("out/demo/problems_counterex.json").write_text(
        json.dumps({"domain": "counterex",
                    "roots": [{"id": ROOT.id, "label": ROOT.label, "domain": ROOT.domain,
                               "motifs": ROOT.motifs, "seed": ROOT.seed}],
                    "problems": [p.to_dict() for p in recs],
                    "report": report}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n已存 out/demo/problems_counterex.json")


if __name__ == "__main__":
    main()
