# -*- coding: utf-8 -*-
"""motif_growth.py — Phase A: 母题扩张(实例化晋升 v1)
  step1 读 derived_motifs.json(math-route 复合母题)
  step2 对可在本机生成载体的对象类, 做小规模试判(两数和覆盖/纪录)得到证据
  step3 stage: 有非平凡结果 -> confirmed(带 parent/证据) ; 无载体 -> hypothesis(待 carrier)
输出: out/demo/grown_motifs.json
"""
import json
from pathlib import Path

from .judges_math import sieve

HERE = Path(__file__).resolve().parent.parent


def _carriers(n=20000):
    """为数学对象类提供载体生成函数(小规模)"""
    ps = sieve(n)
    primes = [i for i in range(2, n) if ps[i]]
    primeset = set(primes)
    oddcomp = [x for x in range(9, n, 2) if not ps[x]]
    oc = set(oddcomp)
    sq = sorted(x * x for x in range(1, int(n ** 0.5) + 1))
    sqset = set(sq)
    tri = sorted(t for t in (i * (i + 1) // 2 for i in range(1, 210)) if t <= n)
    triset = set(tri)
    fib = [1, 1]
    while fib[-1] + fib[-2] < n:
        fib.append(fib[-1] + fib[-2])
    fibset = set(fib)
    pals = sorted(x for x in range(2, n) if str(x) == str(x)[::-1])
    palset = set(pals)
    pow2 = sorted(1 << k for k in range(0, 15))
    pow2set = set(pow2)
    return {
        "质数": (primes, primeset), "奇合数": (oddcomp, oc), "平方数": (sq, sqset),
        "三角数": (tri, triset), "斐波那契数": (fib, fibset), "回文数": (pals, palset),
        "2的幂": (pow2, pow2set),
    }


def _probe_two_sum(a_list, b_set, hi=8000, cap=300):
    """小规模两数和覆盖试判: 返回 {complete, threshold/fails_head}"""
    fails = []
    run = 0
    n = 6
    while n <= hi:
        ok = False
        for a in a_list:
            if a >= n:
                break
            if (n - a) in b_set:
                ok = True
                break
        if not ok:
            fails.append(n)
            run += 1
            if run > cap:
                return {"complete": False, "fails_head": fails[:10]}
        else:
            run = 0
        n += 2
    return {"complete": True, "fails_head": fails[:10],
            "threshold": (max(fails) + 2) if fails else 6}


def grow(derived_path: Path, out_path: Path, max_items: int = 30) -> dict:
    car = _carriers()
    names = list(car.keys())
    grown = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            if len(grown) >= max_items:
                break
            na, nb = names[i], names[j]
            a_list = car[na][0]
            b_set = car[nb][1] if car[nb][1] is not None else set(car[nb][0])
            res = _probe_two_sum(a_list, b_set)
            if res["complete"] and res["threshold"] is not None and res["threshold"] < 8000:
                stage = "confirmed"
            elif res["complete"]:
                stage = "needs_extend"   # 阈值贴着扫描边界 -> 前问题态
            else:
                stage = "hypothesis"
            grown.append({
                "id": f"GM{len(grown):03d}",
                "derived": f"{na} × {nb}",
                "type": "配对集(对象类×对象类)",
                "parents": [f"数学::{na}", f"数学::{nb}"],
                "cross": False,
                "frame": "F_threshold_sum",
                "route": "math",
                "stage": stage,
                "probe": res,
            })
        else:
            continue
        break
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(grown, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"grown": len(grown),
            "confirmed": sum(1 for g in grown if g["stage"] == "confirmed"),
            "needs_extend": sum(1 for g in grown if g["stage"] == "needs_extend"),
            "hypothesis": sum(1 for g in grown if g["stage"] == "hypothesis"),
            "file": str(out_path)}


if __name__ == "__main__":
    print(grow(HERE / "out/demo/derived_motifs.json", HERE / "out/demo/grown_motifs.json"))
