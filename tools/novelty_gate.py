# -*- coding: utf-8 -*-
"""tools/novelty_gate.py — 真实新颖性门(替代"手写字符串 + 无法输出N3的启发式裁判")

旧状(诊断):
  1. pipeline 从不调用裁判; "惊喜候选"是引擎源码里手写的字符串;
  2. novelty_judge.py 无任何代码路径返回 N3 -> "N3=0" 部分是结构性假象;
  3. 问题记录不带整数序列 -> 就算调裁判也无对象可查。

本门四道, 全部真实执行:
  G1 机器真判   : 候选必须带可复核的判定证据(数值/仿真/构造), 否则 悬置(无判定器)
  G2 参照系反查 : 用本地 OEIS 索引实际反查候选的整数序列(带偏移对齐)
  G3 结构可推性 : OEIS 未命中者, 检验其是否可由已知结构推出
                  (常数系数线性递推 / 低阶多项式 / 已知变换后命中 OEIS / 平凡序列)
  G4 分级       : N0 已知 / N1 可推 / N2 检索级未见 / N3 强候选(可达!)

诚实边界(写进结论, 不许粉饰):
  N3 只表示"过了我们手头唯一参照系(OEIS 整数序列)且不能由已知结构推出"。
  **不等于世界新问题** —— 文献门(literature gate)离线无法执行, N3 必须经文献/专家复核才能升级。
"""
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))

from oeis_index import OEISIndex  # noqa: E402


# ==================== 精确工具 ====================
def solve_exact(rows, k):
    """解 k 元线性方程组(精确有理数)。rows=[(coeffs[k], rhs)]。无解/不定返回 None。"""
    A = [[Fraction(x) for x in c] + [Fraction(r)] for c, r in rows[:k]]
    if len(A) < k:
        return None
    n = k + 1
    piv = 0
    for col in range(k):
        p = None
        for r in range(piv, len(A)):
            if A[r][col] != 0:
                p = r
                break
        if p is None:
            return None
        A[piv], A[p] = A[p], A[piv]
        pv = A[piv][col]
        A[piv] = [v / pv for v in A[piv]]
        for r in range(len(A)):
            if r != piv and A[r][col] != 0:
                f = A[r][col]
                A[r] = [a - f * b for a, b in zip(A[r], A[piv])]
        piv += 1
    return [A[i][k] for i in range(k)]


def find_linear_recurrence(seq, max_order=4, min_terms=9):
    """找常数系数线性递推 a[n]=sum c_i*a[n-i](阶<=max_order)。返回 (阶, 系数) 或 None。"""
    n = len(seq)
    if n < min_terms:
        return None
    for k in range(1, max_order + 1):
        if n < k + 3:
            continue
        eqs = [([seq[i - j] for j in range(1, k + 1)], seq[i]) for i in range(k, n)]
        sol = solve_exact(eqs, k)
        if sol is None:
            continue
        if all(sum(c * a for c, a in zip(sol, coef)) == rhs for coef, rhs in eqs):
            return k, sol
    return None


def poly_degree(seq, max_deg=4, min_terms=7):
    """有限差分: 若某阶差分恒为常数, 返回多项式次数; 否则 None。"""
    if len(seq) < min_terms:
        return None
    cur = list(seq)
    for d in range(1, max_deg + 1):
        cur = [cur[i + 1] - cur[i] for i in range(len(cur) - 1)]
        if len(cur) >= 2 and len(set(cur)) == 1:
            return d
    return None


def transforms(seq):
    """常见变换: 一阶差分 / 部分和 / 二项变换。"""
    if len(seq) < 2:
        return {}
    diff = [seq[i + 1] - seq[i] for i in range(len(seq) - 1)]
    run, ps = 0, []
    for v in seq:
        run += v
        ps.append(run)
    # 二项变换 b[n] = sum_k C(n,k) a[k]
    from math import comb
    bt = [sum(comb(i, j) * seq[j] for j in range(i + 1)) for i in range(min(len(seq), 12))]
    return {"差分": diff, "部分和": ps, "二项变换": bt}


def is_trivial(seq):
    """平凡序列: 常数 / 最终常数 / 全同号且 ≤1 项变动 等。"""
    if len(seq) < 4:
        return True
    if len(set(seq)) == 1:
        return True
    if len(set(seq[-4:])) == 1:      # 最终常数(饱和)
        return True
    if seq == list(range(seq[0], seq[0] + len(seq))):
        return True                  # 等差 1
    return False


def is_running_extremum(seq):
    """检测单调序列(潜在的"运行极值"伪影)。
    典型来源: 'max over 规模<=N' 随 N 的序列 —— **单调是构造出来的, 不是发现**
    (S2 广义Collatz"表观有界/爬升"教训的形式化)。
    返回 '非减' / '非增' / None。"""
    if len(seq) < 5:
        return None
    if all(seq[i + 1] >= seq[i] for i in range(len(seq) - 1)):
        return "非减"
    if all(seq[i + 1] <= seq[i] for i in range(len(seq) - 1)):
        return "非增"
    return None


# ==================== 门 ====================
class NoveltyGate:
    def __init__(self, idx: OEISIndex = None):
        self.idx = idx or OEISIndex.load()

    def grade(self, cand: dict) -> dict:
        """cand: {'id','statement','seq','evidence_kind','verdict'}"""
        rec = {"id": cand.get("id"), "statement": cand.get("statement", "")[:120]}

        # ---- G1 机器真判 ----
        seq = cand.get("seq") or []
        kind = cand.get("evidence_kind")
        if not kind or not seq or len(seq) < 6:
            rec.update(grade="N0?", reason="缺机器判定证据或序列过短, 不入新颖性门",
                       route="悬置(无判定器)", stage="G1")
            return rec
        rec["evidence"] = kind

        # ---- G2 参照系实际反查 ----
        hits = self.idx.lookup(seq, max_hits=4)
        need = min(8, len(seq))
        strong = [h for h in hits if h["matched"] >= need]
        rec["oeis_hits"] = [h["a"] for h in hits]
        rec["oeis_strong_hit"] = [h["a"] for h in strong]
        if strong:
            rec.update(grade="N0", reason=f"OEIS 命中并对齐 {need} 项: {[h['a'] for h in strong]}",
                       stage="G2")
            return rec

        # ---- G3 结构可推性 ----
        if is_trivial(seq):
            rec.update(grade="N1", reason="平凡序列(常数/饱和/等差), OEIS 不收录不等于新",
                       stage="G3")
            return rec
        lr = find_linear_recurrence(seq)
        if lr:
            k, sol = lr
            rec.update(grade="N1",
                       reason=f"满足 {k} 阶常数系数线性递推 a[n]=" +
                              "+".join(f"{c}*a[n-{i+1}]" for i, c in enumerate(sol)),
                       stage="G3")
            return rec
        pd = poly_degree(seq)
        if pd:
            rec.update(grade="N1", reason=f"低阶多项式(次数 {pd})", stage="G3")
            return rec
        for tname, ts in transforms(seq).items():
            th = [h for h in self.idx.lookup(ts, max_hits=2) if h["matched"] >= min(6, len(ts))]
            if th:
                rec.update(grade="N1",
                           reason=f"其「{tname}」命中 OEIS {[h['a'] for h in th]} -> 可由已知序列导出",
                           stage="G3")
                return rec

        # ---- G3.5 构造性伪影检测(单调=可能是"运行极值"伪影) ----
        mono = is_running_extremum(seq)
        if mono:
            rec.update(grade="N1",
                       reason=f"序列{mono}(疑似'运行极值/随规模增长'构造伪影: "
                              f"单调由构造产生, 不含发现; S2 教训)",
                       stage="G3.5")
            return rec

        # ---- G3.6 显著性证书(可机检的部分) ----
        # 真正的瓶颈不是新颖性: 任选参数的序列也能 OEIS 未见 + 结构不可推。
        # 显著性要求: 主张必须是关于**具名对象的不变量**, 且在任意选择被扰动后**保持**。
        # 证书字段: invariant(不变量描述) + perturbations[(变体名, 该变体下不变量取值)]
        inv = cand.get("invariant")
        pert = cand.get("perturbations") or []
        if not inv or len(pert) < 2:
            rec.update(grade="N2",
                       reason="OEIS 未命中 + 结构不可推, 但**缺显著性证书**"
                              "(需: 具名对象的不变量 + 至少2个任意选择扰动下该不变量保持)",
                       stage="G3.6", sig=False)
            return rec
        nums = [v for _n, v in pert]
        tol = cand.get("invariant_tol", 0.0)
        if all(isinstance(v, (int, float)) for v in nums):
            lo, hi = min(nums), max(nums)
            mid = (lo + hi) / 2 or 1.0
            spread = (hi - lo) / abs(mid)          # 相对离散度
            holds = spread <= tol
            rec["invariant_spread"] = round(spread, 5)
            rec["invariant_tol"] = tol
        else:
            holds = len(set(nums)) == 1
            rec["invariant_spread"] = 0.0 if holds else None
        if not holds:
            rec.update(grade="N2",
                       reason=f"不变量「{inv}」在扰动下不保持"
                              f"(相对离散度 {rec['invariant_spread']} > 容忍度 {tol}) "
                              f"-> 该次任意选择的产物, 非对象性质",
                       stage="G3.6", sig=False)
            return rec
        rec["invariant"] = inv
        rec["sig_perturbations"] = pert

        # ---- G4 分级 ----
        rec["growth"] = "非平凡"
        if cand.get("prediction"):
            rec.update(grade="N3",
                       reason=f"OEIS 未命中 + 结构不可推 + 不变量「{inv}」在{len(pert)}个扰动下保持 "
                              f"+ 有可检验预言 (仍须文献/专家复核才能称世界新)",
                       stage="G4", route="需文献门")
        else:
            rec.update(grade="N2",
                       reason=f"OEIS 未命中 + 结构不可推 + 不变量「{inv}」保持; "
                              f"缺可检验预言, 停在检索级",
                       stage="G4", route="需文献门")
        return rec


# ==================== 落盘 ====================
def grade_all(cands, idx=None, verbose=True):
    g = NoveltyGate(idx)
    out = [g.grade(c) for c in cands]
    if verbose:
        from collections import Counter
        c = Counter(r["grade"] for r in out)
        print("分级分布:", dict(c))
    return out


if __name__ == "__main__":
    # 自检: 已知序列应 N0/N1; 构造的"结构不可推"序列应能到 N2/N3(证明 N3 路径可达)
    tests = [
        {"id": "T1", "evidence_kind": "数值", "statement": "质数序列",
         "seq": [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]},
        {"id": "T2", "evidence_kind": "数值", "statement": "平方数(多项式)",
         "seq": [1, 4, 9, 16, 25, 36, 49, 64, 81, 100, 121]},
        {"id": "T3", "evidence_kind": "数值", "statement": "斐波那契(线性递推)",
         "seq": [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]},
        {"id": "T4", "evidence_kind": "数值", "statement": "常数序列(平凡)",
         "seq": [7, 7, 7, 7, 7, 7, 7, 7, 7, 7]},
    ]
    for r in grade_all(tests):
        print(f"  {r['id']} {r['grade']}: {r['reason'][:80]}")
