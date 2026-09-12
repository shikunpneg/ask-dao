# -*- coding: utf-8 -*-
"""tools/research/llm_judge_pass.py — LLM 裁判协议(补做 R25–R33 一直没真正做的事)

## 为什么需要它(诚实交代)
项目口径(02_CONTEXT §2)是"**LLM 是操作层裁判**"。但实际做法是:
`tools/research/llm_judgment.py` —— **我手写的台账**(看了几次网页搜索, 把结论敲进 Python 字典),
只覆盖 39 个候选中的约 6 个; G1 候选的"文献沉默"只靠**一次返回空的搜索**撑着。
**这既不是系统化的裁判, 也不是可复现的协议。** R33 补做时立刻查出两处机器侧错误。

## 协议(每个候选必答 5 项)
  J1 known       : 已知/未见/不确定 —— 附文献线索(检索所得)
  J2 mechanism   : **必填** —— 例外集的结构能否用**机器已有的原语**解释? 是什么?
                   ⚠️ 关键设计: 这一问的答案**必须回灌给机器验证**, 不能只在人脑里空想。
                   (R33 教训: 正是这一问揭穿了 `Harshad+平方数` 避开 QR(mod 18)。)
  J3 significance: 置换零模型 p 值与超出倍数(由 significance_vs_random.py 提供)
  J4 verdict     : N0已知 / N0o已知·未解 / N1可推 / N2检索未见 / **撤回**
  J5 human_needed: 是否必须人判断

## 实现限制(必须写明)
本模块**不含模型调用** —— 它定义协议与记录结构。填写者可以是:
  (a) 人在环(或 LLM-in-context)按协议逐条填;  (b) 接 API 自动填。
无论哪种, **J2 的结论都必须回到机器验证**(否则就是又一次 R32)。

## 纪律
- N2(检索未见)**不等于**新; 机器从未自称"新问题"。
- J2 若能被机器原语解释 ⇒ verdict 应降级为"可描述", 不得进 G1。
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
_td = HERE / "tools"
sys.path.insert(0, str(_td))
for _sd in _td.iterdir():
    if _sd.is_dir() and not _sd.name.startswith("_"):
        sys.path.insert(0, str(_sd))

# ---- 裁判记录(R33 按协议补填; 覆盖置换检验显著的 8 个) ----
JUDGMENTS = {
    "奇合数 + 素数": {
        "J1_known": "未确定 —— 检索未单独做",
        "J2_mechanism": "机器已验证: 例外 ⊆ Harshad数(4 个中 4 个)。若例外全是 Harshad 数, "
                        "则结构已被解释(非开放)。**须回灌机器确认**。",
        "J4_verdict": "N1 可推(结构可被机器原语解释)",
        "J5_human_needed": False,
    },
    "奇合数 + 平方数": {
        "J1_known": "未确定",
        "J2_mechanism": "机器已给出: 例外 ⊆ ≡2(mod 3)(11 个中 11 个)。**结构已被解释。**",
        "J4_verdict": "N1 可推",
        "J5_human_needed": False,
    },
    "Harshad数 + 平方数": {
        "J1_known": "未确定 —— 仅一次检索(giving 空结果), 不足以称'文献沉默'",
        "J2_mechanism": "**R32 漏掉的关键一问**。答案: 例外**避开 QR(mod 18)**(模 18 二次剩余, "
                        "覆盖扫描空间 44.5%) —— 用机器原语即可描述。R32 之所以判'无法描述', "
                        "是因为类库缺'避开型'原语与二次剩余类。**结构已部分解释。**",
        "J4_verdict": "**撤回**(原 N2/G1 均不成立)",
        "J5_human_needed": False,
    },
    "奇合数 + 完美幂": {
        "J1_known": "未确定",
        "J2_mechanism": "机器已给出: 例外 ⊆ 无数字0(15 个)。**结构已解释。**",
        "J4_verdict": "N1 可推",
        "J5_human_needed": False,
    },
    "奇合数 + 立方数": {
        "J1_known": "未确定",
        "J2_mechanism": "机器已给出: 例外 < 128(18 个全在小界内)。**结构已解释(小界)。**",
        "J4_verdict": "N1 可推",
        "J5_human_needed": False,
    },
    "奇合数 + 数位只含1和2": {
        "J1_known": "未确定",
        "J2_mechanism": "机器已给出: 例外 ⊆ Harshad数(7 个)。**结构已解释。**",
        "J4_verdict": "N1 可推",
        "J5_human_needed": False,
    },
    "Harshad数 + 三角数": {
        "J1_known": "未确定",
        "J2_mechanism": "机器已给出: 例外 ⊆ ≡2(mod 3) ∪ {754, 1474}(38 个)。**结构基本解释。**",
        "J4_verdict": "N1 可推",
        "J5_human_needed": False,
    },
    "半素数 + 奇合数": {
        "J1_known": "未确定",
        "J2_mechanism": "机器已给出: 例外 ⊆ 无数字0(13 个)。**结构已解释。**",
        "J4_verdict": "N1 可推",
        "J5_human_needed": False,
    },
}


def run(rank_path=None, sig_path=None):
    rank = json.loads((Path(rank_path) if rank_path else
                       HERE / "out/demo/final_candidates.json").read_text(encoding="utf-8"))
    sig = {f"{r['A']} + {r['B']}": r for r in
           json.loads((Path(sig_path) if sig_path else
                       HERE / "out/demo/significance.json").read_text(encoding="utf-8"))}
    out = []
    for c in rank["candidates"]:
        key = f"{c['A']} + {c['B']}"
        j = JUDGMENTS.get(key)
        s = sig.get(key, {})
        rec = {"candidate": key, "exceptions": c["n"], "density": c["density"],
               "machine_desc": {"class_fit": c.get("class_fit"),
                                "avoid_fit": c.get("avoid_fit"),
                                "small_bound": c.get("small_bound"),
                                "period": c.get("period")},
               "J3_significance": {"p": s.get("p_value"), "ratio": s.get("ratio_to_null"),
                                   "null_mean": s.get("null_mean")} if s else None}
        if j:
            rec.update(j)
        else:
            rec.update({"J1_known": "**未裁判**", "J2_mechanism": None,
                        "J4_verdict": "**未裁判**", "J5_human_needed": None})
        out.append(rec)
    return out


def main():
    rows = run()
    judged = [r for r in rows if r["J4_verdict"] != "**未裁判**"]
    print(f"LLM 裁判协议 —— 已裁判 {len(judged)} / {len(rows)} 候选\n")
    print(f"{'verdict':<22}{'p值':>7}{'倍数':>7}  候选")
    print("-" * 78)
    for r in rows:
        s = r["J3_significance"] or {}
        p = f"{s.get('p'):.3f}" if s.get("p") is not None else "—"
        ra = f"{s.get('ratio'):.2f}x" if s.get("ratio") is not None else "—"
        print(f"{r['J4_verdict']:<22}{p:>7}{ra:>7}  {r['candidate']}")

    print("\n== 协议强制项 J2(机制)的效果 ==")
    for r in judged:
        if "撤回" in r["J4_verdict"] or "无法描述" in str(r["J2_mechanism"]):
            print(f"  {r['candidate']}: {r['J2_mechanism'][:100]}")

    from collections import Counter
    c = Counter(r["J4_verdict"] for r in rows)
    print(f"\n裁决分布: {dict(c)}")
    print(f"需人判断的: {sum(1 for r in rows if r['J5_human_needed'])} / {len(rows)}")
    print("\n诚实: 本模块不含模型调用 —— 它定义协议与记录结构; J2 的结论必须回灌机器验证。")
    unjud = len(rows) - len(judged)
    if unjud:
        print(f"⚠️ 仍有 {unjud} 个候选**未裁判** —— 这是当前的真实缺口, 不得当作'已排除'。")
    (HERE / "out/demo/llm_judge_pass.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已存 out/demo/llm_judge_pass.json")


if __name__ == "__main__":
    main()
