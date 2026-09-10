# -*- coding: utf-8 -*-
"""tools/problem_gate.py — 问题级门(对**定性**开放问题)

为什么需要它: novelty_gate 只判整数序列, 而 counterex_engine 产出的是定性问题
("例外集是什么?"/"是否有限?"/"密度极限?") -> 全被记为"不可判"(全库 85 条)。
本门对这类问题做三件**机器真能做**的事, 并诚实标注机器**做不到**的事。

三个维度:
  D1 结构族分类(不是关键词, 是生成时就确定的形式):
     加性基问题(A+B 覆盖等差数列) -> 文献在加性数论; 迭代/递推/图族同理。
  D2 **机器前沿**: 用机器自己的手段(延伸扫描/放宽周期拟合/放大重拟合)去"尝试结算"。
     这是最有价值的量: 机器把问题推进到哪一步、还差什么。
     - 机器给出候选刻画(未证明) -> 前沿最远
     - 机器找到新反例 -> 削弱了原主张
     - 机器毫无进展 -> 超出机器手段
  D3 渐近信号: 例外集是否**局限于小 n**。
     例外集小且有界 => 猜想渐近成立 => 大概率是**已知渐近定理**的小例外(如 Chen 定理)。
     例外集大且分散 => 真正开放的区域。

诚实边界(写进输出, 不许粉饰):
  真正的"已知性"判定需要**文献门**, 离线做不到(D2/D3 只是信号, 不是判定)。
  因此本门**永远不输出"新"**, 只输出"机器推到了哪 + 该去哪个族查文献"。
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src"))

from ask_dao_machine import counterex_engine as ce  # noqa: E402


# ---------------- D1 结构族(由生成形式决定, 非关键词) ----------------
FAMILIES = {
    "加性基": {
        "detect": lambda j: True,   # 本引擎只产 A+B 覆盖型; 形式即族
        "literature": "加性数论: Schnirelmann 密度 / Goldbach-Euler / Chen(p+P2) / "
                      "Vinogradov(三素数) / Waring-Goldbach",
        "note": "该族具体实例从已证(小例外)到开放(大分散例外)都有, 必须查文献",
    },
}


# ---------------- D2 机器前沿: 机器自己去试 ----------------
def machine_attempt(q, cls, lo, hi):
    """用机器的手段尝试结算该问题。返回 (max_frontier, evidence)。
    frontier: '候选刻画' > '削弱原主张' > '无进展'。"""
    j = q["judgement"]
    a, b = q["binds"]["类A"], q["binds"]["类B"]
    kind = q["id"].rsplit("_", 1)[-1]
    ev = {}

    if kind == "char":
        # 放宽周期拟合上界, 看机器能否给出**候选刻画**
        F = ce.scan(cls, a, b, lo, hi)
        pf = ce.period_fit(F, lo, hi, mmax=300)
        ev["period_fit_mmax300"] = pf
        if pf:
            return "候选刻画", {**ev, "claim": f"恰好是模 {pf[0]} 的剩余类 {pf[1]}"}
        # 例外集是否**落在机器自己的某个类里** + 至多3个散点
        # (这是机器本可以自己做、此前却漏掉的一步: "三角数"就在它自己的类库里)
        # 自纠错: 首版用 `if cname in (a,b): continue` 跳过猜想自身的两类, 结果漏掉了
        # "例外集 ⊆ 三角数"这种**恰恰就在猜想的类里**的关键情形(质数+三角数的真实答案)。
        for cname, C in sorted(cls.items()):
            outside = sorted(n for n in F if n not in C)
            if len(outside) <= 3:
                return "候选刻画", {**ev, "claim":
                                    f"例外集 ⊆ {cname} ∪ {outside}(机器类库内的包含关系)",
                                    "class": cname, "outside": outside}
        # 是否有"平凡刻画": 例外集全部 < 某个小界, 之后成立
        T = max(F) if F else 0
        after = ce.scan(cls, a, b, T + 2, hi)
        ev["trivial_bound_T"] = T
        ev["holds_after_T"] = (len(after) == 0)
        if len(after) == 0 and T <= hi // 10:
            return "候选刻画", {**ev, "claim": f"例外集就是 n<{T} 的小例外(之后恒成立)"}
        return "无进展", ev

    if kind == "finite":
        # 延伸扫描, 看是否还有新例外
        ext_hi = hi + (hi - lo) * 3
        F_ext = ce.scan(cls, a, b, hi + 2, ext_hi)
        ev["extended_to"] = ext_hi
        ev["new_exceptions"] = len(F_ext)
        ev["new_head"] = F_ext[:6]
        if F_ext:
            return "削弱原主张", {**ev, "claim": f"延伸到 {ext_hi} 又见 {len(F_ext)} 个例外 "
                                                 f"(有限性未被支持)"}
        return "无进展", {**ev, "claim": f"延伸到 {ext_hi} 未见新例外(仍未证明有限)"}

    if kind == "density":
        # 放大重拟合: 密度估计是否在更大尺度上稳定
        d1 = ce.density_windows(ce.scan(cls, a, b, lo, hi), lo, hi, span=2000)
        ext_hi = hi + (hi - lo) * 2
        d2 = ce.density_windows(ce.scan(cls, a, b, lo, ext_hi), lo, ext_hi, span=2000)
        n1, n2 = len(d1), len(d2)
        tail1 = sum(d1[n1 // 2:]) / max(len(d1[n1 // 2:]), 1)
        tail2 = sum(d2[n2 // 2:]) / max(len(d2[n2 // 2:]), 1)
        ev.update({"tail_density_at_hi": round(tail1, 5),
                   "tail_density_at_2x": round(tail2, 5),
                   "rel_change": round(abs(tail2 - tail1) / (tail1 or 1e-9), 4)})
        if ev["rel_change"] <= 0.25:
            return "候选刻画", {**ev, "claim": f"尾部密度在两个尺度上稳定于 {tail2}"
                                              f"(极限存在的**证据**, 非证明)"}
        return "无进展", {**ev, "claim": f"密度估计随尺度变化 {ev['rel_change']:.0%}, 未稳定"}

    return "无进展", ev


# ---------------- D3 渐近信号 ----------------
def asymptotic_signal(q, cls, lo, hi):
    """例外集是否局限于小 n -> 猜想是否渐近成立。"""
    j = q["judgement"]
    a, b = q["binds"]["类A"], q["binds"]["类B"]
    F = ce.scan(cls, a, b, lo, hi)
    if not F:
        return {"signal": "无例外", "detail": "区间内恒成立"}
    T = max(F)
    spread = T / hi
    small = T <= hi // 10
    return {"signal": "渐近成立(例外集中在小 n)" if small else "例外分散到大 n",
            "T": T, "span_ratio": round(spread, 4),
            "detail": (f"例外最大 {T}, 扫描上界 {hi} -> "
                       + ("猜想在 n>%d 后成立, 大概率是已知渐近定理的小例外" % T
                          if small else "例外延伸到扫描上界附近, 是真正开放的区域"))}


def grade(q, cls, lo, hi):
    """综合 D1/D2/D3 -> 分级。**永不输出"新"**。"""
    fam = FAMILIES["加性基"]
    frontier, ev = machine_attempt(q, cls, lo, hi)
    asym = asymptotic_signal(q, cls, lo, hi)
    # 分级
    if frontier == "候选刻画":
        g = "R1 机器已给出候选刻画(未证明)"
    elif frontier == "削弱原主张":
        g = "R1 机器已削弱原主张(找到新反例)"
    else:
        g = "R2 超出机器手段(无进展)"
    if asym["signal"].startswith("渐近成立"):
        g += " · 疑似已知渐近定理的小例外"
    return {"id": q["id"], "statement": q["statement"][:78],
            "grade": g, "frontier": frontier, "frontier_evidence": ev,
            "family": "加性基", "literature": fam["literature"],
            "asymptotic": asym,
            "known_status": "需文献门(离线不可判)"}


def main():
    path = HERE / "out/demo/problems_counterex.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    lo, hi = data["problems"][0]["judgement"]["scan"]
    cls = ce._classes(hi * 3)
    rows = [grade(p, cls, lo, hi) for p in data["problems"]]

    print("问题级门 — 机器前沿与已知性信号\n")
    print(f"{'问题':<26}{'分级':<44}渐近信号")
    print("-" * 110)
    for r in rows:
        print(f"{r['id']:<26}{r['grade']:<44}{r['asymptotic']['signal']}")
    print("\n== 机器前沿明细 ==")
    for r in rows:
        print(f"\n[{r['id']}]\n  {r['statement']}")
        print(f"  前沿: {r['frontier']} | {r['frontier_evidence'].get('claim','')}")
        print(f"  渐近: {r['asymptotic']['detail']}")
        print(f"  文献族: {r['literature'][:70]}")

    from collections import Counter
    c = Counter(r["frontier"] for r in rows)
    print(f"\n前沿分布: {dict(c)}")
    print(f"疑似已知渐近定理的小例外: "
          f"{sum(1 for r in rows if r['asymptotic']['signal'].startswith('渐近成立'))}/{len(rows)}")
    print("\n诚实边界: 本门**不输出'新'**。已知性需文献门(离线不可判); D2/D3 只是信号。")
    (HERE / "out/demo/problem_gate.json").write_text(
        json.dumps({"rows": rows, "frontier_dist": dict(c)}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print("已存 out/demo/problem_gate.json")


if __name__ == "__main__":
    main()
