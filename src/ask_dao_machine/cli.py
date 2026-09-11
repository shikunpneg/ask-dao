# -*- coding: utf-8 -*-
"""cli.py — 命令行入口（产品化版本）

用法:
  ask-dao-machine <domains...> [--out DIR] [--limits JSON] [--no-viz] [--no-novelty]
  ask-dao-machine paper <文件/目录...>     输入论文，输出问题（含来源标注）+ REPORT.md
  ask-dao-machine report [--out DIR]       把一次跑批汇总成一页人话（写 <out>/REPORT.md）
  ask-dao-machine doctor                   环境自查（缺什么、下一步做什么）
  ask-dao-machine data fetch [--force]     取 OEIS 参照系（data/stripped.gz，约 32MB）

典型一次完整流程:
  python -m ask_dao_machine doctor
  python -m ask_dao_machine all --out out/demo
  python -m ask_dao_machine report --out out/demo
"""
import argparse
import json
import sys
from pathlib import Path

DOMAINS_HINT = ("aesthetics / combo / counterex / digit_base / direction / fusion / "
                "ling / math / records / sparse / all")


def _dispatch(argv):
    """子命令分发：report / doctor / data。返回 exit code，或 None（走引擎跑批）。"""
    if not argv:
        return None
    head = argv[0]
    if head == "report":
        ap = argparse.ArgumentParser(prog="ask-dao-machine report",
                                     description="把一次跑批汇总成一页人话（写 <out>/REPORT.md）")
        ap.add_argument("--out", default=str(Path.cwd() / "out"), help="跑批输出目录（默认 ./out）")
        a = ap.parse_args(argv[1:])
        from . import report as report_mod
        return report_mod.main(a.out)
    if head == "paper":
        ap = argparse.ArgumentParser(
            prog="ask-dao-machine paper",
            description="输入论文（.md/.txt/.pdf/.docx/.epub 或目录），输出问题清单 + 一页人话报告",
            epilog=("例子:\n  ask-dao-machine paper papers/\n"
                    "  ask-dao-machine paper paper.pdf --out out/papers\n"
                    "  产出：problems_paper.json（含「作者已提出」与「机器新提出」两类标注）与 REPORT.md\n"),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        ap.add_argument("paths", nargs="+", help="论文文件或目录")
        ap.add_argument("--out", default=str(Path.cwd() / "out" / "papers"), help="输出目录")
        ap.add_argument("--per-type", type=int, default=8, help="每类机制最多产出多少条（默认 8）")
        a = ap.parse_args(argv[1:])
        from . import paper as paper_mod
        rc = paper_mod.main(a.paths, out_dir=a.out)
        return rc
    if head == "doctor":
        ap = argparse.ArgumentParser(prog="ask-dao-machine doctor",
                                     description="环境自查：Python / 包 / 引擎 / 参照系 / 输出目录 / 测试")
        ap.parse_args(argv[1:])
        from . import doctor as doctor_mod
        return doctor_mod.check()
    if head == "data":
        ap = argparse.ArgumentParser(prog="ask-dao-machine data", description="参照系数据（OEIS）")
        sub = ap.add_subparsers(dest="action", required=True)
        f = sub.add_parser("fetch", help="下载 OEIS stripped.gz 到 data/（约 32MB）")
        f.add_argument("--dest", default=None, help="目标目录（默认 <repo>/data）")
        f.add_argument("--force", action="store_true", help="已存在也重新下载")
        a = ap.parse_args(argv[1:])
        from . import doctor as doctor_mod
        return doctor_mod.fetch(a.dest, a.force)
    return None


def main(argv=None):
    from . import _console
    _console.setup()                     # Windows 控制台非 UTF-8 时也能打印中文
    argv = list(sys.argv[1:] if argv is None else argv)

    rc = _dispatch(argv)
    if rc is not None:
        return rc

    ap = argparse.ArgumentParser(
        prog="ask-dao-machine",
        description="问题制造器 CLI —— 两条路（问题路产问题 / 想象路产概念）+ 母题库 + 判定器 + 出处链",
        epilog=("子命令:\n"
                "  paper <文件/目录...>    输入论文 → 输出问题清单 + REPORT.md\n"
                "  report [--out DIR]      把一次跑批汇总成一页人话（写 <out>/REPORT.md）\n"
                "  doctor                  环境自查（缺什么、下一步做什么）\n"
                "  data fetch [--force]    取 OEIS 参照系（data/stripped.gz，约 32MB）\n"
                "\n例子:\n"
                "  ask-dao-machine all --out out/demo\n"
                "  ask-dao-machine math --limits '{\"N\":100000,\"M\":200000}'\n"
                "  ask-dao-machine paper papers/ --out out/papers\n"
                "  ask-dao-machine report --out out/demo\n"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("domains", nargs="+", help=DOMAINS_HINT)
    ap.add_argument("--out", default=str(Path.cwd() / "out"), help="输出目录（默认 ./out）")
    ap.add_argument("--limits", default="{}",
                    help="引擎限制参数，内联 JSON 字符串（不是文件路径），"
                         "例如 '{\"N\":100000,\"M\":200000}'")
    ap.add_argument("--no-viz", action="store_true", help="只出 JSON，不出可视化")
    ap.add_argument("--no-novelty", action="store_true", help="跳过新颖性门（不实查 OEIS）")
    args = ap.parse_args(argv)

    try:
        limits = json.loads(args.limits)
    except json.JSONDecodeError as e:
        print(f"--limits 需为内联 JSON 字符串（例如 '{{\"N\":100000}}'）；解析失败：{e}", file=sys.stderr)
        return 2
    if not isinstance(limits, dict):
        print("--limits 需为 JSON 对象，例如 '{\"N\":100000}'", file=sys.stderr)
        return 2

    from .pipeline import ProblemMaker
    from . import viz as viz_mod

    _TPL = Path(__file__).resolve().parent.parent.parent / "assets" / "index.html"

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
            print(f"{str(e)}\n可选域: {', '.join(maker.list_domains())}", file=sys.stderr)
            return 2
        sets[d] = ps
        f = maker.save(ps, out / f"problems_{d}.json")
        print(f"[{d}] {ps.stats()} 耗时{getattr(ps, 'elapsed', 0)}s -> {f}")

    if not args.no_viz:
        if not _TPL.exists():
            print(f"缺可视化模板 {_TPL}（安装包时带了 assets 吗？）", file=sys.stderr)
            return 1
        vd = viz_mod.make_viz(out, sets, reg, _TPL)
        print(f"[viz] -> {vd / 'index.html'}  (双击打开; 数据在 data.js)")

    # ---- 新颖性门（真实执行）：引擎不再自称新颖，由本阶段实查 OEIS 后裁决 ----
    if not args.no_novelty:
        try:
            _run_novelty(out, sets)
        except FileNotFoundError:
            print("[novelty] 缺 data/stripped.gz -> 跳过新颖性门")
            print("[novelty] 取参照系：python -m ask_dao_machine data fetch   （约 32MB，来自 oeis.org）")
        except Exception as e:                                  # noqa: BLE001
            print(f"[novelty] 失败: {e}", file=sys.stderr)

    print(f"[registry] 母题库登记总数: {reg.total}")

    # ---- 收尾：直接给出"下一步看什么"（跑完不再是一堆 JSON） ----
    try:
        from . import report as report_mod
        print("")
        report_mod.main(out)
    except Exception as e:                                      # noqa: BLE001
        print(f"[report] 跳过汇总（{e}）；可手动跑：ask-dao-machine report --out {out}")
    return 0


def _run_novelty(out: Path, sets: dict) -> None:
    """对带整数序列的记录过 novelty_gate，结果写回 JSON 并打印分级分布。

    诚实：参照系只有 OEIS 整数序列。**未被门覆盖的记录不是"新"，而是"不可判"**。
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
