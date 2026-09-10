# -*- coding: utf-8 -*-
"""tools/p_C_integrate.py — P-C 当务升级回路:
   1) 给已生成的问题集(全域)打 big_score 当务分, 写回 records
   2) 用张力缺口(gap_map)生成新候选问题, 套句式打当务分, 迭代到出现 ≥ 当务阈值
   3) 写回台账 + log
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from big_score import score_text

HERE = Path(__file__).resolve().parent.parent


def integrate_existing():
    n_sum = 0
    for fn in HERE.glob("out/demo/problems_*.json"):
        d = json.loads(fn.read_text(encoding="utf-8"))
        for p in d["problems"]:
            txt = " ".join([p.get("statement", ""), p.get("seed", ""),
                            " ".join(p.get("motifs", []))])
            sc = score_text(txt)
            p.setdefault("big_score", sc)
            n_sum += 1
        fn.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return n_sum


GAP_MAP = [
    ("言意 x 熵率", "言不尽意", "可生成语言", "意义状态可不可嵌入"),
    ("言意 x 熵率", "言尽意", "可生成语言", "意义状态必可嵌入"),
    ("理气 x 表示", "理在气先", "可计算", "可表"),
    ("理气 x 表示", "理在气中", "可计算", "可表"),
    ("有无 x 穷举", "以无为本", "枚举穷尽", "可列"),
    ("顿渐 x 算法", "顿悟", "算法可达", "可证"),
    ("天人 x 因果", "天人感应", "可识别", "可验"),
]


def gen_gap_candidates():
    out = []
    for topic, a, b, c in GAP_MAP:
        for stmt in [
            f"若 '{a}' 与 '{b}' 真的不可统一, 那么判定 '{c}' 的标准属于公设层还是可测量层? 哪种异常可裁决二者?",
            f"两套 '{a}' vs '{b}' 在 '{c}' 上是否构成悖论? 可否设计一个判决性实验消解?",
            f"何种统一形式能解释 '{a}' 与 '{b}' 各自能测量而不能测量的现象? 给出可检验新预言."
        ]:
            sc = score_text(stmt)
            if sc["total"] >= 3.0:
                out.append({"topic": topic, "statement": stmt, "H": sc["total"],
                             "route": "需专家/语义判官(无本机数值判官)"})
    out.sort(key=lambda x: -x["H"])
    return out


def main():
    n = integrate_existing()
    cands = gen_gap_candidates()
    Path("out/demo/gap_template_candidates.json").parent.mkdir(parents=True, exist_ok=True)
    Path("out/demo/gap_template_candidates.json").write_text(
        json.dumps(cands, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"已写回 big_score 的问题数: {n}")
    print(f"缺口模板生成候选(当务≥3): {len(cands)} (顶 H={cands[0]['H'] if cands else 0})")
    for c in cands[:8]:
        print(f"  H={c['H']} [{c['topic']}] {c['statement'][:80]}")


if __name__ == "__main__":
    main()
