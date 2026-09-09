# -*- coding: utf-8 -*-
"""lang_info_engine.py — 领域交叉: 语言-人文(递归语法) × 信息(信道/熵)
  命题: 一种语法生成的语言, 其熵率(每符号的信息增长)是否有界/如何计算?
  判定路线: 正则文法 -> 邻接矩阵谱半径(Perron, 精确); 无歧义CFG -> 生成计数(BFS, 实测) 对照已知生长(如 Catalan)。
  判据来源: 信息论/形式语言理论(可在本机数值判定)。
"""
import math
from .model import ProblemRecord, TreeRoot

ROOT = TreeRoot("R_linginfo", "交叉实验室: 递归语法(语言) × 信道熵(信息)", "数学",
                ["递归语法", "信息-熵/信道"], "语言的'信息产出率'能被语法结构约束到多大?")


def _no_bb_counts(limit=30):
    """无'bb'子串的二元串数量(斐波那契生长)"""
    c = [0] * (limit + 1)
    c[0], c[1] = 1, 2
    for n in range(2, limit + 1):
        c[n] = c[n - 1] + c[n - 2]
    return c


def _catalan_counts(max_pairs=14):
    """平衡括号串(长度为2k的个数=C_k)"""
    catalan = [1]
    for k in range(1, max_pairs + 1):
        catalan.append(catalan[-1] * 2 * (2 * k - 1) // (k + 1))
    return catalan


def _empirical_growth(counts):
    """用最后两项比估计每符号生长率, 返回 (比, log比, 位置)"""
    n = len(counts) - 1
    r = counts[n] / counts[n - 1]
    return round(r, 6), round(math.log(r), 6), n


def run():
    out = []

    def add(id_, seed, motifs, template, binds, stmt, judgement, status, tag, edge=None):
        out.append(ProblemRecord(id_, "数学", seed, motifs, template, stmt, judgement,
                                 status=status, honesty=tag, binds=binds,
                                 tree={"parent": ROOT.id, "edge": edge or template}))

    # X1: 正则文法(禁止"bb") 熵率 = log(斐波那契生长 φ)
    fb = _no_bb_counts(30)
    gr = _empirical_growth(fb)
    phi = (1 + 5 ** 0.5) / 2
    add("X1", "禁止'bb'的二元串, 数量按什么速率增长? (一条正则递归规则)",
        ["递归语法", "信息-熵/信道", "信道约束"], "交叉模板X1: 正则语言熵率 = 邻接谱半径",
        {"文法": "S→aS|bS 但禁 'bb'", "最大长度": 30},
        "无'bb'子串的二元串计数 c_n 满足 c_n=c_{n-1}+c_{n-2}(斐波那契), 每符号熵率 = log φ ≈ 0.481 nats",
        {"method": "递推+Perron 谱半径", "c_30": fb[30],
         "growth_ratio": gr[0], "phi": round(phi, 6), "rate_nats": round(math.log(phi), 6)},
        "真(已知定理: 正则语言熵率=邻接谱半径, 机器复核)", "已知-著名(形式语言/信息论)",
        "正则约束('bb'禁) -> 斐波那契熵率")

    # X2: 无歧义 CFG(平衡括号/Dyck) 渐进每符号熵率 = ln2 (Catalan 生长, 有限长有 k^-1.5 修正)
    cat = _catalan_counts(300)
    kk = 300
    n2 = 2 * kk
    rate_big = math.log(cat[kk]) / n2  # 每符号 nats (k=300)
    asymp = math.log(2.0)
    add("X2", "平衡括号串(Dyck 语言)的熵率呢? (一条嵌套递归规则)",
        ["递归语法", "信息-熵/信道", "嵌套结构"], "交叉模板X2: 无歧义 CFG 生成计数 → 熵率",
        {"文法": "S → (S)S | ε", "最大半长": 300},
        "Dyck 串数=C_k~4^k/(k^{1.5}), 渐进每符号熵率 = ln 2 nats (k=300 实测接近渐进; 高于'禁bb'的 log φ)",
        {"method": "Catalan 公式(bigint)", "k": kk, "c_k_digits": len(str(cat[kk])),
         "rate_k300_nats": round(rate_big, 6), "asymptotic_nats": round(asymp, 6),
         "compare_regular_nats": round(math.log(phi), 6)},
        "真(已知定理: 无歧义 CFG 熵率=代数方程根; 机器用 Catalan 复核)",
        "已知-著名(形式语言/信息论)",
        "嵌套递归规则 -> 更高熵率")

    # X3: 纪录/比较问题: 同字母表、同样"单条规则"预算, 谁的熵率最高?
    add("X3", "同为二元字母表+一条递归规则, 还能造出比 Dyck 更高熵率的语法吗?",
        ["递归语法", "信息-熵/信道", "母题组合/迁移"], "交叉模板X3: 规则预算固定 → 熵率最大化(纪录搜索)",
        {"字母表": "{a,b}", "规则预算": "1 条递归规则"},
        "在'一条递归规则'类文法中, Dyck(渐进 1 bit/sym) 是否接近熵率上界? 更高者需几条规则?",
        {"method": "纪录-枚举(理论)", "dyck_bit_per_symbol": round(math.log(2.0) / math.log(2), 6),
         "regular_bit_per_symbol": round(math.log(phi) / math.log(2), 6),
         "note": "无歧义性约束下枚举上界属开放方向, 需查证/证明"},
        "真(两例实测) + 悬置(上界未证明)", "惊喜候选(查证器待检: 熵率上界与规则数关系)",
        "规则预算 → 熵率上界(开放)")
    return [ROOT], out
