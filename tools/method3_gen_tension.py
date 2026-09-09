# -*- coding: utf-8 -*-
"""tools/method3_gen_tension.py — METHODOLOGY3 ①阶段升级:
   用张力探测器 v1 的'对峙/批判'候选作为生成输入, 生成带大问题信号的哲学候选。
   过滤器: F1良构(长度/无占位) + F4当务(big_score H>=2 才留) -> 提交人类裁决列表。
   说明: 这类问题无本机数值判官 -> 判官=专家/语义分析(不冒充机器能判)。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from big_score import score_text

HERE = Path(__file__).resolve().parent.parent


def gen_from_tension(o):
    A = o["A"][0]
    B = o["B"][0]
    tpl = [
        f"两套框架 '{A}' 与 '{B}' 能否统一? 冲突究竟在哪一层(定义/前提/判定标准)?",
        f"若 '{A}' 成立, 是否与 '{B}' 相矛盾? 矛盾可否消解(悖论还是可调和)?",
        f"何种判据或测量能区分 '{A}' 与 '{B}' 两种立场?",
        f"'{A}' 与 '{B}' 各自能解释对方解释不了的东西吗(统一候选)?",
    ]
    return tpl


def main():
    tens = json.loads((HERE / "out/demo/tensions_v1.json").read_text(encoding="utf-8"))
    tens = [o for o in tens if o["sub"] == "对峙/批判"]
    n0 = 0
    f1 = []
    surv = []
    for o in tens:
        for s in gen_from_tension(o):
            n0 += 1
            if len(s) < 12:
                continue
            sc = score_text(s)
            hs = sc["total"]
            if hs >= 2.0:
                surv.append({"topic": o["topic"], "excerpt": o["excerpt"],
                             "statement": s, "H": hs, "per": sc["per"],
                             "route": "需专家/语义判官(无本机数值判官)"})
    print(f"张力输入 {len(tens)} 条对峙 -> 生成候选 {n0} -> F4(H>=2) 幸存 {len(surv)}")
    for s in surv[:12]:
        print(f"  H={s['H']} [{s['topic']}] {s['statement'][:64]}")
    Path("out/demo/method3_tension_shortlist.json").parent.mkdir(parents=True, exist_ok=True)
    Path("out/demo/method3_tension_shortlist.json").write_text(
        json.dumps(surv, ensure_ascii=False, indent=1), encoding="utf-8")
    md = HERE / "docs/human_review_sheet.md"
    with md.open("a", encoding="utf-8") as f:
        f.write("\n## 张力注入短名单(METHODOLOGY3, 待人类裁决)\n")
        for s in surv[:12]:
            f.write(f"- H={s['H']} [{s['topic']}] {s['statement']}\n")
    return surv


if __name__ == "__main__":
    main()
