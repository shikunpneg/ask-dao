# -*- coding: utf-8 -*-
"""tools/genspace_scan.py — 生成空间策略对照实验(回答"能不能发现新问题")

方法: 用多种生成策略各产生一批整数序列, 统一过 novelty_gate(G1机器真判→G2 OEIS实查→G3结构可推性),
      实测每个策略的: OEIS命中率 / 结构可推率 / 幸存率(N2+N3)。

关键对照(诚实): 加一条"任选参数"策略作阳性对照 —— 若它也能产出 N2/N3, 说明
      **新颖性门能被无意义序列轻易通过**, 真正的瓶颈不是新颖性而是意义/显著性。

策略:
  A 经典组合计数      (binary strings avoiding word / max-run)   —— 预期 OEIS 稠密
  B 参数族停时表      (广义 Collatz max stop, 参数 p,q)          —— 上轮唯一 OEIS 未见来源
  C 模迭代轨道        (x^2+c mod m 最长环, 参数 c,m)             —— 参数化族
  D 表示计数序列      (math_engine T1 模板的底层序列 R(n))       —— 机器实际在用的模板
  E 任选参数对照      (x^2+3 mod 10007 迭代轨道, 任意种子)        —— 阳性对照(应暴露假阳)
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src"))
sys.path.insert(0, str(HERE / "tools"))

from oeis_index import OEISIndex          # noqa: E402
from novelty_gate import NoveltyGate      # noqa: E402
from ask_dao_machine import combo_engine as ce   # noqa: E402
from ask_dao_machine import sparse_engine as se  # noqa: E402
from ask_dao_machine.judges_math import sieve    # noqa: E402


# ---------------- 序列生成器 ----------------
def strat_A():
    """经典组合计数: 禁词 / 最大游程(机器实际 combo 引擎的函数)"""
    out = []
    for w in ("00", "010", "0101", "000", "01001", "10110"):
        out.append({"id": f"A_avoid_{w}", "seq": ce.counts_avoid_word(14, w),
                    "statement": f"长度 n 的 0/1 串中不含子串 {w} 的计数",
                    "evidence_kind": "DP精确枚举"})
    for mr in (2, 3, 4):
        out.append({"id": f"A_maxrun{mr}", "seq": ce.counts_maxrun(14, 2, mr),
                    "statement": f"0/1 串中 1-游程不超过 {mr} 的计数",
                    "evidence_kind": "DP精确枚举"})
    return out


def strat_B():
    """参数族停时表: 广义 Collatz 最大停时(参数 p, q)"""
    out = []
    for p in (3, 5, 7):
        for q in (1, 3, 5):
            seq = [se.max_stop(p, q, N=3000) for _ in range(1)]  # 单值, 需多值故扩展
        # 用不同 N 上界形成序列(随规模增长)
        vals = [se.max_stop(p, 1, N=n) for n in (500, 1000, 2000, 4000, 8000, 16000)]
        out.append({"id": f"B_stop_p{p}", "seq": vals,
                    "statement": f"n<={p} 广义Collatz(n奇->{p}n+1) 最大停时随规模",
                    "evidence_kind": "带记忆迭代"})
    return out


def strat_C():
    """模迭代轨道: x^2+c mod m 最长原始环(参数 c, m)"""
    out = []
    for c in (1, 2, 3):
        vals = [se.max_cycle_len(c, m) for m in range(3, 19)]
        out.append({"id": f"C_cycle_c{c}", "seq": vals,
                    "statement": f"x->x^2+{c} mod m 最长原始环随 m (m=3..18)",
                    "evidence_kind": "全态迭代"})
    return out


def strat_D():
    """表示计数序列: math_engine T1 模板的底层 R(n) —— 机器实际在用"""
    ps = sieve(200000)
    primes = [i for i in range(2, 200000) if ps[i]]
    pmask = set(primes)
    out = []
    # R(n) = 把 n 写成 奇合数 + 奇合数 的表示数
    def odd_composites(limit):
        s = set()
        for n in range(9, limit, 2):
            if n not in pmask:
                s.add(n)
        return s
    oc = odd_composites(400)
    vals = []
    for n in range(40, 40 + 2 * 14, 2):
        c = 0
        for a in sorted(oc):
            if a > n // 2:
                break
            if (n - a) in oc:
                c += 1
        vals.append(c)
    out.append({"id": "D_R_oddcomp", "seq": vals,
                "statement": "n = 奇合数 + 奇合数 的表示数 R(n), n=40,42,...",
                "evidence_kind": "程序枚举"})
    # R(n) = n 写成 质数 + 半素数
    semi = set()
    for a in primes:
        if a * a > 400:
            break
        for b in primes:
            if a * b > 400:
                break
            semi.add(a * b)
    vals2 = []
    for n in range(20, 20 + 2 * 14, 2):
        c = 0
        for a in primes:
            if a > n:
                break
            if (n - a) in semi:
                c += 1
        vals2.append(c)
    out.append({"id": "D_R_prime_semi", "seq": vals2,
                "statement": "n = 质数 + 半素数 的表示数 R(n)",
                "evidence_kind": "程序枚举"})
    return out


def strat_E():
    """阳性对照: 任选参数的确定性轨道(无数学动机)。
    故意**不带显著性证书**(无具名对象不变量) -> 应被 G3.6 拦下, 不得判 N3。"""
    out = []
    for seed0 in (12345, 777, 31337):
        a = [seed0]
        for _ in range(13):
            a.append((a[-1] * a[-1] + 3) % 10007)
        out.append({"id": f"E_arbitrary_{seed0}", "seq": a,
                    "statement": f"x->x^2+3 mod 10007 自种子 {seed0} 的轨道",
                    "evidence_kind": "任意迭代", "prediction": "轨道周期整除 10007"})
    return out


def strat_F():
    """带显著性证书的正例: 广义Collatz 的**非单调**观测量,
    并在任意选择(起点/扫描窗)扰动下检验不变量是否保持。
    观测量: 出现次数(设为奇数的 n 占比) —— 非单调, 避开运行极值伪影。"""
    out = []
    for p in (3, 5):
        def density(p, lo, hi):
            tot = odd = 0
            for n in range(lo, hi):
                tot += 1
                x, steps = n, 0
                while x != 1 and steps < 500:
                    x = p * x + 1 if x % 2 else x // 2
                    steps += 1
                    if steps == 3 and x % 2:
                        odd += 1
                        break
            return round(odd / max(tot, 1), 4)
        # 扰动: 换扫描窗(任意选择)
        vals = [("窗[100,1100]", density(p, 100, 1100)),
                ("窗[2000,3000]", density(p, 2000, 3000)),
                ("窗[5000,6000]", density(p, 5000, 6000))]
        seq = [int(density(p, 100 * (k + 1), 100 * (k + 1) + 200) * 1000) for k in range(8)]
        out.append({"id": f"F_collatz_density_p{p}", "seq": seq,
                    "statement": f"广义Collatz(p={p}) 第3步为奇的 n 的密度随扫描窗",
                    "evidence_kind": "程序枚举",
                    "invariant": f"p={p} 第3步奇占比≈常数",
                    "invariant_tol": 0.01,      # 声明式容忍度: 相对离散 <=1%
                    "perturbations": vals,
                    "prediction": f"p={p} 时第3步奇占比趋于常数, 与起点无关"})
    return out


STRATS = [("A 经典组合计数", strat_A), ("B 参数族停时表(运行极值)", strat_B),
          ("C 模迭代轨道", strat_C), ("D 表示计数(math引擎模板)", strat_D),
          ("E 任选参数对照(无证书)", strat_E), ("F 带显著性证书正例", strat_F)]


def main():
    idx = OEISIndex.load()
    gate = NoveltyGate(idx)
    report, all_recs = [], []
    for name, fn in STRATS:
        cands = fn()
        recs = [gate.grade(c) for c in cands]
        for r, c in zip(recs, cands):
            r["strategy"] = name
            r["seq_head"] = c["seq"][:8]
        all_recs += recs
        cnt = Counter(r["grade"] for r in recs)
        n = len(recs)
        hit = sum(1 for r in recs if r["grade"] == "N0")
        deriv = sum(1 for r in recs if r["grade"] == "N1")
        surv = sum(1 for r in recs if r["grade"] in ("N2", "N3"))
        report.append({"strategy": name, "n": n, "N0_OEIS命中": hit,
                       "N1_结构可推": deriv, "N2_检索级未见": cnt.get("N2", 0),
                       "N3_强候选": cnt.get("N3", 0),
                       "幸存率": round(surv / n, 3) if n else 0})

    print(f"{'策略':<26}{'n':>3}{'N0命中':>8}{'N1可推':>8}{'N2':>5}{'N3':>5}{'幸存率':>8}")
    for r in report:
        print(f"{r['strategy']:<26}{r['n']:>3}{r['N0_OEIS命中']:>8}{r['N1_结构可推']:>8}"
              f"{r['N2_检索级未见']:>5}{r['N3_强候选']:>5}{r['幸存率']:>8}")
    print("\n== 幸存明细(N2/N3) ==")
    for r in all_recs:
        if r["grade"] in ("N2", "N3"):
            print(f"  [{r['grade']}] {r['id']:<22} {r['reason'][:58]}")
            print(f"        seq={r['seq_head']}  {r['statement'][:70]}")

    (HERE / "out/demo/genspace_scan.json").write_text(
        json.dumps({"report": report, "records": all_recs}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print("\n已存 out/demo/genspace_scan.json")


if __name__ == "__main__":
    main()
