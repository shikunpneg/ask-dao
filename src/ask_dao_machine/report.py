# -*- coding: utf-8 -*-
"""report.py — 把一次跑批的结果汇总成**一页人话**（解决"跑完不知道下一步看什么"）。

输入: 一次跑批的输出目录（含 problems_*.json、novelty_report.json、viz/）
输出: <out>/REPORT.md + 终端摘要

设计原则（与本项目纪律一致）:
  - 状态只来自记录，不在这里改写；
  - 明确区分"已判定"(真/假)、"待解"(悬置·开放)、"不可判"；
  - 新颖性一栏只说门的结果，不说"新"。
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

STATUS_KEYS = ("真", "假", "悬置", "有限", "待实验")
NOVELTY_ORDER = ("N0", "N1", "N2", "N3", "不可判(无序列)")


def _bucket(status: str) -> str:
    s = str(status or "")
    if s.startswith("真"):
        return "真"
    if s.startswith("假"):
        return "假"
    if "悬置" in s or "开放" in s:
        return "悬置·开放"
    if "验证" in s or "有限" in s:
        return "有限/数值验证"
    if "待" in s:
        return "待实验/待评审"
    return s[:12] or "未标"


def collect(out_dir: Path) -> dict:
    """扫描跑批目录，汇总成结构化结果。"""
    out_dir = Path(out_dir)
    domains, novel = [], {}
    files = sorted(out_dir.glob("problems_*.json"))
    for f in files:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:                                   # noqa: BLE001
            continue
        probs = d.get("problems") or []
        st = Counter(_bucket(p.get("status")) for p in probs)
        roots = d.get("roots") or []
        routes = Counter(str(p.get("judge_route") or (p.get("judgement") or {}).get("method") or "—")
                         for p in probs)
        # 优先挑"机器结算不了/待解"的若干条作为"先看这个"
        openish = [p for p in probs if _bucket(p.get("status")) in ("悬置·开放", "待实验/待评审")]
        domains.append({
            "domain": d.get("domain") or f.stem.replace("problems_", ""),
            "file": f.name,
            "n": len(probs),
            "status": dict(st),
            "roots": len(roots),
            "routes": dict(routes.most_common(6)),
            "open_samples": [{
                "id": p.get("id"), "statement": p.get("statement"),
                "status": p.get("status"),
                "route": p.get("judge_route") or (p.get("judgement") or {}).get("method"),
            } for p in openish[:2]],
            "graded": sum(1 for p in probs if p.get("novelty_gate")),
        })
    nr = out_dir / "novelty_report.json"
    if nr.exists():
        try:
            novel = json.loads(nr.read_text(encoding="utf-8")).get("distribution") or {}
        except Exception:                                   # noqa: BLE001
            novel = {}
    viz = out_dir / "viz" / "index.html"
    return {
        "out_dir": str(out_dir),
        "domains": domains,
        "total": sum(d["n"] for d in domains),
        "status_total": dict(sum((Counter(d["status"]) for d in domains), Counter())),
        "novelty": novel,
        "viz": str(viz) if viz.exists() else None,
        "artifacts": sorted(p.name for p in out_dir.rglob("*") if p.is_file()),
    }


def _pct(n: int, total: int) -> str:
    return f"{100.0 * n / total:.0f}%" if total else "—"


def render_markdown(rep: dict) -> str:
    total = rep["total"]
    st = rep["status_total"]
    nov = rep["novelty"]
    L = []
    L.append("# 跑批报告（自动生成）")
    L.append("")
    L.append(f"> 输出目录：`{rep['out_dir']}`　总问题数：**{total}**　"
             f"域数：**{len(rep['domains'])}**")
    L.append("")
    L.append("## 一句话结论")
    L.append("")
    if total:
        parts = " · ".join(f"{k} {v}（{_pct(v, total)}）" for k, v in
                           sorted(st.items(), key=lambda kv: -kv[1]))
        L.append(f"本批共产出 **{total}** 条**带判定路由**的问题：{parts}。")
    else:
        L.append("本批没有产出问题记录（检查是否用了 `--out` 指向了空目录）。")
    if nov:
        n3 = int(nov.get("N3", 0) or 0)
        L.append("")
        L.append(f"新颖性门（OEIS 参照系）分级：" +
                 " · ".join(f"{k} {nov.get(k, 0)}" for k in NOVELTY_ORDER if nov.get(k) is not None) + "。")
        L.append(f"**世界新问题 N3 = {n3}**；「不可判」不等于「已排除」——没有整数序列的记录进不了这道门。")
    else:
        L.append("")
        L.append("本批**没有跑新颖性门**（缺 `data/stripped.gz`，或用了 `--no-novelty`）。"
                 "需要它时先取参照系：`python -m ask_dao_machine data fetch`。")
    L.append("")
    L.append("## 各域一览")
    L.append("")
    L.append("| 域 | 题数 | 状态分布 | 母题根 | 主要判定路由 |")
    L.append("|---|---|---|---|---|")
    for d in sorted(rep["domains"], key=lambda x: -x["n"]):
        stx = " · ".join(f"{k} {v}" for k, v in sorted(d["status"].items(), key=lambda kv: -kv[1]))
        rt = " · ".join(list(d["routes"])[:3])
        L.append(f"| `{d['domain']}` | {d['n']} | {stx} | {d['roots']} | {rt} |")
    L.append("")
    # 先看什么
    picks = [(d["domain"], s) for d in rep["domains"] for s in d["open_samples"]]
    if picks:
        L.append("## 建议先看这几条（机器结算不了的 / 待解待评的）")
        L.append("")
        for dom, s in picks[:6]:
            L.append(f"- **[{dom} {s['id']}]** {s['statement']}")
            L.append(f"  - 状态：{s['status']}　判定路由：{s['route']}")
        L.append("")
    L.append("## 产物与用途")
    L.append("")
    L.append("| 产物 | 用途 |")
    L.append("|---|---|")
    for f in rep["artifacts"]:
        why = {
            "REPORT.md": "本报告（一页人话汇总）",
            "novelty_report.json": "新颖性门的分级分布（N0–N3 + 不可判）",
            "data.js": "可视化页的数据（问题树/概念树）",
            "index.html": "交互式可视化入口",
        }.get(f)
        if not why:
            why = ("该域的问题清单（带出处链：母题→模板→绑定→判定）"
                   if f.startswith("problems_") else "跑批中间产物")
        L.append(f"| `{f}` | {why} |")
    L.append("")
    L.append("## 下一步")
    L.append("")
    steps = []
    if rep["viz"]:
        steps.append(f"**看可视化**：双击 `{rep['viz']}`（问题树 + 概念树 + 概念论证）。")
    steps.append("**取一条问题去解**：把 `problems_*.json` 里 `status` 为「悬置·开放」或其判定路由为"
                 "「开放(机器无法结算)」的条目，交给 AI4S harness 或人工。")
    steps.append("**过参照系**：`python -m ask_dao_machine data fetch` 取 OEIS 索引后重跑"
                 "（不加 `--no-novelty`），`novelty_gate` 字段会写回每条记录。")
    steps.append("**自查环境**：`python -m ask_dao_machine doctor`。")
    for i, t in enumerate(steps, 1):
        L.append(f"{i}. {t}")
    L.append("")
    L.append("---")
    L.append("")
    L.append("*状态与分级均直接来自记录，本报告只做汇总，不改写任何判定结果。*")
    return "\n".join(L)


def main(out_dir="out", quiet=False) -> int:
    out = Path(out_dir)
    if not out.exists():
        print(f"目录不存在：{out}（先跑一次：python -m ask_dao_machine all --out {out}）")
        return 2
    rep = collect(out)
    md = render_markdown(rep)
    dst = out / "REPORT.md"
    dst.write_text(md, encoding="utf-8")
    if not quiet:
        # 终端摘要（短版）
        st = rep["status_total"]
        print("=" * 76)
        print(f"跑批报告 · {out} · 共 {rep['total']} 条问题 / {len(rep['domains'])} 个域")
        print("=" * 76)
        for d in sorted(rep["domains"], key=lambda x: -x["n"]):
            stx = " ".join(f"{k} {v}" for k, v in sorted(d["status"].items(), key=lambda kv: -kv[1]))
            print(f"  {d['domain']:<12} {d['n']:>3} 条   {stx}")
        if st:
            print("  " + "-" * 66)
            print("  合计状态：" + " · ".join(f"{k} {v}" for k, v in sorted(st.items(), key=lambda kv: -kv[1])))
        if rep["novelty"]:
            print("  新颖性门：" + " · ".join(f"{k} {rep['novelty'].get(k, 0)}" for k in NOVELTY_ORDER
                                             if rep["novelty"].get(k) is not None))
        else:
            print("  新颖性门：未跑（缺 data/stripped.gz）—— python -m ask_dao_machine data fetch")
        picks = [(d["domain"], s) for d in rep["domains"] for s in d["open_samples"]][:3]
        if picks:
            print("\n  先看这几条：")
            for dom, s in picks:
                print(f"    [{dom} {s['id']}] {str(s['statement'])[:64]}")
        print(f"\n  完整报告：{dst}")
        if rep["viz"]:
            print(f"  可视化：  {rep['viz']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
