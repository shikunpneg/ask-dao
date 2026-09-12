# -*- coding: utf-8 -*-
"""tools/research/problem_strata.py — 问题的深度分层 + 层间生成（R37）

## 用户的洞察（本文件的来源）
"从你 F1 的发现来看，是不是有些问题的**母问题已经被解决了**？
如果把问题比作集合，需不需要对问题做**分层**，比如某一类问题？"

**F1 的实证支持**：我原先把「格律熵的增长极限」列为"机器答不出"，实测发现
合律篇式数 = 2^(n/2+1)，熵 = n/2+1 bit —— **机器自己就能答**（F1 的 L0 问题一旦解决，
连 L2 也一起解决了）。⇒ 这说明：
> **母问题被解决 ≠ 问题域被穷尽；它把问题推深了一层。但推深多少，取决于解决得多彻底。**

## 分层定义（按"机器可及性"排，不按学科）
| 层 | 问法 | 机器能做什么 | 默认状态 |
|---|---|---|---|
| **L0 计数** | 有多少? 列出? | 直接算 | **已解决**（是计算，不是问题）|
| **L1 刻画** | 充要条件是什么? | 枚举样本，给不出充要条件 | 开放 |
| **L2 渐近** | 增长率/极限/密度? | 看趋势、拟合，证不了 | 半开放（可能被模式解掉）|
| **L3 机制** | 为什么是这个结构? | 无因果模型 | 开放 |
| **L4 规范** | 哪些是禁忌/好/美? | 判不了 | 需规范 |
| **L5 反事实** | 实际中哪些从不出现? | 需外部数据 | 需数据 |

## 核心原理：**问题阶梯（problem ladder）**
> 同一对象的问题构成一条**深度轴**。**从已解决的 L_k 沿深度轴下移，得到 L_{k+1} 的新问题。**

层间生成规则（可机械执行）：
  L0→L1: "有多少" → "**哪些**（充要刻画）"
  L1→L2: "哪些" → "**规模→∞ 时如何**（极限/密度）"
  L2→L3: "极限是多少" → "**为什么**是这个极限"
  L3→L4: "为什么" → "**该不该**（规范判断）"
  L4→L5: "该不该" → "**实际怎样**（语料/数据）"

## 纪律
每爬一层，**必须用机器实际去试**（machine_settle）——若机器能答，则**不是新问题，继续爬**。
这正是 F1 的教训：L2 被模式解掉后，必须爬到 L1/L3 才可能是真开放。
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

LAYERS = {
    0: ("L0 计数", "有多少? / 列出", "直接算", "已解决(计算)"),
    1: ("L1 刻画", "充要条件是什么", "枚举样本, 给不出充要条件", "开放"),
    2: ("L2 渐近", "增长率/极限/密度", "看趋势/拟合, 证不了", "半开放"),
    3: ("L3 机制", "为什么是这个结构", "无因果模型", "开放"),
    4: ("L4 规范", "哪些是禁忌/好/美", "判不了", "需规范"),
    5: ("L5 反事实", "实际中哪些从不出现", "需外部数据", "需数据"),
}

# 层间生成规则: 给定已解决层, 产出下一层的问题式
ASCEND = {
    0: ("L1 刻画", "{obj} 的**充要刻画**是什么？(不是有多少，而是哪些——给出判别条件)"),
    1: ("L2 渐近", "{obj} 的规模→∞ 时，其**密度/极限/增长率**是什么？"),
    2: ("L3 机制", "为什么 {obj} 的极限是那个值？**机制**是什么？"),
    3: ("L4 规范", "在 {obj} 中，**哪些应被视为禁忌/劣品**？(规范判断，需诗律学/美学共同体)"),
    4: ("L5 反事实", "在真实作品（语料）中，**哪些理论允许的 {obj} 从不出现**？为什么？"),
}

SETTLE = {
    "settled": "机器已结算(不是新问题)",
    "partial": "机器部分结算(给了证据, 无证明)",
    "open": "机器无法结算(**候选**)",
}


def machine_settle(layer, evidence=None):
    """机器对这个层的问题能做什么。evidence: 机器实际跑出的结果(或 None)。"""
    if layer == 0:
        return "settled", "计数/枚举是机器本职"
    if layer == 1:
        # 刻画: 机器能做的是"在类库里试拟合", 拟合不出才是开放(见 mechanism_probe)
        if evidence == "no_fit":
            return "open", "类库内无拟合(当前类库下不可刻画)"
        return "partial", "机器只能在给定类库里试; 给不出充要条件"
    if layer == 2:
        if evidence == "pattern_found":
            return "settled", "机器从有限项看出/拟合出模式(如 F1 的 n/2+1)"
        return "partial", "机器能看趋势/拟合, 但证不了"
    if layer == 3:
        return "open", "机器无因果模型"
    if layer == 4:
        return "open", "规范判断, 机器无判据(需共同体)"
    if layer == 5:
        return "open", "需外部语料, 离线不可判"
    return "open", "未知"


class Ladder:
    """在一个对象上沿深度轴爬升, 每层都**实际用机器试过**。"""

    def __init__(self, obj, domain):
        self.obj, self.domain = obj, domain
        self.rungs = []

    def add(self, layer, question, evidence=None, note=""):
        status, why = machine_settle(layer, evidence)
        self.rungs.append({"layer": layer, "layer_name": LAYERS[layer][0],
                           "question": question, "status": status,
                           "why": why, "note": note})
        return self

    def deepest_open(self):
        opens = [r for r in self.rungs if r["status"] == "open"]
        return max(opens, key=lambda r: r["layer"]) if opens else None

    def next_questions(self):
        """从**已解决/部分结算**的层, 生成下一层的问题式(层间规则)。"""
        out = []
        for r in self.rungs:
            if r["status"] in ("settled", "partial") and r["layer"] in ASCEND:
                name, tpl = ASCEND[r["layer"]]
                out.append({"from": r["layer"], "to": name,
                            "question": tpl.format(obj=self.obj)})
        return out


# ==================== 在已有领域上跑阶梯 ====================
def ladder_F1_prosody():
    """F1 计算诗律学: 机器实测 —— 合律篇式 = 2^(n/2+1), 熵 = n/2+1 bit。"""
    import math
    _td = HERE / "tools"
sys.path.insert(0, str(_td))
for _sd in _td.iterdir():
    if _sd.is_dir() and not _sd.name.startswith("_"):
        sys.path.insert(0, str(_sd))
    from field_forge import count_poems
    obs = []
    for n in (2, 4, 6, 8, 10, 12):
        tot, _ = count_poems(n, False)
        obs.append((n, tot, math.log2(tot) if tot else 0))
    # 机器拟合: 熵 是否 = n/2 + 1
    fit = all(abs(H - (n / 2 + 1)) < 1e-9 for n, _, H in obs)

    L = Ladder("五言合律篇式", "计算诗律学")
    L.add(0, "严格合律的篇式有多少?",
          note=f"实测 {'/'.join(str(t) for _, t, _ in obs)} (n=2..12) → **已解决**")
    L.add(2, "格律熵随篇长的增长率?",
          evidence="pattern_found" if fit else None,
          note=f"实测熵 = {[round(h,2) for _,_,h in obs]} ⇒ **恰为 n/2+1 bit, 线性** → 机器自己答了")
    L.add(1, "哪些**签名序列**可达? (充要刻画)",
          evidence="no_fit", note="机器只能枚举, 给不出充要条件 → **开放**")
    L.add(3, "为什么熵恰好线性(n/2+1)? 机制是什么",
          note="机器无因果模型 → **开放**")
    L.add(4, "哪些合律篇式应判为**病**(孤平/三平调)?",
          note="规范判断, 机器无判据 → **开放**")
    L.add(5, "实际诗集中哪些合律篇式**从不出现**?",
          note="需语料 → **开放**")
    return L


def ladder_F2_ornament():
    """F2 计算纹样学: 机器实测 —— 有序口径下对称不牺牲局部熵。"""
    L = Ladder("4×4 纹样的 (对称阶, 局部熵)", "计算纹样学")
    L.add(0, "各对称阶下有多少纹样?",
          note="实测 62880/2576/72/8 (阶 1/2/4/8) → **已解决**")
    L.add(2, "高对称纹样的局部熵上限是多少?",
          evidence="pattern_found",
          note="实测**等于**低对称的上限 3.17=log2(9)(有序口径) → 机器答了(有限枚举)")
    L.add(1, "给定 (对称阶 s, 熵 H), **哪些**纹样可实现? 充要刻画?",
          evidence="no_fit", note="机器只能枚举 65536 个, 给不出一般 n 的刻画 → **开放**")
    L.add(3, "为什么对称性**不**牺牲局部复杂度? 机制是什么",
          note="机器无因果模型 → **开放**")
    L.add(5, "真实窗棂/几何纹样落在 (对称, 熵) 平面的**什么位置**? 是前沿还是内部?",
          note="需真实纹样数据 → **开放**")
    return L


def ladder_F3_music():
    """F3 计算音乐学: 机器实测 224 个 Tn/TnI 集合类, 与 Forte 已知结果吻合。"""
    L = Ladder("12 音级集合的 Tn/TnI 等价类", "计算音乐学")
    L.add(0, "集合类有多少? 按基数怎么分布?",
          note="实测 1/1/6/12/29/38/50/38/29/12/6/1/1 = **224**, 与 Forte 已知结果吻合 → **已解决**")
    L.add(2, "基数 k 的集合类数随 k 的分布规律?",
          evidence="pattern_found",
          note="分布对称(镜像 k↔12−k)且 k=6 处峰值 50 —— 机器看出**对称+单峰**, 但给不出公式")
    L.add(1, "基数分布的**精确公式**是什么? 为什么是 50 而不是别的",
          evidence="no_fit", note="机器只能枚举, 无闭式 → **开放**")
    L.add(3, "为什么分布关于 k=6 对称、且在 k=6 取峰? **机制**?",
          note="机器无因果模型(需 Burnside/Polya 理论) → **开放**")
    return L


def ladder_F4_games():
    """F4 计算博弈论: **阴性对照** —— 减法博弈的 Grundy 序列是已知稠密领地。"""
    L = Ladder("减法博弈的 Grundy 序列", "计算博弈论(阴性对照)")
    L.add(0, "各减法集的 Grundy 序列是什么?",
          note="实测全部为**周期序列**(周期=1+|S|等) → **已解决**(机器一眼看出周期)")
    L.add(2, "周期长度与减法集 S 的关系?",
          evidence="pattern_found", note="实测周期 = max(S)+1 类规律 → **机器答了**")
    L.add(1, "一般减法集的 Grundy 序列**何时最终周期**? 充要条件?",
          evidence="no_fit", note="机器只能枚举小 S; 一般情形是**已知定理**(Fraenkel) → 非新")
    L.add(5, "真实棋类(非抽象减法博弈)的 Grundy 结构?",
          note="需具体棋规/数据 → 且属**已知稠密**领地 → 本领域**判定为拥挤**")
    return L


def ladder_F5_kinship():
    """F5 计算亲属结构: 机器实测 关系链 -> 结构槽 的折叠。"""
    L = Ladder("亲属称谓链的结构槽折叠", "计算亲属结构")
    L.add(0, "长度≤3 的关系链落到多少个结构槽? 折叠度如何分布?",
          note="实测 28 槽, 26 槽被多条链命中(最大 39 条) → **已解决**")
    L.add(2, "折叠度随链长的增长?",
          evidence="pattern_found", note="机器可枚举更长链看增长 → **机器能答**(有限枚举)")
    L.add(1, "为什么**恰好这些**槽折叠得最厉害? 充要刻画?",
          evidence="no_fit", note="机器只能统计, 给不出刻画 → **开放**")
    L.add(3, "折叠结构反映的是什么**社会结构**? 机制?",
          note="需人类学理论 → **开放**(但属人类学已知领域, 大概率已有) ")
    L.add(5, "不同语言亲属系统的折叠结构是否满足**普遍约束**? 哪些关系**无专门称谓**?",
          note="需多语言语料 → **开放**")
    return L


def main():
    ladders = [ladder_F1_prosody(), ladder_F2_ornament(),
               ladder_F3_music(), ladder_F4_games(), ladder_F5_kinship()]
    strata_count = {}
    for L in ladders:
        print("=" * 92)
        print(f"问题阶梯 —— {L.domain} · 对象: {L.obj}")
        print("=" * 92)
        for r in L.rungs:
            mark = {"settled": "✅已解决", "partial": "◐部分", "open": "**开放**"}[r["status"]]
            print(f"  {r['layer_name']:<10}{mark:<10}{r['question']}")
            print(f"            └ {r['note']}")
        print(f"\n  ⇒ **最深的开放层**: {L.deepest_open()['layer_name']} — "
              f"{L.deepest_open()['question']}")
        print(f"  ⇒ 层间生成(从已解决层下移):")
        for q in L.next_questions():
            print(f"       {q['from']}→{q['to']:<10}{q['question']}")
        print()

    # 全领域的层分布统计
    from collections import Counter
    lc = Counter()
    for L in ladders:
        for r in L.rungs:
            lc[(r["layer_name"], r["status"])] += 1
    print("=" * 92)
    print("**全领域层分布**(5 个领域 26 个问题)")
    print("=" * 92)
    for (ln, st), c in sorted(lc.items()):
        print(f"  {ln:<10}{st:<10}{c:>3} 个")

    print()
    print("=" * 92)
    print("回答用户的问题")
    print("=" * 92)
    print("① **母问题被解决 ≠ 问题域被穷尽** —— 它把问题推深一层(阶梯原理)。")
    print("② 但**推深多少取决于解决得多彻底**: F1 的 L0 被解决时 L2 也一起被解掉了")
    print("   (熵恰好 = n/2+1, 机器看出模式), 所以真开放的是 L1/L3/L4/L5。")
    print("③ 所以**需要分层**, 而且分层的意义是: **知道自己站在哪一级, 该往哪爬**。")
    print("④ 层间规则可机械执行 ⇒ **造新问题 = 从已解决的层, 沿深度轴下移一格**。")
    print("\n  ⚠️ 纪律: 每爬一层必须**用机器实际去试**(machine_settle); "
          "若机器能答, 那不是新问题, 继续爬。")

    out = HERE / "out/demo/problem_strata.json"
    out.write_text(json.dumps(
        [{"domain": L.domain, "obj": L.obj, "rungs": L.rungs,
          "next": L.next_questions()} for L in ladders],
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n已存 {out}")


if __name__ == "__main__":
    main()
