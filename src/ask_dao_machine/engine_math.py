# -*- coding: utf-8 -*-
"""math_engine.py — 数学域 问题制造器核心:
  母题对象(质数/奇合数/平方/三角/斐波那契/回文/半素数...) × 映射(σ/τ/φ/数位迭代)
  × 模板(两项和/三项和/加常数变异/构造...) → 候选命题 → 判定 → ProblemRecord(带出处链)
  输出与 machine_v1 v0.2 一致(25 题), 但全部经 judges_math 原语与 model 记录。"""
import math
from .judge_math import sieve, sigma_tau_phi_tables, is_pal_str, scan_two_sum
from .data_problem_model import ProblemRecord, TreeRoot


def run(N: int = 300000, M: int = 500000):
    ps = sieve(N)
    primes = [i for i in range(2, N) if ps[i]]
    primeset = set(primes)
    oddcomp = [x for x in range(9, N, 2) if not ps[x]]
    ocset = set(oddcomp)
    sqset = set([0] + [i * i for i in range(1, int(N ** 0.5) + 1)])
    tri = sorted([0] + [i * (i + 1) // 2 for i in range(1, 210)])
    tris = set(tri)
    fib = [1, 1]
    while fib[-1] + fib[-2] < N:
        fib.append(fib[-1] + fib[-2])
    palset = set(x for x in range(1, N) if is_pal_str(x))
    semis = set()
    for i, p in enumerate(primes):
        if p * p > N:
            break
        for q in primes[i:]:
            if p * q >= N:
                break
            semis.add(p * q)
    sig, tau, phi = sigma_tau_phi_tables(M)

    roots = [
        TreeRoot("R_goldbach", "疑问: 偶数与质数的拆分之谜", "数学", ["奇偶", "质数", "奇合数", "两项和", "三项和"], "偶数能拆成什么?"),
        TreeRoot("R_sigma", "疑问: '因子和'的世界", "数学", ["因子和", "加常数变异", "欧拉φ", "除数个数τ"], "因子和与自己差多少?"),
        TreeRoot("R_primegap", "疑问: 质数之间的空档", "数学", ["整除", "阶乘构造", "连续区间"], "质数越到后面越稀疏?"),
        TreeRoot("R_squares", "疑问: 平方数之间藏着质数?", "数学", ["连续平方", "质数"], "相邻平方之间必有质数吗?"),
        TreeRoot("R_seq", "疑问: 按规则一直算下去会怎样?(递推)", "数学", ["递推映射", "Collatz3n+1", "数位和", "快乐数"], "一个规则套下去, 会收敛/循环/发散?"),
        TreeRoot("R_pal", "疑问: 数字的'长相'(回文与分解)", "数学", ["回文数", "半素数", "2的幂"], "对称的数里藏着质数吗?"),
    ]
    out = []

    def add(id_, seed, motifs, template, binds, stmt, judgement, status, tag, tree):
        parent, edge = (tree.split("/", 1) if "/" in tree else (tree, ""))
        out.append(ProblemRecord(id_, "数学", seed, motifs, template, stmt, judgement,
                                 status=status, honesty=tag, binds=binds,
                                 tree={"parent": parent, "edge": edge}))

    # ---- 族 A: 偶数的两项奇合数之和 ----
    f1 = scan_two_sum(6, N, 2, oddcomp)
    th1 = max(f1) + 2
    add("A1", "偶数能拆成两个'非质数'的奇数吗?", ["奇偶", "奇合数", "两项和"], "T1 域×对象类×两项和",
        {"对象类": "奇合数", "约束": "可相同", "扫描域": f"6..{N}"}, f"所有 ≥{th1} 的偶数都是两个奇合数之和",
        {"method": "暴力扫描", "range": f"偶数6..{N}", "fail_count": len(f1), "fails_head": f1[:12],
         "threshold": th1, "proof": "配方 n%6==0:9+(n-9); n≡4:25+(n-25); n≡2:35+(n-35)"},
        "真(定理+配方证明)", "及格线产物(文献大概率已有)", "R_goldbach/把'质数'换成'奇合数'")

    f2 = scan_two_sum(6, N, 2, oddcomp, distinct=True)
    th2 = max(f2) + 2
    add("A2", "若两数还必须不同(不许9+9)呢?", ["奇偶", "奇合数", "两项和"], "T1 + 约束(相异)",
        {"对象类": "奇合数", "约束": "两数不同", "扫描域": f"6..{N}"}, f"所有 ≥{th2} 的偶数都是两个不同奇合数之和",
        {"method": "暴力扫描(相异)", "range": f"偶数6..{N}", "fail_count": len(f2), "fails_head": f2[:14],
         "threshold": th2}, "有限验证(至扫描上限, 非证明)", "待参照系反查(未过 novelty_gate)", "A1/加约束:两数不同")

    f3 = scan_two_sum(6, N, 2, oddcomp, class_b=primeset)
    th3 = max(f3) + 2
    add("A3", "一边质数一边奇合数呢?", ["奇偶", "质数", "奇合数", "两项和"], "T1 混合类",
        {"类A": "奇合数", "类B": "质数", "扫描域": f"6..{N}"}, f"所有 ≥{th3} 的偶数 = 奇合数+质数",
        {"method": "暴力扫描", "range": f"偶数6..{N}", "fail_count": len(f3), "fails_head": f3[:12],
         "threshold": th3}, "有限验证(至扫描上限, 非证明)", "待参照系反查(未过 novelty_gate)", "R_goldbach/混合两类对象")

    # ---- 族 B: 质数相关(著名) ----
    gold = []
    for n in range(4, min(100000, N - 1) + 1, 2):
        if not any(ps[p] and ps[n - p] for p in primes if p < n):
            gold.append(n)
    add("B1", "每个≥4的偶数=两质数和?", ["奇偶", "质数", "两项和"], "T1(对象类=质数)",
        {"对象类": "质数", "扫描域": f"4..{min(100000,N-1)}"}, "每个 ≥4 的偶数都是两个质数之和",
        {"method": "暴力扫描", "range": f"偶数4..{min(100000,N-1)}", "fail_count": len(gold), "fails_head": gold[:5]},
        "悬置(开放)", "已知-著名: 哥德巴赫猜想", "R_goldbach/原版(著名)")

    lem = []
    for n in range(9, min(50000, N - 1), 2):
        if not any(ps[q] and n > 2 * q and ps[n - 2 * q] for q in primes if q <= n // 2):
            lem.append(n)
    add("B2", "奇数 = 质数 + 2×质数?", ["奇偶", "质数", "两项和"], "T2 奇数=p+2q",
        {"扫描域": f"奇数9..{min(50000,N-1)}"}, "每个 ≥9 的奇数都是质数与二倍质数之和",
        {"method": "暴力扫描", "range": f"奇数9..{min(50000,N-1)}", "fail_count": len(lem), "fails_head": lem[:5]},
        "悬置(开放)", "已知-著名: 莱莫因/利维猜想", "R_goldbach/换域+换结构(+2q)")

    gold2ok = {}
    weak = []
    for n in range(9, min(50000, N - 1), 2):
        ok = False
        for p in primes:
            if p >= n:
                break
            r = n - p
            if r >= 4 and r % 2 == 0:
                key = r
                if key not in gold2ok:
                    gold2ok[key] = any(ps[a] and ps[key - a] for a in primes if a < key)
                if gold2ok[key]:
                    ok = True
                    break
        if not ok:
            weak.append(n)
    add("B3", "每个大奇数=三个质数和?(弱哥德巴赫)", ["奇偶", "质数", "三项和"], "T3 奇数=p+q+r",
        {"扫描域": f"奇数9..{min(50000,N-1)}"}, "每个 ≥9 的奇数都是三个质数之和",
        {"method": "数值复核", "range": f"奇数9..{min(50000,N-1)}", "fail_count": len(weak), "fails_head": weak[:5]},
        "真(已证: Helfgott 2013, 机器数值复核)", "已知-已证(弱哥德巴赫)", "R_goldbach/三项和")

    bert = []
    for n in range(2, min(30000, N // 2)):
        if not any(ps[x] for x in range(n + 1, 2 * n)):
            bert.append(n)
    add("B4", "[n,2n] 之间必有质数?(贝特朗)", ["连续区间", "质数"], "T4 区间存在性",
        {"扫描域": f"n=2..{min(30000,N//2)-1}"}, "对任意 n>1, n 与 2n 之间存在质数",
        {"method": "区间扫描", "range": f"n=2..{min(30000,N//2)-1}", "fail_count": len(bert), "fails_head": bert[:5]},
        "真(已证: 切比雪夫/贝特朗)", "已知-已证定理", "R_primegap/区间[n,2n]")

    # ---- 族 C: 因子和家族 ----
    perfect = [n for n in range(2, M + 1) if sig[n] == 2 * n]
    add("C1", "存在因子和=自己的数?", ["因子和", "加常数变异"], "T5 σ(n)=2n+c, c=0",
        {"c": 0, "扫描域": f"2..{M}"}, "存在完全数(σ=2n)",
        {"method": "筛法σ表", "range": f"2..{M}", "found": perfect[:8], "count": len(perfect)},
        "真(存在,例证)", "及格线产物", "R_sigma/c=0 完全数")
    quasi = [n for n in range(2, M + 1) if sig[n] == 2 * n + 1]
    add("C2", "因子和=自己+1 呢?", ["因子和", "加常数变异"], "T5 σ(n)=2n+c, c=1",
        {"c": 1, "扫描域": f"2..{M}"}, "存在 n>1 使 σ(n)=2n+1 (准完全数)",
        {"method": "筛法σ表", "range": f"2..{M}", "found": quasi[:5], "count": len(quasi)},
        "悬置(开放)", "已知-著名: 准完全数是否存在", "C1/参数移动 c:0→1")
    oddperf = [n for n in range(1, M + 1, 2) if sig[n] == 2 * n]
    add("C3", "完全数还得是奇数?", ["因子和", "奇偶", "加常数变异"], "T5+奇偶约束",
        {"奇偶": "奇数", "扫描域": f"奇数1..{M}"}, "存在奇完全数",
        {"method": "筛法σ表(奇数)", "range": f"奇数1..{M}", "found": oddperf[:5], "count": len(oddperf)},
        "悬置(开放)", "已知-著名: 奇完全数(未解)", "C1/加约束:n为奇数")
    amic, seen = [], set()
    amic_hi = min(400000, M)
    for n in range(2, amic_hi):
        if n in seen:
            continue
        m = sig[n] - n
        if m != n and 1 < m <= amic_hi and sig[m] - m == n:
            amic.append((n, m))
            seen.add(n)
            seen.add(m)
    add("C4", "两个数互为对方真因子和?(亲和)", ["因子和", "加常数变异"], "T6 σ(n)−n=m ∧ σ(m)−m=n",
        {"扫描域": "2..400000"}, "存在亲和数对",
        {"method": "筛法σ表", "range": "2..400000", "found": amic[:8], "count": len(amic)},
        "真(存在,例证)", "及格线产物", "R_sigma/自指配对(链长2)")
    pbad = []
    for n in range(1, 40001):
        r = int(n ** 0.5)
        sq2 = (r * r == n) or (n % 2 == 0 and int((n // 2) ** 0.5) ** 2 == n // 2)
        if (sig[n] % 2 == 1) != sq2:
            pbad.append(n)
    add("C5", "σ(n) 何时是奇数?", ["因子和", "奇偶"], "T7 值域奇偶性刻画",
        {"扫描域": "1..40000"}, "σ(n) 奇 ⇔ n 为平方或2×平方",
        {"method": "全量对照", "range": "1..40000", "violations": len(pbad)},
        "真(已知定理,机器验证)", "及格线产物(验证)", "R_sigma/元观察:奇偶性")
    tbad = []
    for n in range(1, 40001):
        if (tau[n] % 2 == 1) != (int(n ** 0.5) ** 2 == n):
            tbad.append(n)
    add("C6", "τ(n)(因子个数) 何时是奇数?", ["除数个数τ", "奇偶"], "T8 τ奇偶刻画",
        {"扫描域": "1..40000"}, "τ(n) 奇 ⇔ n 为平方数",
        {"method": "全量对照", "range": "1..40000", "violations": len(tbad)},
        "真(已知定理,机器验证)", "及格线产物(验证)", "R_sigma/τ与平方配对")
    phibad = []
    for n in range(3, 40001):
        if phi[n] % 2 == 1:
            phibad.append(n)
    add("C7", "φ(n)(1..n中与n互质数) 总为偶数?", ["欧拉φ", "奇偶"], "T9 φ值域奇偶性",
        {"扫描域": "n=3..40000"}, "对 n≥3, φ(n) 是偶数",
        {"method": "全量对照", "range": "n=3..40000", "violations": len(phibad)},
        "真(已知定理,机器验证)", "及格线产物(验证)", "R_sigma/φ与奇偶")

    # ---- 族 D: 质数空隙(构造) ----
    fac = math.factorial(11)
    r10 = [fac + t for t in range(2, 12)]
    add("D1", "质数之间的空档能多大?", ["整除", "阶乘构造"], "T10 (k+1)!+t 为合数",
        {"k": 10}, "存在任意长连续合数串(质数间隔无上界)",
        {"method": "构造证明", "witness": f"{fac}+2..{fac}+11",
         "verified": all(any(r10[i] % d == 0 for d in range(2, r10[i])) for i in range(10))},
        "真(构造证明)", "及格线产物", "R_primegap/阶乘构造")

    # ---- 族 E: 平方区间 / 两平方 ----
    leg = []
    for k in range(1, int(N ** 0.5)):  # 保证 (k+1)^2 <= N
        lo, hi = k * k, (k + 1) * (k + 1)
        if not any(ps[x] for x in range(lo + 1, hi)):
            leg.append(k)
    add("E1", "k² 与 (k+1)² 之间有质数?", ["连续平方", "质数"], "T11 区间存在性",
        {"扫描域": f"k=1..{int(N**0.5)-1}"}, "对任意 k≥1, k² 与 (k+1)² 之间存在质数",
        {"method": "区间扫描", "range": f"k=1..{int(N**0.5)-1}", "fail_count": len(leg), "fails_head": leg[:5]},
        "悬置(开放)", "已知-著名: 勒让德猜想", "R_squares/连续平方域")

    s2set = set()
    sqvals = [i * i for i in range(0, int(2000 ** 0.5) + 1)]
    for a in sqvals:
        for b in sqvals:
            if a + b <= 2000:
                s2set.add(a + b)
    sq2f = [n for n in range(0, 2000, 2) if n not in s2set]
    add("E2", "所有偶数都是两平方和?", ["平方数", "两项和", "奇偶"], "T12 两平方和",
        {"扫描域": "0..2000"}, "所有偶数都是两个平方数之和",
        {"method": "集合反查", "range": "0..2000", "even_fail_examples": sq2f[:6],
         "note": "4k+2 形数永不可拆 → 结构性假"},
        "假(结构性: 4k+2 不可能)", "及格线产物(反例+模论证)", "R_squares/平方对象×两项和")

    # ---- 族 F: 三三角数(高斯复核) ----
    tripair = set()
    for i in range(len(tri)):
        for j in range(i, len(tri)):
            s = tri[i] + tri[j]
            if s > 20000:
                break
            tripair.add(s)
    tri3fail = []
    for n in range(0, 20001):
        ok = False
        for t in tri:
            if t > n:
                break
            if (n - t) in tripair:
                ok = True
                break
        if not ok:
            tri3fail.append(n)
    add("F1", "每个数=三个三角数和?(高斯)", ["三角数", "三项和"], "T13 n=T_a+T_b+T_c",
        {"扫描域": "0..20000"}, "每个非负整数都是三个三角数之和",
        {"method": "集合反查", "range": "0..20000", "fail_count": len(tri3fail), "fails_head": tri3fail[:5]},
        "真(已证: 高斯 Eureka)", "已知-已证定理(机器复核)", "R_goldbach/三角对象×三项和")

    # ---- 族 G: 递推/循环 ----
    collcache = {1: True}
    import sys as _sys
    _sys.setrecursionlimit(1000000)

    def reach1(x, depth=0):
        if depth > 200000:
            return False
        if x in collcache:
            return collcache[x]
        nxt = 3 * x + 1 if x % 2 else x // 2
        collcache[x] = reach1(nxt, depth + 1)
        return collcache[x]

    coll = []
    for n0 in range(2, 100001):
        if not reach1(n0):
            coll.append(n0)
    add("G1", "3n+1 规则套下去都会回到1吗?(Collatz)", ["递推映射", "Collatz3n+1"], "T14 a→3a+1(奇)/a/2(偶)",
        {"扫描域": "2..100000"}, "对任意正整数, Collatz 迭代最终到达 1",
        {"method": "带记忆迭代", "range": "2..100000", "fail_count": len(coll)},
        "悬置(开放)", "已知-著名: Collatz 猜想", "R_seq/代表'递推映射'族")

    def digit_sq(x):
        return sum(int(c) ** 2 for c in str(x))

    def happy_path(x):
        seen = set()
        while x != 1 and x not in seen:
            seen.add(x)
            x = digit_sq(x)
        return x == 1, seen

    sad_cycle = None
    for n0 in [2, 3, 4, 5, 6, 8, 9]:
        h, path = happy_path(n0)
        if not h:
            sad_cycle = (n0, list(path)[-10:])
            break
    happy_n = [n for n in range(1, 20000) if happy_path(n)[0]]
    add("G2", "'快乐数'(数位平方迭代到1)存在吗?循环长什么样?", ["数位和", "递推映射"], "T15 数位平方映射",
        {"扫描域": "1..20000"}, "存在快乐数; 存在不快乐数的循环(4→16→37→58→89→145→42→20→4)",
        {"method": "迭代轨迹", "range": "1..20000", "happy_count": len(happy_n), "sad_cycle_seed": sad_cycle},
        "真(存在例证+循环构造)", "及格线产物/部分已知定义", "R_seq/数位和×递推")

    fibbad = []
    fn, fn1 = 1, 1
    for _ in range(100):
        if math.gcd(fn, fn1) != 1:
            fibbad.append((fn, fn1))
        fn, fn1 = fn1, fn + fn1
    add("G3", "斐波那契相邻两项互质吗?", ["斐波那契数", "整除"], "T16 gcd(F_n,F_{n+1})",
        {"扫描域": "前100项"}, "斐波那契相邻项最大公约数为1",
        {"method": "迭代gcd", "range": "前100项", "violations": len(fibbad)},
        "真(已知定理,机器验证)", "及格线产物(验证)", "R_seq/递推×整除")

    # ---- 族 H: 回文/分解 ----
    palprimes = [x for x in palset if x > 1 and x < N and ps[x]]
    add("H1", "回文的数里藏得住质数吗?", ["回文数", "质数"], "T17 回文∩质数(存在)",
        {"扫描域": f"1..{N}"}, "存在回文质数",
        {"method": "集合交", "range": f"1..{N}", "found": palprimes[:12], "count": len(palprimes)},
        "真(存在,例证)", "及格线产物", "R_pal/回文×质数")
    add("H2", "回文质数有无限多个吗?", ["回文数", "质数"], "T18 无穷性",
        {"扫描域": f"1..{N}"}, "存在无穷多个回文质数",
        {"method": "证据+文献", "range": f"1..{N}", "count_sofar": len(palprimes)},
        "悬置(开放)", "开放(相信为真未证明, 需查证)", "H1/升级为无穷性")

    semi_pair = None
    for x in range(1, N):
        if x in semis and x + 1 in semis:
            semi_pair = (x, x + 1)
            break
    add("H3", "两个连续数都是'半素数'(恰两个素因子)?", ["半素数", "连续整数串"], "T19 半素数连续对(存在)",
        {"扫描域": f"1..{N}"}, "存在连续两个半素数",
        {"method": "集合扫描", "range": f"1..{N}", "example": semi_pair},
        "真(存在,例证)", "及格线产物", "R_pal/半素数×连续串")
    add("H4", "这样的'半素数孪生对'无限吗?", ["半素数", "连续整数串"], "T20 无穷性",
        {"example": semi_pair}, "存在无穷多对连续半素数",
        {"method": "证据+文献", "note": "与筛法/孪生族相关"},
        "悬置(开放)", "开放(需查证)", "H3/升级为无穷性")
    return roots, out
