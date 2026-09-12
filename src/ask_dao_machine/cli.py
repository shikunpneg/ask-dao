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
import re
import sys
from pathlib import Path

DOMAINS_HINT = ("aesthetics / combo / counterex / digit_base / direction / fusion / "
                "ling / math / records / sparse / all")


def _repo_tools():
    """源码运行时复用 tools/ 里的判定器（question_refiner 等）。装成 wheel 时不可用。"""
    import sys as _s
    for base in (Path.cwd(), Path(__file__).resolve().parents[2]):
        for p in [base, *base.parents]:
            if (p / "tools" / "run_paths.py").exists():
                tp = str(p / "tools")
                if tp not in _s.path:
                    _s.path.insert(0, tp)
                return p
    return None


def _cmd_ask(argv):
    """日常疑问 → 类型 + 判定路由 + 科学问题（可复用的单条命令）。"""
    ap = argparse.ArgumentParser(
        prog="ask-dao-machine ask",
        description="日常疑问 → 类型判定 + 判定路由 + 形式化后的科学问题",
        epilog=("例子:\n  ask-dao-machine ask \"为什么有些数学猜想几十年都没人证明出来？\"\n"
                "  ask-dao-machine ask \"为什么鸟群能同步转向？\" --out out/ask\n"),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("question", nargs="+", help="疑问原文（不用加引号也行，会拼起来）")
    ap.add_argument("--out", default=str(Path.cwd() / "out" / "ask"), help="输出目录")
    a = ap.parse_args(argv)
    q = " ".join(a.question).strip()
    if not _repo_tools():
        print("这条命令需要仓库里的 tools/（用源码运行或 pip install -e .）；"
              "若只需要论文支线，请用 ask-dao-machine paper。", file=sys.stderr)
        return 2
    import question_refiner as qr
    r = qr.refine({"daily_question": q, "domain": "通用"})
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rec = {"id": "ASK01", "source": "<cli ask>", "domain": "日常疑问",
           "type": f"日常疑问→{r.get('kind')}", "is_author_stated": False,
           "evidence": q, "statement": r.get("scientific_question"),
           "route": r.get("judge_route"), "status": "待实验/待评审",
           "kind": r.get("kind")}
    (out / "problems_ask.json").write_text(
        json.dumps({"domain": "ask", "generator": "ask-dao-machine/cli.py ask",
                    "counts": {"total": 1, "author_stated": 0, "machine_raised": 1},
                    "problems": [rec]}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"疑问：{q}")
    print(f"类型：{r.get('kind')}　判定路由：{r.get('judge_route')}")
    print(f"科学问题：{r.get('scientific_question')}")
    print(f"→ {out / 'problems_ask.json'}（可接 ask-dao-machine report --out {out}）")
    return 0


def _cmd_imagine(argv):
    """自造词 → 概念链（组词/拆词/还原造句/成段/解释）。"""
    ap = argparse.ArgumentParser(
        prog="ask-dao-machine imagine",
        description="想象路：自造词 → 概念（标准是「被理解」，不是真伪）",
        epilog=("例子:\n  ask-dao-machine imagine 记忆调性 --depth 3\n"
                "  ask-dao-machine imagine 熵选择 --bridge    # 过经验桥：检索现实经验作脚手架\n"
                "  ask-dao-machine imagine --pairs 经济 信息\n"
                "说明：想象路可以单独跑，也可以选择过桥；桥只做脚手架，不做裁判。\n"),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("word", nargs="?", help="要理解的概念词（与 --pairs 二选一）")
    ap.add_argument("--pairs", nargs=2, metavar=("A", "B"), help="用两个词组合出新概念")
    ap.add_argument("--depth", type=int, default=3, help="拆分深度 d（默认 3）")
    ap.add_argument("--bridge", action="store_true",
                    help="过经验桥：全量走检索（等价 RETRIEVE_ALL=1），把现实经验写成经验锚点")
    a = ap.parse_args(argv)
    if not a.word and not a.pairs:
        ap.error("给一个词，或用 --pairs A B")
    if not _repo_tools():
        print("这条命令需要仓库里的 tools/（用源码运行或 pip install -e .）。", file=sys.stderr)
        return 2
    if a.bridge:
        import os
        os.environ["RETRIEVE_ALL"] = "1"
        print("（已开启经验桥：每个组合词都会先检索现实经验；失败则自动退化为无锚点）")
    import run_paths as rp
    rp.run_imagine(argparse.Namespace(word=a.word, pairs=a.pairs, depth=a.depth))
    return 0


def _cmd_bridge(argv):
    """经验桥：把两个词接到现实经验上（维基双通道 + arXiv 回退）。只检索，不判真伪。"""
    ap = argparse.ArgumentParser(
        prog="ask-dao-machine bridge",
        description="经验桥（可选）：组合词 → 中文维基双通道（词条通道 / 搜索通道）"
                    "+ arXiv 回退 → 经验锚点。只检索，不做价值判断。",
        epilog=("例子:\n  ask-dao-machine bridge 熵 选择\n"
                "  ask-dao-machine bridge 熵 选择 --out out/bridge --no-browser   # 只读本地缓存/API\n"
                "说明：两条路可以各自单独跑，也可以选择过桥；过桥不改变任何判定。\n"),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a", help="第一个词")
    ap.add_argument("b", help="第二个词")
    ap.add_argument("--out", default=str(Path.cwd() / "out" / "bridge"), help="输出目录")
    ap.add_argument("--no-browser", action="store_true",
                    help="跳过浏览器通道（只读 data/wiki 缓存 + arXiv 回退，离线友好）")
    a = ap.parse_args(argv)
    if not _repo_tools():
        print("这条命令需要仓库里的 tools/（用源码运行或 pip install -e .）。", file=sys.stderr)
        return 2

    term, hits, search = f"{a.a}{a.b}", [], None
    if not a.no_browser:
        try:
            import retrieve_browser as rb
            r = rb.retrieve_cached(a.a, a.b) or {}
            hits = r.get("hits") or []
            search = r.get("search")
        except Exception as e:                                        # noqa: BLE001
            print(f"[bridge] 浏览器通道不可用（{type(e).__name__}），回退 arXiv", file=sys.stderr)
    if not hits:
        try:
            import retrieve_context as rc
            r = rc.retrieve(a.a, a.b) or {}
            hits = r.get("hits") or []
        except Exception as e:                                        # noqa: BLE001
            print(f"[bridge] arXiv 通道也不可用（{type(e).__name__}）；本次无脚手架",
                  file=sys.stderr)

    # 搜索通道摘要：维基里这个组合词"是否已成词"
    search_line = None
    if isinstance(search, dict):
        sn = (search.get("snippet") or "")
        m = re.search(r"共([\d,]+)条", sn)
        newpage = "您可以新建这个页面" in sn
        search_line = (f"命中 {m.group(1)} 条" if m else "（无命中统计）")
        search_line += "；尚无独立条目（维基提示可新建）" if newpage else "；词条/页面已存在"
    elif isinstance(search, str):
        search_line = search.strip().split("\n")[-1][:120]

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    payload = {"term": term, "a": a.a, "b": a.b, "hits": hits,
               "search": search, "search_line": search_line,
               "note": "只检索，不做价值判断；无命中即退化为无脚手架，不阻止理解"}
    (out / "bridge.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
    print(f"组合词：{term}")
    if hits:
        for h in hits[:3]:
            print(f"  经验锚点（{h.get('title', '')[:40]}）："
                  f"{(h.get('fragment') or '').replace(chr(10), ' ')[:120]}")
    else:
        print("  经验锚点：无（本地缓存与 arXiv 都没命中；这不影响概念是否成立）")
    if search_line:
        print(f"  搜索通道：{search_line}")
    print(f"→ {out / 'bridge.json'}（可接 ask-dao-machine report --out {out}）")
    return 0


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
    if head == "perceive":
        ap = argparse.ArgumentParser(
            prog="ask-dao-machine perceive",
            description="经验/感知入口：图像结构 → 日常疑问 → 带判定路由的科学问题",
            epilog=("例子:\n  ask-dao-machine perceive\n"
                    "  ask-dao-machine perceive photos/ --out out/perceive\n"),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        ap.add_argument("paths", nargs="*", help="图像文件或目录（不给则用 numpy 合成图，零依赖可跑）")
        ap.add_argument("--out", default=str(Path.cwd() / "out" / "perceive"), help="输出目录")
        a = ap.parse_args(argv[1:])
        from . import perceive as perceive_mod
        return perceive_mod.main(a.paths, out_dir=a.out)
    if head == "paper":
        from . import paper as paper_mod
        return paper_mod.main(argv[1:])
    if head == "run":
        from . import flow as flow_mod
        return flow_mod.main(argv[1:])
    if head == "mcp":
        from . import mcp as mcp_mod
        return mcp_mod.main(argv[1:])
    if head == "ask":
        return _cmd_ask(argv[1:])
    if head == "imagine":
        return _cmd_imagine(argv[1:])
    if head == "bridge":
        return _cmd_bridge(argv[1:])
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

    from . import banner as banner_mod
    # 裸命令 / help / --version：进来看「道」的徽标与速查（管道里自动不带颜色）
    if not argv:
        banner_mod.show()
        return 0
    if argv[0] in ("help", "?", "--help", "-h"):
        banner_mod.show()
        print(banner_mod.usage_line())
        print()
        print("子命令速查（每条都支持 --help）：")
        for cmd, desc in banner_mod.COMMANDS:
            print(f"  ask-dao-machine {cmd:<22} {desc}")
        print("\n领域跑批（多进程引擎）："
              f"ask-dao-machine <{DOMAINS_HINT}> [--out DIR] [--limits JSON]"
              " [--no-viz] [--no-novelty]")
        return 0
    if argv[0] in ("--version", "-V", "version"):
        print(f"ask-dao-machine {banner_mod.version()}")
        return 0

    rc = _dispatch(argv)
    if rc is not None:
        return rc

    ap = argparse.ArgumentParser(
        prog="ask-dao-machine",
        description="问题制造器 CLI —— 两条路（问题路产问题 / 想象路产概念）+ 母题库 + 判定器 + 出处链",
        epilog=("子命令:\n"
                "  paper <文件/目录...>    输入论文 → 输出问题清单 + REPORT.md\n"
                "  ask \"<日常疑问>\"        疑问 → 类型 + 判定路由 + 科学问题\n"
                "  imagine <自造词>        造词 → 概念（五步）\n"
                "  perceive [图像/目录]    输入图像（经验）→ 输出带判定路由的问题\n"
                "  mcp                     以 MCP server 方式运行（stdio，供 Claude Code / DSH / Cursor 等挂载）\n"
                "  report [--out DIR]      把一次跑批汇总成一页人话（写 <out>/REPORT.md）\n"
                "  imagine <自造词>        造词 → 概念（五步；--bridge 可选择过经验桥）\n"
                "  bridge <词A> <词B>      经验桥：组合词 → 维基双通道 + arXiv 回退 → 经验锚点\n"
                "  doctor                  环境自查（缺什么、下一步做什么）\n"
                "  data fetch [--force]    取 OEIS 参照系（data/stripped.gz，约 32MB）\n"
                "\n例子:\n"
                "  ask-dao-machine\n"
                "  ask-dao-machine all --out out/demo\n"
                "  ask-dao-machine math --limits '{\"N\":100000,\"M\":200000}'\n"
                "  ask-dao-machine paper papers/ --out out/papers\n"
                "  ask-dao-machine ask \"为什么有些数学猜想几十年都没人证明出来？\"\n"
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
