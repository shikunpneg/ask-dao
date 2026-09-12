# -*- coding: utf-8 -*-
"""tools/research/s2_bounded.py — S2 广义Collatz停时"有界性"严格复算(纠错版)

背景: 早期(R7-R15)记录称 "max over 奇q<=Q 的停时单调爬升, 表观有界未证"。
复算发现两处方法学缺陷:
  (1) "max over q<=Q" 是**运行最大值**, 对 Q 单调递增是集合扩张的同义反复, 不含信息;
  (2) 停时对 cap/esc 截断敏感, 且 p>=5 时部分轨道发散, 到达1的 n 占比本身随 p 变。
本脚本改用**滑窗统计量**(窗口内 max/中位) + **存活率** + **无截断计数**, 重新判定。

判定口径: 窗口统计量随 q 中心单调上升 => 无界(增长); 持平 => 有界(该窗口尺度内)。
"""
import json
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

HERE = Path(__file__).resolve().parent.parent
N = 20000
CAP = 20000
ESC = 10 ** 9


def scan(p, q, N=N, cap=CAP, esc=ESC):
    """返回 (最大停时, argmax n, 到达1的n数)。超过截断的轨道记 -1 不计入。"""
    memo = {1: 0}
    best, arg, reached = 0, 0, 0
    for n in range(2, N + 1):
        x = n
        chain = []
        while x != 1 and x not in memo:
            if x > esc:
                break
            chain.append(x)
            x = p * x + q if x % 2 else x // 2
            if len(chain) > cap:
                break
        if x == 1 or x in memo:
            b = memo.get(x, 0)
            for y in reversed(chain):
                b += 1
                memo[y] = b
            reached += 1
            if memo[n] > best:
                best, arg = memo[n], n
        else:
            for y in chain:
                memo[y] = -1
    return best, arg, reached


def main():
    windows = [(1, 201), (401, 601), (801, 1001), (1801, 2001), (4801, 5001)]
    out = {}
    verdicts = {}
    for p in (3, 5, 7):
        rows = []
        for lo, hi in windows:
            qs = list(range(lo, hi, 2))
            vals, reached = [], []
            for q in qs:
                b, _a, r = scan(p, q)
                vals.append(b)
                reached.append(r)
            rows.append({
                "q_lo": lo, "q_hi": hi,
                "win_max": max(vals),
                "win_median": int(statistics.median(vals)),
                "win_mean": round(statistics.mean(vals), 1),
                "survival_frac": round(statistics.mean(reached) / (N - 1), 4),
            })
        # 有界性判定: 窗口 max 与中位是否随 q 中心单调上升
        meds = [r["win_median"] for r in rows]
        maxs = [r["win_max"] for r in rows]
        med_mono = all(meds[i + 1] > meds[i] for i in range(len(meds) - 1))
        max_mono = all(maxs[i + 1] > maxs[i] for i in range(len(maxs) - 1))
        # 幂律拟合(中位 vs 窗口中心)
        xs = [math.log((r["q_lo"] + r["q_hi"]) / 2) for r in rows]
        ys = [math.log(r["win_median"]) for r in rows]
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        a = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
        verdicts[p] = {
            "median_monotone_up": med_mono,
            "winmax_monotone_up": max_mono,
            "growth_exponent_a": round(a, 3),
            "verdict": "无界(随q增长)" if med_mono else "窗口内有界(持平)",
        }
        out[p] = rows
        print(f"=== p={p} ===")
        for r in rows:
            print(f"  q∈[{r['q_lo']},{r['q_hi']}) 窗口max={r['win_max']:<5} 中位={r['win_median']:<5} "
                  f"存活率={r['survival_frac']:.3f}")
        print(f"  -> 中位单调↑={med_mono} 窗口max单调↑={max_mono} 幂指数a={a:.3f} "
              f"=> {verdicts[p]['verdict']}")
    payload = {
        "note": "max over q<=Q 是运行最大值(同义反复); 本节用滑窗统计量。",
        "N": N, "cap": CAP, "windows": windows,
        "by_p": out, "verdicts": verdicts,
    }
    (HERE / "out/demo/s2_bounded.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n已存 out/demo/s2_bounded.json")


if __name__ == "__main__":
    main()
