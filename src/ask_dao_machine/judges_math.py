# -*- coding: utf-8 -*-
"""judges_math.py — 数学判定原语(可复用):
  阈值扫描(全称-找反例) / 存在例证 / 结构反例 / 构造证明 / 表对照(奇偶定理)
  全部纯函数: 给定 limit 建表 → 返回结果; 便于不同规模重复使用。"""

def sieve(n: int) -> bytearray:
    bs = bytearray(b"\x01") * (n + 1)
    bs[0:2] = b"\x00\x00"
    i = 2
    while i * i <= n:
        if bs[i]:
            bs[i*i::i] = b"\x00" * (((n - i*i)//i) + 1)
        i += 1
    return bs


def sigma_tau_phi_tables(m: int):
    """返回 (sigma[], tau[], phi[]) 1..m"""
    sig = [0] * (m + 1)
    tau = [0] * (m + 1)
    for d in range(1, m + 1):
        for k in range(d, m + 1, d):
            sig[k] += d
            tau[k] += 1
    phi = list(range(m + 1))
    for i in range(2, m + 1):
        if phi[i] == i:
            for j in range(i, m + 1, i):
                phi[j] -= phi[j] // i
    return sig, tau, phi


def is_pal_str(x: int) -> bool:
    s = str(x)
    return s == s[::-1]


def scan_two_sum(lo: int, hi: int, step: int, class_a, class_b=None,
                 distinct: bool = False):
    """阈值扫描: 对 n∈[lo,hi,step], 问 ∃ a∈A 使 n-a ∈ B?
    返回反例列表(找不到的 n)。class_a 须为升序列表, class_b 为集合(默认同 A)。"""
    if class_b is None:
        class_b = set(class_a)
    else:
        class_b = set(class_b)
    fails = []
    for n in range(lo, hi + 1, step):
        ok = False
        for a in class_a:
            if a >= n:
                break
            b = n - a
            if b in class_b and (not distinct or b != a):
                ok = True
                break
        if not ok:
            fails.append(n)
    return fails
