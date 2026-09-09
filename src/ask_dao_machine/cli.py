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
    print(f"[registry] 母题库登记总数: {reg.total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
