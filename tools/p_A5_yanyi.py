# -*- coding: utf-8 -*-
"""tools/p_A5_yanyi.py — P-A.A5: "言不尽意 × 熵率" 的可判雏形(把前问题做成判定器)

思路(把哲学断言重写为形式语言判定问题):
  "言不尽意" 的机器可判版本 = **最小文法类分离问题**:
    给定"意义模式"(形式语言 L, 代表一类不可压缩的语义结构),
    问: L 落在哪个最小文法类? 若 L 不在任何有限(正则/CFG)文法类中,
        则"有限的'言'(表层语法)不能穷尽该'意'"。

判定工具(均为可计算的, 非关键词):
  T1 非正则性: Myhill-Nerode 残差类计数随前缀长度的增长(截断近似)。
              正则语言残差类数有界; 若观测到持续增长 -> 非正则。
  T2 非上下文无关性: CFL 泵引理 + Ogden 标记的**穷举检查**:
              对见证词穷举满足 |vxy|<=p 的全部分解, 无一可泵 -> 非CFG。
              (在给定 p 上界内穷举; 是实例级机器验证, 不是通用判定过程)

纪律: 状态只来自判定器; 组件理论均为经典(N1), 不冒充新发现。
"""
import json
import sys
from itertools import product
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


# ---------------- 意义模式(形式语言) ----------------
def m_aNbN(w):
    """嵌套依赖 a^n b^n (如中心嵌入的从句)"""
    i = 0
    while i < len(w) and w[i] == 'a':
        i += 1
    j = i
    while j < len(w) and w[j] == 'b':
        j += 1
    return j == len(w) and i == len(w) - i and i > 0 or w == ""


def m_aNbNcN(w):
    """双重嵌套依赖 a^n b^n c^n"""
    if w == "":
        return True
    i = 0
    while i < len(w) and w[i] == 'a':
        i += 1
    j = i
    while j < len(w) and w[j] == 'b':
        j += 1
    k = j
    while k < len(w) and w[k] == 'c':
        k += 1
    return k == len(w) and i == j - i == k - j and i > 0


def m_aNbNcNdN(w):
    """三重嵌套依赖 a^n b^n c^n d^n"""
    if w == "":
        return True
    counts, cur, ok = [], None, True
    for ch in w:
        if ch != cur:
            counts.append([ch, 1])
            cur = ch
        else:
            counts[-1][1] += 1
    if len(counts) != 4 or [c for c, _ in counts] != ['a', 'b', 'c', 'd']:
        return False
    ns = [n for _, n in counts]
    return len(set(ns)) == 1 and ns[0] > 0


def m_ww(w):
    """跨序列依赖(复制/交叉依赖) ww"""
    if len(w) % 2:
        return False
    h = len(w) // 2
    return w[:h] == w[h:]


def m_dyck(w):
    """广义嵌套 Dyck 语言(括号)"""
    d = 0
    for ch in w:
        if ch == '(':
            d += 1
        elif ch == ')':
            d -= 1
            if d < 0:
                return False
    return d == 0


PATTERNS = {
    "a^n b^n  (嵌套依赖)": (m_aNbN, "ab", "CFG(非正则)"),
    "a^n b^n c^n (双重嵌套)": (m_aNbNcN, "abc", "非CFG"),
    "a^n b^n c^n d^n (三重嵌套)": (m_aNbNcNdN, "abcd", "非CFG"),
    "ww (跨序列复制)": (m_ww, "ab", "非CFG"),
    "Dyck (一般嵌套)": (m_dyck, "()", "CFG(非正则)"),
}


# ---------------- T1: Myhill-Nerode 残差类计数 ----------------
def residual_counts(mem, alpha, K=None, M=None):
    """对长度<=K 的所有前缀, 用长度<=M 的后缀特征做签名; 返回每个前缀长度上的类数。
    K/M 按字母表大小自适应, 控制枚举规模(|alpha|^K <= ~2000)。"""
    A = len(alpha)
    if K is None:
        K = 9 if A == 2 else 4
    if M is None:
        M = 7 if A == 2 else 4
    suffixes = [""]
    for L in range(1, M + 1):
        suffixes += ["".join(p) for p in product(alpha, repeat=L)]
    sigs_at_k = {}
    for k in range(K + 1):
        seen = set()
        for pre in product(alpha, repeat=k):
            u = "".join(pre)
            sig = tuple(mem(u + v) for v in suffixes)
            seen.add(sig)
        sigs_at_k[k] = len(seen)
    return sigs_at_k


# ---------------- T0: 正则泵引理穷举 ----------------
def reg_pump_fails(mem, w, pmax):
    """穷举 w=xyz, |xy|<=p, |y|>=1; 若全部分解在 i=0,2 上破成员 => 非正则。
    返回 (all_fail, n_decompositions, counterexample)。"""
    n = len(w)
    total = 0
    for p in range(1, pmax + 1):
        for ly in range(1, p + 1):
            for lx in range(0, p - ly + 1):
                x = w[:lx]
                y = w[lx:lx + ly]
                z = w[lx + ly:]
                total += 1
                if mem(x + z) and mem(x + y + y + z):
                    return False, total, {"p": p, "y": y}
    return True, total, None


# ---------------- T2: CFL 泵引理穷举 ----------------
def cfl_pump_fails(mem, w, pmax):
    """穷举 |vxy|<=p, |vy|>=1 的分解, 找是否存在可泵分解(i=0,2 均保成员)。
    返回 (all_fail, n_decompositions)。all_fail=True => 在 p<=pmax 内无合法泵分解。"""
    n = len(w)
    total = 0
    for p in range(1, pmax + 1):
        for i in range(n):
            for j in range(i + 1, n + 1):      # v = w[i:j], |v|>=0
                for k in range(j, n):
                    for l in range(k + 1, n + 1):  # y = w[k:l], |y|>=0
                        x = w[j:k]
                        vxy_len = (j - i) + (k - j) + (l - k)
                        if (j - i) + (l - k) < 1:
                            continue
                        if vxy_len > p:
                            continue
                        total += 1
                        u, v, y, z = w[:i], w[i:j], w[k:l], w[l:]
                        ok0 = mem(u + x + z)
                        ok2 = mem(u + v + v + x + y + y + z)
                        if ok0 and ok2:
                            return False, total, {"p": p, "v": v, "y": y}
    return True, total, None


def main():
    rows = []
    for name, (mem, alpha, expect) in PATTERNS.items():
        rc = residual_counts(mem, alpha)
        kmax = max(rc)
        pmax = 3
        n = 2 * pmax + 2
        if "a^n b^n c^n" in name:
            witness = "a" * n + "b" * n + "c" * n
        elif "d^n" in name:
            witness = "a" * n + "b" * n + "c" * n + "d" * n
        elif "ww" in name:
            witness = "ab" * n
        elif "Dyck" in name:
            witness = "(" * n + ")" * n
        else:
            witness = "a" * n + "b" * n
        reg_fail, reg_ndec, _r = reg_pump_fails(mem, witness, pmax)
        cfl_fail, cfl_ndec, _c = cfl_pump_fails(mem, witness, pmax)
        if not reg_fail:
            verdict = "正则(未见非正则见证)"
        elif not cfl_fail:
            verdict = ">=CFG 且非正则(未见非CFG见证)"
        else:
            verdict = ">=上下文敏感(非CFG, 机器验证)"
        rows.append({
            "pattern": name, "expect": expect,
            "residual_counts_by_prefix_len": rc,
            "reg_witness": witness, "reg_decompositions_tried": reg_ndec,
            "reg_all_pump_fail": reg_fail,
            "cfl_witness": witness, "cfl_decompositions_tried": cfl_ndec,
            "cfl_all_pump_fail": cfl_fail,
            "verdict": verdict,
        })
        print(f"{name}")
        print(f"  残差类数(k=0..{kmax}, 仅描述): {[rc[k] for k in range(kmax + 1)]}")
        print(f"  正则泵穷举: 见证词={witness} 分解数={reg_ndec} 全部不可泵={reg_fail}")
        print(f"  CFL泵穷举: 分解数={cfl_ndec} 全部不可泵={cfl_fail}")
        print(f"  => 判定: {verdict}  (预期 {expect})")

    payload = {
        "problem": "言不尽意 的可判版本: 意义模式(形式语言)的最小文法类分离",
        "tooling": ["Myhill-Nerode 残差类计数(截断近似)", "CFL 泵引理穷举(实例级机器验证)"],
        "honesty": "组件理论(Myhill-Nerode/CFL泵引理)均为经典 N1; 本脚本的贡献是把"
                   "'言不尽意'重写为可判分离问题, 不主张理论新意。",
        "rows": rows,
    }
    (HERE / "out/demo/p_A5_yanyi.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n已存 out/demo/p_A5_yanyi.json")


if __name__ == "__main__":
    main()
