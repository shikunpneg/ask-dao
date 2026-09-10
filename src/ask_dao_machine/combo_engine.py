# -*- coding: utf-8 -*-
"""combo_engine.py — 组合纪录实验室(试点): 换域到'受限组合族'
  生成: (字母表 × 约束族) / (步集 × 游走族) 的参数化实例
  判定: DP 精确计数到 n, 生长率/前缀
  新颖代理: 本地种子表(已知序列前缀+已知常数) -> 命中=已知; 未命中= R(真且种子外, 需查证)
  指标: R 率 = R数 / 总数(目标 ≥5/100)
"""
import math
from .model import ProblemRecord, TreeRoot

ROOT = TreeRoot("R_combo", "组合纪录实验室: 受限字符串/游走 的计数族", "数学",
                ["连续整数串", "组合计数", "递推映射", "母题组合/迁移"],
                "换一个约束/步集, 计数族怎么变? 哪些是种子表外?")

# ---- 本地种子表(扩充): name -> (比率常数或None, 前缀) ----
SEEDS = {
    "Fibonacci": (1.618034, [1, 2, 3, 5, 8, 13, 21, 34]),
    "Pell": (2.414214, [1, 2, 5, 12, 29, 70]),
    "Padovan": (1.324718, [1, 1, 1, 2, 2, 3, 4, 5]),
    "Tribonacci": (1.839286, [1, 1, 2, 4, 7, 13, 24]),
    "powers_of_2": (2.0, [1, 2, 4, 8, 16, 32, 64]),
    "Catalan": (4.0, [1, 2, 5, 14, 42, 132]),
    "central_binomial": (4.0, [2, 6, 20, 70, 252]),      # C(2n,n), 去零后的偶长子列
    "central_trinomial": (3.0, [1, 3, 7, 19, 51, 141]),
    # ---- 扩充: 可公式生成的经典序列(前缀匹配用) ----
    "Lucas": (None, [1, 3, 4, 7, 11, 18, 29, 47]),
    "Jacobsthal": (2.0, [1, 1, 3, 5, 11, 21, 43]),       # (2^n-(-1)^n)/3
    "Bell": (None, [1, 2, 5, 15, 52, 203]),
    "derangements": (None, [1, 2, 9, 44, 265, 1854]),
    "Motzkin": (3.0, [1, 2, 4, 9, 21, 51, 127]),
    "Schroder": (5.828427, [1, 2, 6, 22, 90, 394]),      # 大Schroder(每步比->3+2√2≈5.828)
    "perrin": (1.324718, [3, 0, 2, 3, 2, 5, 5, 7]),
}

def _nonzero_seq(counts):
    return [v for v in counts if v > 0]

def classify(counts, paired=False):
    """按去零子列的生长率/前缀对表 -> ('known', name) or ('R', None)"""
    nz = _nonzero_seq(counts)
    if len(nz) < 3 or not nz[-1]:
        return ("R", None)
    ratio = nz[-1] / nz[-2]
    for name, (sr, pref) in SEEDS.items():
        pref = [p for p in pref if p > 0]
        if pref and nz[: len(pref)] == pref[: len(nz)]:
            return ("known", name)
        if sr and abs(ratio - sr) < 0.02:
            return ("known", name)
    return ("R", None)


def counts_avoid_word(nmax, word):
    """二元串(长度1..nmax)禁连续子串 word 的个数 DP"""
    aut = build_automaton(word)
    c = []
    cur = [0] * (len(word))
    cur[0] = 1
    for n in range(1, nmax + 1):
        nxt = [0] * len(word)
        for s in range(len(word)):
            if cur[s]:
                for b in "01":
                    t = aut[s][b]
                    if t != "X":
                        nxt[t] += cur[s]
        cur = nxt
        c.append(sum(cur))
    return c

def compute_next(word, s, b):
    """在已匹配 s 个字符后读入 b, 返回新匹配长度(=len(word)表示出现完整模式, 应拒绝)"""
    cand = word[:s] + b
    for L in range(len(word), -1, -1):
        if cand.endswith(word[:L]):
            return L
    return 0

def build_automaton(word):
    """KMP 式转移: 状态=已匹配长度; 达到 len(word) 记 'X'(拒收)"""
    trans = {}
    for s in range(len(word) + 1):
        trans[s] = {}
        for b in "01":
            if s >= len(word):
                trans[s][b] = "X"
                continue
            t = compute_next(word, s, b)
            trans[s][b] = "X" if t >= len(word) else t
    return trans

def counts_maxrun(nmax, alphabet, maxrun):
    """无 maxrun 个连续相同字符的串计数(字母表大小 alphabet) DP"""
    c = []
    cur = {(0, 1): 1}  # (last_char, run_len)
    for n in range(1, nmax + 1):
        nxt = {}
        for (ch, r), cnt in cur.items():
            for b in range(alphabet):
                nr = r + 1 if b == ch else 1
                if nr <= maxrun:
                    nxt[(b, nr)] = nxt.get((b, nr), 0) + cnt
        cur = nxt
        c.append(sum(cur.values()))
    return c

def counts_walk(nmax, steps):
    """Z 上从0出发、每步 ∈ steps 的返回原点计数(偶/奇按可达性), 用 DP on [-R,R]"""
    R = max(abs(s) for s in steps) * nmax
    cur = {0: 1}
    c = []
    for n in range(1, nmax + 1):
        nxt = {}
        for x, cnt in cur.items():
            for s in steps:
                nxt[x + s] = nxt.get(x + s, 0) + cnt
        cur = nxt
        c.append(cur.get(0, 0))
    return c


def run(nmax: int = 40):
    out = []

    def add(id_, seed, motifs, template, binds, stmt, judgement, status, tag, edge=None):
        out.append(ProblemRecord(id_, "数学", seed, motifs, template, stmt, judgement,
                                 status=status, honesty=tag, binds=binds,
                                 tree={"parent": ROOT.id, "edge": edge or template}))

    # ---- 生成实例: 禁串族 ----
    forbids = ["00", "11", "000", "111", "010", "101", "0101", "1010", "0000", "0110", "1001"]
    for i, w in enumerate(forbids):
        c = counts_avoid_word(nmax, w)
        kind, seedname = classify(c)
        rl = c[-1] / c[-2] if c[-2] else 0
        tag = f"种子命中: {seedname}" if kind == "known" else "种子表外(待 novelty_gate 反查 OEIS)"
        st = "有限验证(DP精确计数至%d, 非证明)" % nmax
        add(f"CB{i:02d}", f"禁连续子串 '{w}' 的二元串, 计数族是什么?",
            ["连续整数串", "组合计数"], "约束串计数(禁子串)", {"禁": w, "n": nmax},
            f"禁 '{w}' 二元串计数: 尾比≈{rl:.4f}",
            {"method": "KMP-DP", "tail_ratio": round(rl, 4), "c_n": c[-1], "seq": c},
            st, tag, f"禁子串 '{w}'")
    # ---- 生成实例: 最长游程族 ----
    for maxrun in range(2, 7):
        c = counts_maxrun(nmax, 2, maxrun)
        kind, seedname = classify(c)
        rl = c[-1] / c[-2] if c[-2] else 0
        tag = f"种子命中: {seedname}" if kind == "known" else "种子表外(待 novelty_gate 反查 OEIS)"
        add(f"MR{maxrun}", f"没有 {maxrun} 个连续相同符号的二元串, 多少个?",
            ["连续整数串", "组合计数"], "约束串计数(最大游程)", {"maxrun": maxrun, "n": nmax},
            f"无≥{maxrun}连续相同的二元串计数: 尾比≈{rl:.4f}",
            {"method": "游程DP", "tail_ratio": round(rl, 4), "c_n": c[-1], "seq": c},
            f"有限验证(DP精确计数至{nmax}, 非证明)", tag, f"maxrun={maxrun}")
    # ---- 生成实例: 游走族(返回原点计数) ----
    walks = [(-1, 1), (-1, 1, 2, -2), (-1, 0, 1), (-1, 1, -3, 3), (-2, 2, -1, 1, 3, -3), (-1, 1, 2), (-1, 1, 0, 2, -2)]
    for i, stp in enumerate(walks):
        c = counts_walk(nmax, stp)
        kind, seedname = classify(c, paired=(stp == (-2, 2) or stp == (-1, 1)))
        rl = c[-1] / c[-2] if c[-2] else 0
        tag = f"种子命中: {seedname}" if kind == "known" else "种子表外(待 novelty_gate 反查 OEIS)"
        add(f"WK{i:02d}", f"步集 {stp} 的格点游走, 回原点的路数序列?",
            ["递推映射", "组合计数"], "游走返回计数", {"steps": stp, "n": nmax},
            f"步集{stp}返回计数: 尾比≈{rl:.4f}",
            {"method": "格点DP", "tail_ratio": round(rl, 4), "c_n": c[-1], "seq": c},
            f"有限验证(DP精确计数至{nmax}, 非证明)", tag, f"步集 {stp}")
    # ---- 统计 ----
    from collections import Counter
    stat = Counter(p.honesty.split(":")[0].strip() for p in out)
    r_items = [p for p in out if p.honesty.startswith("种子表外")]
    return ROOT, out, stat, len(r_items)
