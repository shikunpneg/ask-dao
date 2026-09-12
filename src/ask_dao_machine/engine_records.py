# -*- coding: utf-8 -*-
"""records_engine.py — 纪录/图案型问题制造器:
  把生成移到"参数化边角": (对象类A × 对象类B × 偶数域) 的覆盖性扫描,
  输出 覆盖阈值/反例图案/间隙纪录/迭代纪录 —— 机器自己发现的数字事实即新问题原料。
  诚实: 只对扫描范围负责; 已知配对自动标注; 其余=待参照系反查 -> 交给 novelty_gate。"""
import math
from .judge_math import sieve
from .data_problem_model import ProblemRecord, TreeRoot

# 已收录配对的先验知识(模板=偶数两数和)
KNOWN = {
    ("质数", "质数"): ("悬置(开放)", "已知-著名: 哥德巴赫"),
    ("奇合数", "奇合数"): ("有限验证(至扫描上限, 非证明)", "已知-小定理(阈值40; 文献大概率已有)"),
    ("平方数", "平方数"): ("假(结构性: 4k+2)", "已知(模论证)"),
    ("质数", "奇合数"): ("有限验证(至扫描上限, 非证明)", "已知-易证类(文献需核对具体阈值)"),
    ("无平方因子数", "无平方因子数"): ("有限验证(至扫描上限, 非证明)", "已知(Estermann 系: 大整数=两无平方因子数)"),
}


def run(N: int = 80000, SCAN: int = 40000, RUN_CAP: int = 400):
    ps = sieve(N)
    primes = [i for i in range(2, N) if ps[i]]
    primeset = set(primes)
    oddcomp = [x for x in range(9, N, 2) if not ps[x]]
    oddcompset = set(oddcomp)

    def sqfree():
        ok = bytearray(b"\x01") * (N + 1)
        ok[0:2] = b"\x00\x00"
        i = 2
        while i * i <= N:
            if ps[i]:
                for j in range(i * i, N + 1, i * i):
                    ok[j] = 0
            i += 1
        return sorted(x for x in range(2, N) if ok[x])

    sqf = sqfree()
    sqfset = set(sqf)
    squares = sorted(x * x for x in range(1, int(N ** 0.5) + 1))
    sqset = set(squares)
    tri = [t for t in (i * (i + 1) // 2 for i in range(1, int((2 * N) ** 0.5) + 2)) if t <= N]
    triset = set(tri)
    fib = [1, 1]
    while fib[-1] + fib[-2] < N:
        fib.append(fib[-1] + fib[-2])
    fibset = set(fib)
    pals = sorted(x for x in range(2, N) if str(x) == str(x)[::-1])
    palset = set(pals)
    semis = set()
    for i, p in enumerate(primes):
        if p * p > N:
            break
        for q in primes[i:]:
            if p * q >= N:
                break
            semis.add(p * q)
    semi = sorted(semis)

    classes = {"质数": primes, "奇合数": oddcomp, "平方数": squares,
               "三角数": tri, "无平方因子数": sqf, "半素数": semi,
               "回文数": pals, "斐波那契数": fib}

    roots = [TreeRoot("R_records", "参数化边角实验室: 两类对象×偶数域 的覆盖与纪录", "数学",
                      list(classes.keys()), "换一组对象类, 覆盖阈值/反例图案会怎么变?")]
    out = []

    def add(id_, seed, motifs, template, binds, stmt, judgement, status, tag):
        out.append(ProblemRecord(id_, "数学", seed, motifs, template, stmt, judgement,
                                 status=status, honesty=tag, binds=binds,
                                 tree={"parent": "R_records", "edge": template}))

    def scan(a_name, b_name):
        A = classes[a_name]
        Bset = set(classes[b_name])
        fails_head = []
        run = 0
        threshold = None
        n = 6
        while n <= SCAN:
            ok = False
            for a in A:
                if a >= n:
                    break
                if (n - a) in Bset:
                    ok = True
                    break
            if not ok:
                fails_head.append(n)
                run += 1
                if run > RUN_CAP:
                    return {"complete": False, "fails_head": fails_head, "run_capped": True}
            else:
                run = 0
            n += 2
        return {"complete": True, "fails_head": fails_head, "run_capped": False,
                "threshold": (max(fails_head) + 2) if fails_head else 6,
                "fails_count": len(fails_head)}

    pair_ids = ["质数", "奇合数", "平方数", "无平方因子数", "半素数", "回文数", "三角数"]
    for i, a in enumerate(pair_ids):
        for b in pair_ids[i:]:
            rid = f"R2_{a[:1]}{b[:1]}{i}"
            r = scan(a, b)
            key = (a, b) if (a, b) in KNOWN else ((b, a) if (b, a) in KNOWN else None)
            if r["complete"]:
                if r["fails_head"]:
                    stmt = (f"所有 ≥{r['threshold']} 且 ≤{SCAN} 的偶数均可写成 {a}+{b}"
                            if not (key and KNOWN[key][0].startswith("假")) else
                            f"并非所有偶数都可写成 {a}+{b} (如 4k+2 恒失败); 扫描到{SCAN}失败{len(r['fails_head'])}个")
                else:
                    stmt = f"6..{SCAN} 内偶数均可写成 {a}+{b}"
                if key:
                    status, tag = KNOWN[key]
                    if r["fails_head"] and (status.startswith("真") or status.startswith("有限验证")):
                        status = f"有限验证(阈值{r['threshold']}, 扫描至{SCAN}, 非证明)"
                else:
                    status, tag = "有限验证(至扫描上限, 非证明)", "待参照系反查(未过 novelty_gate)"
                judge = {"method": "双类两数和覆盖扫描", "range": f"偶数6..{SCAN}",
                         "fail_count": len(r["fails_head"]), "fails_head": r["fails_head"][:10],
                         "threshold": r["threshold"]}
            else:
                stmt = f"是否存在某个界后 偶数皆 = {a}+{b}? (扫描至{SCAN} 失败超{RUN_CAP}次, 疑似无覆盖)"
                if key:
                    status, tag = KNOWN[key]
                    if status.startswith("假"):
                        stmt = f"并非所有偶数都是 {a}+{b} (结构性失败, 如 4k+2)"
                else:
                    status, tag = "悬置(覆盖疑似失败·证据不足)", "待参照系反查(未过 novelty_gate)"
                judge = {"method": "双类两数和覆盖扫描(失败截断)", "range": f"偶数6..{SCAN}",
                         "fails_head": r["fails_head"][:10], "capped": True}
            add(rid, f"把 {a} 与 {b} 配对当'两个加数', 偶数都够得到吗?", [a, b, "奇偶", "两项和"],
                f"纪录模板: 覆盖扫描({a}×{b})", {"类A": a, "类B": b, "扫描": SCAN}, stmt,
                judge, status, tag)
    return roots, out
