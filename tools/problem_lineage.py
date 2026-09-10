# -*- coding: utf-8 -*-
"""tools/problem_lineage.py — 问题谱系：把孤立问题还原成**整根树枝**（R38）

## 用户的提醒（本文件的来源）
"我们既然是在找新问题，但是对于知识来说，**只有孤立的问题是不行的**，
还需要这一整只树枝，需要它的**来龙去脉**，也就是**前问题**。"

⇒ 一个问题的**价值不在它的陈述里，而在它在树上的位置**：
  它从哪个母题长出、踏过哪些前问题、解决后会解锁什么、以及它在别的领域有没有同胞。

## 谱系四段（祖先 / 自身 / 后代 / 侧枝）
  祖 ANCESTORS : 母题 → 前问题链(已解决的下层) → 本问题       "它是怎么长出来的"
  本 SELF      : 问题在深度轴上的位置(L0–L5)                   "它站在哪一级"
  孙 DESCENDANTS: 解决后沿层间规则解锁的下一层问题             "它会通向哪里"
  旁 LATERALS  : 同一(对象|方法)在别的领域的同胞                "同样的结构还出现在哪"

## 关键: 层间规则即**树的边**
  祖先链 = 沿深度轴**向下**的边;  后代链 = 沿深度轴**向上**的边。
  所以分层不是分类学, 是**谱系学** —— 这正是用户说的"树枝"。
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
sys.path.insert(0, str(HERE / "src"))

from problem_strata import LAYERS, ASCEND, machine_settle  # noqa: E402


# ---------- (对象, 方法) 矩阵: 用于找"侧枝"与"未配对的空格" ----------
PAIRS = [
    # (领域, 对象, 方法, 是否已实例化)
    ("计算诗律学", "近体诗格律", "形式文法+熵", True),
    ("计算纹样学", "周期纹样", "对称群+局部熵", True),
    ("计算音乐学", "12音级集合", "Tn/TnI群论", True),
    ("计算博弈论", "减法博弈", "Sprague-Grundy", True),
    ("计算亲属结构", "亲属称谓", "关系代数", True),
    # ---- 以下为**尚未实例化**的配对: 下一个领域候选 ----
    ("计算诗律学", "近体诗格律", "对称群(对/粘=Z2作用)", False),
    ("计算音乐学", "12音级集合", "信息熵(集合的熵分布)", False),
    ("计算纹样学", "周期纹样", "形式文法(纹样的生成文法)", False),
    ("计算亲属结构", "亲属称谓", "对称群(辈分翻转)", False),
    ("计算博弈论", "减法博弈", "偏序/格(博弈序)", False),
    ("计算诗律学", "词牌长短句", "形式文法", False),
    ("计算音乐学", "旋律轮廓", "对称群+熵", False),
    ("计算纹样学", "分形纹样", "尺度标度", False),
]


def lateral_links(obj, method, top=3):
    """同一对象换方法 / 同一方法换对象 —— 即"侧枝"与"未配对空格"。"""
    same_obj = [p for p in PAIRS if p[1] == obj and p[2] != method]
    same_m = [p for p in PAIRS if p[2] == method and p[1] != obj]
    return {"same_obj_other_method": same_obj[:top],
            "same_method_other_obj": same_m[:top],
            "unpaired_slots": [p for p in PAIRS if not p[3]][:top]}


# ---------- 谱系构建 ----------
class Lineage:
    def __init__(self, statement, domain, obj, layer, motifs=None):
        self.statement, self.domain, self.obj = statement, domain, obj
        self.layer, self.motifs = layer, (motifs or [])

    def ancestors(self):
        """祖: 母题 → 已解决的下层(前问题) → 本问题。

        自纠错(第 23 次): 首版用 `ASCEND[k][1]` —— 那是"从 k 升到 k+1"的**下一层**问法,
        于是 `前问题@L0` 显示成了 L1 的模板(层级错位)。
        前问题在第 k 层, 应当用 **`LAYERS[k]` 自己的问法**。
        """
        chain = []
        for m in self.motifs:
            chain.append({"kind": "母题", "text": m})
        for k in sorted(LAYERS):
            if k >= self.layer:
                break
            name, ask, _cap, _default = LAYERS[k]
            chain.append({"kind": f"前问题@{name}", "text": f"{name}层问法: {ask}",
                          "status": "已解决(机器可算)" if k in (0, 2) else "—"})
        chain.append({"kind": f"**本问题**@{LAYERS[self.layer][0]}",
                      "text": self.statement})
        return chain

    def descendants(self):
        """孙: 沿层间规则向上解锁的问题。"""
        out = []
        k = self.layer
        while k in ASCEND:
            name, tpl = ASCEND[k]
            # 找到该层的层号
            lk = [i for i, v in LAYERS.items() if v[0] == name]
            lk = lk[0] if lk else None
            out.append({"to_layer": name, "question": tpl.format(obj=self.obj)})
            if lk is None:
                break
            k = lk
        return out

    def laterals(self):
        return lateral_links(self.obj, self.domain)

    def to_dict(self):
        return {"statement": self.statement, "domain": self.domain, "obj": self.obj,
                "layer": LAYERS[self.layer][0],
                "ancestors": self.ancestors(),
                "descendants": self.descendants(),
                "laterals": self.laterals()}


def render(lin, indent=""):
    """把谱系画成树。"""
    d = lin.to_dict()
    out = [f"{indent}╔═ 谱系: {d['statement'][:60]}",
           f"{indent}║  领域={d['domain']}  对象={d['obj']}  层={d['layer']}",
           f"{indent}║",
           f"{indent}║  【祖】它是怎么长出来的:"]
    for a in d["ancestors"]:
        mark = " ←本问题" if "本问题" in a["kind"] else ""
        out.append(f"{indent}║    {a['kind']:<18}{a['text'][:62]}{mark}")
    out.append(f"{indent}║")
    out.append(f"{indent}║  【孙】解决后会通向:")
    if not d["descendants"]:
        out.append(f"{indent}║    (已到最深可问层)")
    for s in d["descendants"]:
        out.append(f"{indent}║    → {s['to_layer']:<10}{s['question'][:60]}")
    out.append(f"{indent}║")
    out.append(f"{indent}║  【旁】同样的结构还出现在:")
    L = d["laterals"]
    for p in L["same_obj_other_method"]:
        out.append(f"{indent}║    [同对象换方法] {p[0]} · {p[1]} × {p[2]}")
    for p in L["same_method_other_obj"]:
        out.append(f"{indent}║    [同方法换对象] {p[0]} · {p[1]} × {p[2]}")
    out.append(f"{indent}║")
    out.append(f"{indent}║  【空格】尚未配对的 (对象,方法) —— 下一个领域候选:")
    for p in L["unpaired_slots"]:
        out.append(f"{indent}║    ○ {p[0]} · {p[1]} × {p[2]}")
    return "\n".join(out)


class Ladder_probe(Lineage):
    """简化构造: 直接用字段, 不走 Ladder 类。"""
    def __init__(self, statement, domain, obj, layer, motifs):
        super().__init__(statement, domain, obj, layer, motifs)


# ---------- 谱系完备性门（R38: 树枝即新颖性检验） ----------
def lineage_gate(statement, domain, obj, layer, motifs):
    """**候选的前置条件**: 进 G1 之前必须先给出完整谱系。

    依据(R38 文献核查的意外结论): 单条问题无法自证新旧 —— 检索"一条陈述"几乎必然空手;
    检索"**一棵树枝**"才可能命中。F3/F5 的"新领域"之所以被查出是重造,
    正是因为把谱系拿去比对文献时发现了同构树枝。
    ⇒ 谱系不是展示件, 是**新颖性门的必要构件**。

    返回 (是否通过, 缺失项)。
    """
    miss = []
    lin = Ladder_probe(statement, domain, obj, layer, motifs)
    d = lin.to_dict()
    if not d["ancestors"] or len([a for a in d["ancestors"] if "母题" in a["kind"]]) == 0:
        miss.append("母题(问题从哪长出)")
    pre = [a for a in d["ancestors"] if "前问题" in a["kind"]]
    if not pre:
        miss.append("前问题链(它踏过哪些已解决的下层)")
    if not d["descendants"]:
        miss.append("后代(解决后解锁什么)")
    L = d["laterals"]
    if not (L["same_obj_other_method"] or L["same_method_other_obj"]):
        miss.append("侧枝(同结构在别的领域)")
    return (len(miss) == 0), miss, d


def main():
    # 从 5 个领域各取一个真实问题, 建其谱系
    demos = [
        Ladder_probe("诗律熵为何恰为 n/2+1", "计算诗律学", "近体诗格律", 3,
                     ["形式文法", "熵率"]),
        Ladder_probe("集合类基数分布的精确公式", "计算音乐学", "12音级集合", 1,
                     ["群论等价类", "计数"]),
        Ladder_probe("亲属称谓折叠槽的充要刻画", "计算亲属结构", "亲属称谓", 1,
                     ["关系代数", "折叠"]),
        Ladder_probe("哪些合律篇式在诗集里从不出现", "计算诗律学", "近体诗格律", 5,
                     ["形式文法", "反事实"]),
    ]
    out = []
    for lin in demos:
        print(render(lin))
        print()
        out.append(lin.to_dict())

    print("=" * 92)
    print("为什么『树枝』比『孤立问题』重要")
    print("=" * 92)
    print("① **孤立问题的价值不可判**: 单看『格律熵为何是 n/2+1』, 无法判断它值不值得问。")
    print("   但放在谱系里就清楚了: 它的祖(L0计数/L2渐近)机器已解决, 它的孙指向机制(L3),")
    print("   它的旁延伸到音乐/纹样 —— **位置本身就是价值信息**。")
    print("② **前问题定义问题的来路**: 没有 L0/L2 被解决, L3 的『为什么』根本问不出来。")
    print("   ⇒ 前问题 = 问题的**存在条件**, 不是背景装饰。")
    print("③ **空格提示下一个领域**: 未配对的 (对象,方法) 就是可锻造的下一批领域。")

    print("\n" + "=" * 92)
    print("未配对的 (对象, 方法) 空格 —— 下一批领域候选")
    print("=" * 92)
    for p in PAIRS:
        if not p[3]:
            print(f"  ○ {p[0]:<14}{p[1]:<14}× {p[2]}")

    print()
    print("=" * 92)
    print("谱系完备性门 —— 候选进 G1 的前置条件")
    print("=" * 92)
    checks = [
        ("诗律熵为何恰为 n/2+1", "计算诗律学", "近体诗格律", 3, ["形式文法", "熵率"]),
        ("某条无来龙去脉的孤立陈述", "某域", "某对象", 1, []),
    ]
    gate_out = []
    for st, dm, ob, ly, mo in checks:
        ok, miss, d = lineage_gate(st, dm, ob, ly, mo)
        print(f"  {'✅通过' if ok else '❌不通过'}  {st[:40]}")
        if miss:
            print(f"        缺失: {miss}")
        gate_out.append({"statement": st, "pass": ok, "missing": miss})

    (HERE / "out/demo/problem_lineage.json").write_text(
        json.dumps({"lineages": out,
                    "lineage_gate": gate_out,
                    "unpaired_slots": [list(p) for p in PAIRS if not p[3]]},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n已存 out/demo/problem_lineage.json")


if __name__ == "__main__":
    main()
