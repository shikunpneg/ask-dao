# -*- coding: utf-8 -*-
"""territory_engine.py — 领地协议(把反例驱动泛化为可插拔的"领地")

LONG_PLAN_V2 Phase 1 的核心: 反例驱动不该只服务加性数论这一块领地。
一个"领地" = 一组 Spec(猜想) + 该族的文献路由。引擎只做与领地无关的通用事:

  扫例外 -> 表征结构 -> 诚实探针(向界外延伸) -> 产出开放问题(status=UNRESOLVED)

领地差异全部收敛到 Spec 的两个函数里:
  holds(n)  —— 该猜想对 n 是否成立(False => n 是例外)
  classes   —— 具名对象类, 供**机器自主**给出"例外集 ⊆ 某个类"的候选刻画

纪律(承接 R24/R25): 机器只提它自己结算不了的问题; judgement 只带反例证据, 不带判定。
"""
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set, Any

from .model import ProblemRecord, TreeRoot, UNRESOLVED


@dataclass
class Spec:
    """一个猜想。领地的全部差异都在这里。"""
    id: str
    claim: str                                   # 人话陈述, 如 "每个 n 可写成 回文数 + 平方数"
    holds: Callable[[int], bool]                 # True = 无例外
    classes: Dict[str, Set[int]] = field(default_factory=dict)  # 具名类, 供刻画
    params: Dict[str, Any] = field(default_factory=dict)
    step: int = 1                                # 扫描步长(偶数为 2)
    quantity: str = ""                           # 参数量词域(良构用)


@dataclass
class Territory:
    name: str
    family: str          # 结构族(决定文献路由)
    literature: str      # 该族的文献线索
    motifs: List[str]
    seed: str
    specs: Callable[[], List[Spec]]


# ---------------- 通用: 表征 ----------------
def period_fit(F: List[int], lo: int, hi: int, mmax: int = 60):
    """例外集是否**恰好**是某组模 m 剩余类。返回 (m, residues) 或 None。"""
    fs = set(F)
    for m in range(2, mmax + 1):
        residues = {x % m for x in F}
        if not residues:
            continue
        pred = {n for n in range(lo, hi + 1) if (n % m) in residues}
        if pred == fs:
            return m, sorted(residues)
    return None


def density_windows(F: List[int], lo: int, hi: int, span: int = 2000):
    out, a = [], lo
    while a < hi:
        b = min(a + span, hi)
        tot = len(range(a, b)) or 1
        out.append(round(sum(1 for x in F if a <= x < b) / tot, 4))
        a = b
    return out


def classify(F: List[int], lo: int, hi: int, classes: Dict[str, Set[int]]):
    """给例外集一个结构描述。**不预设答案**, 只用机器有的手段。"""
    if not F:
        return {"kind": "空", "n": 0, "examples": []}
    pf = period_fit(F, lo, hi)
    d = density_windows(F, lo, hi)
    tail = d[len(d) // 2:] or [0.0]
    info = {"n": len(F), "first": min(F), "last": max(F),
            "at_boundary": max(F) >= hi - 4, "examples": F[:10],
            "density_all": d,
            "density_tail_stable": (max(tail) - min(tail)) <= 0.01,
            "density_tail": round(sum(tail) / len(tail), 4)}
    if pf:
        info["kind"] = "周期"
        info["period"], info["residues"] = pf
    elif len(F) <= 40:
        info["kind"] = "有限稀疏"
    else:
        info["kind"] = "非周期(疑似无限/稠密)"
    # 机器自主刻画: 例外集 ⊆ 某个具名类 ∪ {至多3个散点}
    info["class_fit"] = None
    for cname, C in sorted(classes.items()):
        outside = sorted(n for n in F if n not in C)
        if len(outside) <= 3:
            info["class_fit"] = {"class": cname, "outside": outside}
            break
    # 小例外界: 例外全在 T 之前, 之后恒成立
    T = max(F)
    info["small_bound"] = T if T <= hi // 10 else None
    return info


def probe(spec: Spec, lo: int, hi: int) -> dict:
    """诚实探针: 向 hi 之外延伸, 看是否还有新例外。"""
    ext_lo, ext_hi = hi + spec.step, hi + (hi - lo)
    F_ext = [n for n in range(ext_lo, ext_hi + 1, spec.step) if not spec.holds(n)]
    return {"ext_range": [ext_lo, ext_hi], "n_beyond": len(F_ext),
            "beyond_head": F_ext[:5], "extends": len(F_ext) > 0}


# ---------------- 通用: 产出 ----------------
def questions(spec: Spec, info: dict, pr: dict, lo: int, hi: int) -> List[dict]:
    """把例外集的结构变成问题。机器无法结算 => UNRESOLVED。"""
    qs, head = [], spec.claim
    if info["kind"] == "周期":
        m, R = info["period"], info["residues"]
        qs.append({"suffix": "char",
                   "statement": f"{head} 的例外集在 [{lo},{hi}] 内**恰好**是模 {m} 的剩余类 {R}"
                                f"(共 {info['n']} 个)。这个刻画是精确的吗——为什么恰好是这些剩余类?",
                   "crit": f"证明对该模 {m} 的所有剩余类成立, 或给出刻画之外的例外"})
    elif info.get("class_fit"):
        cf = info["class_fit"]
        extra = f" ∪ {cf['outside']}" if cf["outside"] else ""
        qs.append({"suffix": "char",
                   "statement": f"{head} 的例外集 ⊆ **{cf['class']}**{extra}"
                                f"(机器用自身类库拟合, 共 {info['n']} 个)。"
                                f"这个包含关系是精确的吗——为什么例外恰好落在这一类里?",
                   "crit": f"证明例外集 = {cf['class']} 的某个子族, 或给出反例"})
    elif info.get("small_bound"):
        qs.append({"suffix": "char",
                   "statement": f"{head} 的例外集恰好 {info['n']} 个, 最大者 {info['last']}"
                                f"(前几个 {info['examples'][:6]}), 之后恒成立。"
                                f"**是什么刻画了这批小例外**?",
                   "crit": "给出小例外集的精确刻画并证明, 或指出刻画不存在的理由"})
    else:
        qs.append({"suffix": "char",
                   "statement": f"{head} 的例外集在 [{lo},{hi}] 内共 {info['n']} 个, "
                                f"最大者 {info['last']}(前几个 {info['examples'][:6]})。"
                                f"**是什么刻画了这个例外集**?",
                   "crit": "给出例外集的精确刻画(同余类/代数条件)并证明, 或指出刻画不存在的理由"})
    if info["at_boundary"] or pr["extends"]:
        ev = (f"最后例外在 {info['last']}; 延伸到 {pr['ext_range'][1]} 又见 {pr['n_beyond']} 个新例外"
              if pr["extends"] else f"最后例外在 {info['last']}, 紧贴扫描上界 {hi}")
        qs.append({"suffix": "finite",
                   "statement": f"{head}: {ev}。例外集是**有限**的吗? "
                                f"(机器的全部本事是'扫到上界', 扫不出这个问题)",
                   "crit": "证明例外有限并给出可证上界, 或构造扫描上界之外的新例外"})
    if info["kind"] == "非周期(疑似无限/稠密)" and info["density_tail_stable"] \
            and 0 < info["density_tail"] < 0.9:
        qs.append({"suffix": "density",
                   "statement": f"{head} 的例外集尾部密度稳定在 {info['density_tail']}"
                                f"(逐窗 {info['density_all'][-4:]})。密度极限是否存在? 极限值是多少?",
                   "crit": "证明密度极限存在并定值, 或证明其不存在"})
    return qs


def emit(t: Territory, spec: Spec, info: dict, pr: dict, qs: List[dict],
         lo: int, hi: int) -> List[ProblemRecord]:
    root = TreeRoot(f"R_{t.name}", f"领地·{t.family}", "数学", t.motifs, t.seed)
    out = []
    for q in qs:
        out.append(ProblemRecord(
            f"CX_{spec.id}_{q['suffix']}", "数学",
            f"机器扫出「{spec.claim}」的例外集后, 反例自身的结构成了新问题",
            t.motifs + [info["kind"]],
            f"反例驱动({t.family})",
            q["statement"],
            {"method": "反例集结构拟合(机器枚举)", "examples": info["examples"],
             "count": info["n"], "period": info.get("period"),
             "residues": info.get("residues"), "class_fit": info.get("class_fit"),
             "small_bound": info.get("small_bound"), "scan": [lo, hi], "probe": pr,
             "settleable_by_machine": False, "crit": q["crit"],
             "params": spec.params},
            status=UNRESOLVED, honesty="机器提出·未结算(需证明或反例)",
            binds={**{k: str(v) for k, v in spec.params.items()},
                   "扫描": f"{lo}..{hi}"},
            tree={"parent": root.id, "edge": spec.claim[:40]}))
    return out


# ---------------- 通用: 跑一个领地 ----------------
def run_territory(t: Territory, lo: int, hi: int, max_exc_density: float = 0.05):
    """max_exc_density: 例外稠密阈值。

    诚实守卫(实测教训): 若例外占扫描空间的很大比例(如 base-2 回文数+素数 达 50%),
    说明**猜想本身就是假的**, 例外集不是"特殊对象"——此时问"什么刻画了例外集"是坏问题
    (大多数 n 都是例外, 无结构可言)。只有例外**稀疏**时, 例外集才是一个值得刻画的对象。
    """
    specs = t.specs()
    recs, report = [], []
    total_n = len(range(lo, hi + 1))
    for spec in specs:
        F = [n for n in range(lo, hi + 1, spec.step) if not spec.holds(n)]
        scanned = len(range(lo, hi + 1, spec.step))
        dens = len(F) / max(scanned, 1)
        # 无例外: 机器未能结算"是否恒成立" -> 这本身是个开放问题
        if not F:
            info = {"kind": "无例外(区间内)", "n": 0, "examples": []}
            qs = [{"suffix": "holds",
                   "statement": f"{spec.claim} —— 机器扫遍 [{lo},{hi}] 未发现任何例外。"
                                f"这个猜想是**定理**吗? (机器只能验证到上界, 证不了)",
                   "crit": "证明该猜想恒成立, 或给出扫描上界之外的第一个反例"}]
            recs += emit(t, spec, info, {}, qs, lo, hi)
            report.append({"spec": spec.id, "claim": spec.claim, "n": 0, "density": 0.0,
                           "kind": info["kind"], "verdict": "无例外 -> 产出 1 个开放问题(是否定理)"})
            continue
        # 例外稠密 => 猜想被否证, 例外集非特殊对象, 不产出问题
        if dens > max_exc_density:
            report.append({"spec": spec.id, "claim": spec.claim, "n": len(F),
                           "density": round(dens, 4), "kind": "—",
                           "verdict": f"**猜想被否证**(例外占 {dens:.0%} > {max_exc_density:.0%}); "
                                      f"例外集非特殊对象, 不产出问题(诚实守卫)"})
            continue
        info = classify(F, lo, hi, spec.classes)
        info["density_overall"] = round(dens, 4)
        pr = probe(spec, lo, hi)
        qs = questions(spec, info, pr, lo, hi)
        recs += emit(t, spec, info, pr, qs, lo, hi)
        report.append({"spec": spec.id, "claim": spec.claim, "n": info["n"],
                       "density": round(dens, 4), "kind": info["kind"], "last": info["last"],
                       "at_boundary": info["at_boundary"],
                       "class_fit": info.get("class_fit"),
                       "small_bound": info.get("small_bound"),
                       "probe_extends": pr["extends"], "n_beyond": pr["n_beyond"],
                       "verdict": f"产出 {len(qs)} 个开放问题"})
    roots = [TreeRoot(f"R_{t.name}", f"领地·{t.family}", "数学", t.motifs, t.seed)]
    return roots, recs, {"territory": t.name, "family": t.family,
                         "literature": t.literature, "specs": report}
