# -*- coding: utf-8 -*-
"""tools/research/cross_md_v4.py — 多域交叉 v4: 真F1门槛 + 真三域(去名义化) + 质量分层

整改项(03_NEXT_STEPS A1/A2/A3):
  A1 三域去名义化: 第三域必须进入计算, 且结果随第三域参数变化(sensitivity), 否则判 nominal。
  A2 F1良构门槛: 从 len(statement)>=20 升级为结构化门槛 —— 必须显式给出
        obj(对象) / quant(参数量词域) / crit(判定判据), 缺一即空壳。
  A3 质量分层: 全部组合分为 (i)可判 (ii)需建验证器 (iii)空壳, 只保留 (i)(ii)。

纪律: 当务分只走 big_score_ev(证据门); 真三域须过 sensitivity; 名义三域如实计数, 不粉饰。
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from big_score_ev import score_ev
from tri_verifiers import TRI_REGISTRY, sensitivity

HERE = Path(__file__).resolve().parent.parent

# 与 v3 相同的域矩阵(用于分层审计, 不是用于产出真候选)
D = {
    "信息": {"方向": ["熵率上界", "信道容量", "算法复杂度", "语义接地"], "载体": ["有限文法语言", "编码族", "序列族"]},
    "数学": {"方向": ["分布均匀性", "表示覆盖", "极值纪录", "收敛与周期"], "载体": ["质数模类", "递推映射", "禁构族"]},
    "生物": {"方向": ["选择迭代", "群体固定"], "载体": ["等位基因频率", "性状分布"]},
    "心理": {"方向": ["信念修正", "机制分解"], "载体": ["证据流", "任务表现"]},
    "物理": {"方向": ["对称守恒", "尺度标度"], "载体": ["守恒量谱", "临界指数"]},
    "语言": {"方向": ["形式文法", "歧义"], "载体": ["CFG/正则族", "句法树"]},
    "工程": {"方向": ["功能结构映射", "可靠性"], "载体": ["设计空间", "失效模式"]},
}

# ---- F1 良构门槛 ----
PLACEHOLDER = re.compile(
    r"上述|该命题|前述|相关性质如何|能否裁决|的判定标准能否|如何接地\?$")


def f1_check(rec):
    """结构化良构检查。返回 (ok, missing[]).
    要求: obj 非空且非占位符; quant 显式含参数域(数字区间或具名参数集); crit 给出判定判据。"""
    missing = []
    obj = (rec.get("obj") or "").strip()
    quant = (rec.get("quant") or "").strip()
    crit = (rec.get("crit") or "").strip()
    if not obj or PLACEHOLDER.search(obj):
        missing.append("obj")
    # 参数域: 需出现区间/集合/枚举(数字 或 ∈ 或 范围词)
    if not quant or not re.search(r"\d|∈|≤|>=|区间|集合|网格", quant):
        missing.append("quant")
    if not crit or len(crit) < 6:
        missing.append("crit")
    return (len(missing) == 0), missing


# ---- 策展候选(可判: 有真 handler) ----
def curated_2domain():
    from cross_md_v3 import HANDLERS
    specs = [
        (("信息", "语言"), "禁bb/无歧义CFG 的熵率上界与达上界的对象族",
         "字母表 Σ 大小 |Σ|∈{2,3,4}", "熵率 h 是否达 log|Σ|",
         "有限文法语言的熵率上界是多少? 无歧义 CFG 能否达到 log|Σ|?"),
        (("数学", "信息"), "质数间隙 ≡0(mod4) 的二元序列一阶熵",
         "质数上限 N ∈ {1e5, 2e5, 1e6}", "频率与熵是否偏离 1/2 均匀值",
         "质数间隙模4的二元序列一阶熵与均匀分布的偏差?"),
        (("生物", "数学"), "选择迭代不动点在选择系数网格上的位置",
         "选择系数 s ∈ {0.1,0.3,0.6,1.0}", "不动点是否为 1(固定)或存在多态",
         "等位基因频率在选择迭代下是否固定? 固定速度随 s 如何变?"),
        (("工程", "信息"), "k-out-of-n 冗余的可靠度-成本前沿",
         "冗余 n ∈ {3,5,7}, 阈值 k ∈ [1,n]", "单机可靠度 0.9 下前沿是否单调",
         "冗余设计的可靠度-成本前沿形状?"),
    ]
    out = []
    for (a, b), obj, quant, crit, stmt in specs:
        r = {"domains": [a, b], "arity": 2, "obj": obj, "quant": quant,
             "crit": crit, "statement": stmt,
             "handler": (a, b) if (a, b) in HANDLERS else (b, a)}
        out.append(r)
    return out


def curated_3domain():
    out = []
    for key, e in TRI_REGISTRY.items():
        ok, table = sensitivity(e)
        r = {"domains": list(key), "arity": 3, "third": e["third"],
             "third_param": e["param"],
             "obj": e["obj"], "quant": e["quant"], "crit": e["crit"],
             "statement": e["statement"],
             "sensitive": ok, "third_grid": e["grid"],
             "third_table": [{"theta": t["theta"],
                              "outputs": [round(x, 4) for x in t["outputs"]]} for t in table]}
        out.append(r)
    return out


# ---- 需建验证器(良构但无 handler) ----
def needs_verifier():
    specs = [
        (["物理", "数学"], "守恒量谱的极值分布",
         "对称群 G ∈ {Z2, S3, SO(3)}", "极值是否服从尺度律/普适类",
         "守恒量谱的极值分布是否服从尺度律? 对称破缺如何移动极值?"),
        (["生物", "心理"], "选择压下的信念-行为耦合固定点",
         "选择系数 s ∈ (0,1], 学习率 η ∈ (0,1]", "是否存在双稳态与滞后",
         "选择压与信念修正耦合时是否存在双稳态?"),
        (["语言", "生物"], "文法复杂度在文化传递中的稳定阈值",
         "传递保真度 μ ∈ [0,1]", "是否存在复杂度崩塌阈值",
         "文法复杂度在含噪文化传递下是否存在崩塌阈值?"),
    ]
    return [{"domains": d, "arity": 2, "obj": o, "quant": q, "crit": c,
             "statement": s, "route": "需建验证器"} for d, o, q, c, s in specs]


# ---- 名义三域审计(对 v3 旧产物) ----
def audit_nominal(rows):
    """三域行中, 第三域是否进入任何 handler 签名。返回 (真, 名义)。"""
    real, nominal = [], []
    for r in rows:
        if len(r.get("domains", [])) < 3:
            continue
        handler = tuple(r.get("handler", ()))
        third = r["domains"][2]
        (real if third in handler else nominal).append(r)
    return real, nominal


def main():
    # A2: 原始笛卡尔矩阵(与 v3 完全同构: 2域 + 名义3域) -> F1 审计
    matrix = []
    doms = list(D.keys())
    for a in doms:
        for b in doms:
            if a == b:
                continue
            for dirn in D[a]["方向"]:
                for car in D[b]["载体"]:
                    matrix.append({"domains": [a, b], "dir": dirn, "carrier": car,
                                   "statement": f"{a}·{dirn} × {b}·{car}: {car}的相关性质如何?",
                                   "obj": "", "quant": "", "crit": ""})
            for c in doms:  # v3 的名义三域: 第三域挂在句尾, 不参与计算
                if c in (a, b):
                    continue
                matrix.append({"domains": [a, b, c], "dir": D[a]["方向"][0],
                               "carrier": D[b]["载体"][0],
                               "statement": f"{a}·{D[a]['方向'][0]} × {b}·{D[b]['载体'][0]} × {c}判据: "
                                            f"第三域{c}的判定标准能否裁决上述{a}-{b}交叉命题?",
                               "obj": "", "quant": "", "crit": ""})
    f1_pass = [r for r in matrix if f1_check(r)[0]]

    # A1/A3: 策展候选
    two = curated_2domain()
    tri = curated_3domain()
    nv = needs_verifier()

    # 旧产物名义审计
    old_path = HERE / "out/demo/cross_md_v3.json"
    nominal_report = None
    if old_path.exists():
        old = json.loads(old_path.read_text(encoding="utf-8"))["rows"]
        real, nominal = audit_nominal(old)
        nominal_report = {"three_domain_total": len(real) + len(nominal),
                          "real_three_domain": len(real), "nominal_three_domain": len(nominal)}

    # 打分(证据门) + 判定
    from cross_md_v3 import HANDLERS
    for r in two:
        try:
            r["verify"] = HANDLERS[r["handler"]]()
        except Exception as e:
            r["verify"] = {"kind": "err", "result": str(e), "verdict": "err"}
    for r in tri:
        ok, _ = f1_check(r)
        r["f1_ok"] = ok
        r["verdict_class"] = "真三域" if r["sensitive"] else "名义三域(剔除)"
    for r in two + tri:
        ev = {"method_gap": True, "experiment_design": "仿真/数值",
              "route": "仿真" if r.get("verify", {}).get("kind") == "仿真" else "数值"}
        r["H_ev"] = score_ev({"evidence": ev})["total"]

    # 分层(A3)
    layering = {
        "i_可判": len([r for r in two + tri if f1_check(r)[0]]),
        "ii_需建验证器": len([r for r in nv if f1_check(r)[0]]),
        "iii_空壳": len(matrix) - len(f1_pass),
    }
    payload = {
        "stages": {"笛卡尔矩阵": len(matrix), "F1过门": len(f1_pass),
                   "真三域候选": len([r for r in tri if r["sensitive"]]),
                   "名义三域(剔除)": len([r for r in tri if not r["sensitive"]])},
        "layering": layering,
        "nominal_audit_v3": nominal_report,
        "two_domain": two, "three_domain": tri, "needs_verifier": nv,
        "f1_reject_sample": f1_pass[:0],  # 矩阵全数被 F1 拒
    }
    out = HERE / "out/demo/cross_md_v4.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    print("== 分层(i/ii/iii) ==")
    print(f"  笛卡尔矩阵 {len(matrix)} 全部过 F1 的仅 {len(f1_pass)} -> "
          f"空壳 {layering['iii_空壳']}")
    print(f"  (i)可判 {layering['i_可判']}  (ii)需建验证器 {layering['ii_需建验证器']}")
    print("== 真三域(过敏感性) ==")
    for r in tri:
        print(f"  [{'真' if r['sensitive'] else '名义'}] {r['domains']} 第三域={r['third']}"
              f"({r['third_param']}) H={r['H_ev']} | {r['obj']}")
    print("== 旧 v3 名义审计 ==")
    print(f"  {nominal_report}")
    print("saved:", out)


if __name__ == "__main__":
    main()
