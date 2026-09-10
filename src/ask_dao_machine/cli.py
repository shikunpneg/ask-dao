# -*- coding: utf-8 -*-
"""cli.py — 命令行入口: python -m ask_dao_machine <domains...> [--out DIR] [--limits JSON]

示例:
  python -m ask_dao_machine math a
  python -m ask_dao_machine all --out out/demo
  python -m ask_dao_machine math --limits '{"N":100000,"M":200000}'
"""
import argparse
import json
import sys
from pathlib import Path

from .pipeline import ProblemMaker
from .registry import Registry
from . import viz as viz_mod

_TPL = Path(__file__).resolve().parent.parent.parent / "assets" / "index.html"


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ask-dao-machine", description="问题制造器 CLI")
    ap.add_argument("domains", nargs="+", help="math / aesthetics / all")
    ap.add_argument("--out", default=str(Path.cwd() / "out"), help="输出目录(默认 ./out)")
    ap.add_argument("--limits", default="{}", help="JSON 限制参数(数学扫描上界)")
    ap.add_argument("--no-viz", action="store_true", help="只出 JSON, 不出可视化")
    ap.add_argument("--no-novelty", action="store_true", help="跳过新颖性门(不实查 OEIS)")
    args = ap.parse_args(argv)

    try:
        limits = json.loads(args.limits)
    except json.JSONDecodeError:
        print("--limits 需为 JSON", file=sys.stderr)
        return 2

    maker = ProblemMaker()
    reg = maker.registry
    domains = list(maker.list_domains()) if "all" in args.domains else args.domains

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    sets = {}
    for d in domains:
        try:
            ps = maker.run(d, limits)
        except KeyError as e:
            print(str(e), file=sys.stderr)
            return 2
        sets[d] = ps
        f = maker.save(ps, out / f"problems_{d}.json")
        print(f"[{d}] {ps.stats()} 耗时{getattr(ps,'elapsed',0)}s -> {f}")

    if not args.no_viz:
        if not _TPL.exists():
            print(f"缺可视化模板 {_TPL}", file=sys.stderr)
            return 1
        vd = viz_mod.make_viz(out, sets, reg, _TPL)
        print(f"[viz] -> {vd / 'index.html'}  (双击打开; 数据在 data.js)")

    # ---- 新颖性门(真实执行): 引擎不再自称新颖, 由本阶段实查 OEIS 后裁决 ----
    if not args.no_novelty:
        try:
            _run_novelty(out, sets)
        except FileNotFoundError:
            print("[novelty] 缺 data/stripped.gz -> 跳过新颖性门(参照系不可用)")
        except Exception as e:
            print(f"[novelty] 失败: {e}", file=sys.stderr)

    print(f"[registry] 母题库登记总数: {reg.total}")
    return 0


def _run_novelty(out: Path, sets: dict) -> None:
    """对带整数序列的记录过 novelty_gate, 结果写回 JSON 并打印分级分布。

    诚实: 参照系只有 OEIS 整数序列。**未被门覆盖的记录不是"新", 而是"不可判"**。
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "tools"))
    from novelty_gate import NoveltyGate
    from oeis_index import OEISIndex

    gate = NoveltyGate(OEISIndex.load())
    from collections import Counter
    total = Counter()
    for d, ps in sets.items():
        graded, unjudged = {}, 0
        for p in ps.problems:
            rec = p.to_dict()
            seq = (p.judgement or {}).get("seq")
            if not seq or len(seq) < 6:
                unjudged += 1
                continue
            r = gate.grade({"id": p.id, "seq": seq, "statement": p.statement,
                            "evidence_kind": (p.judgement or {}).get("method")})
            graded[p.id] = r
            total[r["grade"]] += 1
        if graded:
            f = out / f"problems_{d}.json"
            data = json.loads(f.read_text(encoding="utf-8"))
            for q in data["problems"]:
                if q["id"] in graded:
                    q["novelty_gate"] = graded[q["id"]]
            f.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        total["不可判(无序列)"] += unjudged
        print(f"[novelty:{d}] 过门 {len(graded)} / 不可判 {unjudged}")
    print(f"[novelty] 全库分级: {dict(total)}")
    (out / "novelty_report.json").write_text(
        json.dumps({"distribution": dict(total)}, ensure_ascii=False, indent=1),
        encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
