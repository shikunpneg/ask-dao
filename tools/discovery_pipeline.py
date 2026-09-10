# -*- coding: utf-8 -*-
"""tools/discovery_pipeline.py — 问题发现器主入口（R52）

定位(用户): 先做问题制造/发现器, 再接最主流的 AI4S harness。
=> 本模块是**发现器的对外接口**: 把已有模块串成流水线, 产出
   **AI4S harness 可直接消费的问题清单**。

AI4S harness 需要的问题格式: 明确的输入/判定路由/可验证性。
所以我们输出的每条问题 = {问题, 判定路由, 证据, 状态}。

流水线:
  P1 多进制规律候选(K2-14)  -> 写成可验证命题(K1)
  P2 反例驱动(counterex)    -> 例外刻画问题
  P3 跨域组合(crazy_scale)  -> 分级候选
  P4 问题分层+谱系           -> 每条的层与谱系
输出: out/demo/discovery_manifest.json (AI4S 可消费)
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))

from palbase_scan import scan as palbase_scan  # noqa: E402


def p1_cross_base(N=5_000_000):
    """P1: 把跨进制规律写成可验证命题(K1 层提出)。"""
    rows = json.loads((HERE / "out/demo/palbase_scan.json").read_text(encoding="utf-8"))
    out = []
    for r in rows:
        if r["exc"] == 0:
            status = "已验证(N=5e6 零例外)"
            verdict = "猜想: 回文(b)+素数 覆盖所有 n (b≥7)"
        elif not r["at_boundary"]:
            status = "疑似有限(最后例外后全覆盖)"
            verdict = f"猜想: 例外集有限且 = {r['exc_list']}"
        else:
            status = "贴边界(未知)"
            verdict = "开放: 例外是否有限?"
        out.append({
            "id": f"Q_b{r['b']}",
            "domain": "数论(进制依赖)",
            "statement": f"每个 n 是否都可写成 回文数(base {r['b']}) + 素数?",
            "conjecture": verdict,
            "evidence": {"scan_to": N, "exceptions": r["exc_list"],
                         "count": r["exc"], "last": r["last"]},
            "judge_route": "数值枚举到 N(向量化标记); 若需证明走解析数论",
            "status": status,
            "layer": "L0/L2",
        })
    return out


def p2_counterex():
    """P2: 反例驱动问题(counterex 引擎已产出)。"""
    p = HERE / "out/demo/problems_counterex.json"
    if not p.exists():
        return []
    d = json.loads(p.read_text(encoding="utf-8"))
    return [{
        "id": q["id"], "domain": "加性数论",
        "statement": q["statement"],
        "conjecture": "例外集的刻画/有限性/密度极限",
        "evidence": q["judgement"],
        "judge_route": "反例集结构拟合 + 延伸探针",
        "status": "开放(机器无法结算)",
        "layer": "L1/L2",
    } for q in d["problems"]]


def p3_cross_scale():
    """P3: 跨域组合分级(最好的一档)。"""
    p = HERE / "out/demo/crazy_scale.json"
    if not p.exists():
        return []
    d = json.loads(p.read_text(encoding="utf-8"))
    out = []
    # 跨域里"例外少且不贴边界"的
    for r in d.get("cross", []):
        if 0 < r["exception_count"] < 10 and not r["at_boundary"]:
            out.append({
                "id": f"P3_{len(out)}", "domain": "跨域组合",
                "statement": f"{r['pair']} 的例外集({r['exception_count']}个)有限吗? 刻画?",
                "conjecture": "例外有限且小",
                "evidence": {"count": r["exception_count"], "density": r["density"]},
                "judge_route": "向量化标记到 1e5",
                "status": "疑似有限",
                "layer": "L1",
            })
    return out


def main():
    print("=" * 100)
    print("问题发现器主入口 —— 产出 AI4S harness 可消费的问题清单")
    print("=" * 100)
    all_q = []
    for fn, name in ((p1_cross_base, "P1 跨进制规律"), (p2_counterex, "P2 反例驱动"),
                     (p3_cross_scale, "P3 跨域组合")):
        qs = fn()
        print(f"\n  {name}: {len(qs)} 条")
        all_q += qs
        for q in qs[:3]:
            print(f"    [{q['status']}] {q['statement'][:60]}")
    print(f"\n  总计: {len(all_q)} 条可交付问题")

    manifest = {"generator": "ask-dao-machine/discovery_pipeline",
                "target": "AI4S harness",
                "problem_format": "{statement, conjecture, evidence, judge_route, status, layer}",
                "count": len(all_q), "problems": all_q}
    out = HERE / "out/demo/discovery_manifest.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n已存 {out} —— 可直接喂给 AI4S harness(每条带判定路由)")


if __name__ == "__main__":
    main()
