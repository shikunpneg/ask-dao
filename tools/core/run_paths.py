# -*- coding: utf-8 -*-
"""tools/core/run_paths.py — 统一入口：两条路的输入接口（v0.2）

系统 = 两条独立的路, 各有自己的输入接口与成功标准。

╔══════════════════════════════════════════════════════════════════════════╗
║ 问题路 (Problem Path)  —— 产问题, 需解决                                   ║
║   输入: 外部信息(视觉/听觉/文本) | 日常问题 | 母题                          ║
║   流水: 日常问题 -> 前问题 -> 科学问题 -> 基础领域 -> 问题树 -> 领域融合    ║
║   出口: 可判问题清单(带判定路由) -> AI4S 执行模块                           ║
║   标准: 答案成立 / 可判                                                     ║
╠══════════════════════════════════════════════════════════════════════════╣
║ 想象路 (Imagination Path) —— 产概念, 需解释                                ║
║   输入: 词                                                                ║
║   流水: 组词 -> 拆词(深度d) -> 还原造句(嵌套/推理/判断/比较) -> 成段 -> 解释 ║
║   出口: 被理解的概念/理论                                                  ║
║   标准: 解释语法正确 + 逻辑通畅 + 有推理判断                                ║
║   原则(不可动摇): 每个词都有意义, 只是缺想象力                              ║
╚══════════════════════════════════════════════════════════════════════════╝

用法:
  python tools/core/run_paths.py problem --input text --src <文件>
  python tools/core/run_paths.py problem --input daily --q "为什么..."
  python tools/core/run_paths.py problem --input motif --m "质数"
  python tools/core/run_paths.py imagine --word 记忆调性
  python tools/core/run_paths.py imagine --pairs 经济 信息
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
_td = HERE / "tools"
sys.path.insert(0, str(_td))
for _sd in _td.iterdir():
    if _sd.is_dir() and not _sd.name.startswith("_"):
        sys.path.insert(0, str(_sd))
sys.path.insert(0, str(HERE / "src"))

OUT = HERE / "out/demo"


# ==================== 问题路 ====================
def problem_from_text(path):
    """输入: 文本 -> 日常问题"""
    from corpus_to_problems import stage_a, stage_b, stage_c
    txt = Path(path).read_text(encoding="utf-8", errors="ignore")
    qs = []
    for q in stage_a(txt):
        q.update(stage_b(q))
        lvl, ev = stage_c(q)
        q["judgeable"] = lvl
        q["judge_evidence"] = ev
        qs.append(q)
    return qs


def problem_from_daily(question):
    """输入: 日常问题 -> 科学问题(定型)"""
    from question_refiner import classify, refine
    q = {"daily_question": question, "domain": "通用"}
    kind, dom, route = classify(q)
    r = refine(q)
    return [r]


def problem_from_motif(motif):
    """输入: 母题 -> 问题树生长"""
    from ask_dao_machine.data_motif_registry import Registry
    reg = Registry.bundled()
    hits = [m for m in reg.math_core if motif in m["name"]]
    return [{"motif": motif, "matched": [h["name"] for h in hits],
             "note": "母题 -> 方向模板 -> 实例化问题(见 make_ledger)"}]


def run_problem(args):
    print("=" * 100)
    print("问题路 —— 产问题(需解决)")
    print("=" * 100)
    if args.input == "text":
        qs = problem_from_text(args.src)
        print(f"  输入文本: {args.src}")
        print(f"  抽出日常问题: {len(qs)}")
        from collections import Counter
        c = Counter(q["judgeable"] for q in qs)
        print(f"  可判性分布: {dict(c)}")
        for q in qs[:5]:
            print(f"    [{q['judgeable']}] {q['text'][:50]}")
    elif args.input == "daily":
        qs = problem_from_daily(args.q)
        print(f"  输入日常问题: {args.q}")
        for q in qs:
            print(f"  类型: {q['kind']}  路由: {q['judge_route']}")
            print(f"  科学问题: {q['scientific_question']}")
    elif args.input == "motif":
        qs = problem_from_motif(args.m)
        for q in qs:
            print(f"  母题「{q['motif']}」命中: {q['matched']}")
            print(f"  {q['note']}")
    return qs


# ==================== 想象路 ====================
def run_imagine(args):
    print("=" * 100)
    print("想象路 —— 产概念(需解释)")
    print("=" * 100)
    print("  原则: 每个词都有意义, 只是缺想象力")
    if args.word:
        # 单概念: 拆词 -> 还原 -> 成段
        from depth_sentence import TREE, to_paragraph
        term = args.word
        if term in TREE:
            print(f"\n  「{term}」五步:")
            print(f"  ①组词: 已给")
            print(f"  ②拆词(d={args.depth}):")
            print(f"     {to_paragraph(TREE[term], args.depth)[:100]}...")
            print(f"  ⑤解释: 见 out/demo/reconstruct_*.json")
        else:
            print(f"\n  「{term}」: 未建树; 用 --pairs 生成组合")
    if args.pairs:
        # 词对 -> 组词
        from word_fusion import WORDS
        a, b = args.pairs
        for d, ws in WORDS.items():
            if a in ws:
                a = d
            if b in ws:
                b = d
        print(f"\n  组词: {args.pairs[0]}({a}) × {args.pairs[1]}({b}) -> 「{args.pairs[0]}{args.pairs[1]}」")
    return []


def main():
    ap = argparse.ArgumentParser(description="问道 · 两条路统一入口")
    sub = ap.add_subparsers(dest="path", required=True)

    p = sub.add_parser("problem", help="问题路: 产问题")
    p.add_argument("--input", choices=["text", "daily", "motif"], required=True)
    p.add_argument("--src", help="文本文件路径")
    p.add_argument("--q", help="日常问题")
    p.add_argument("--m", help="母题")

    i = sub.add_parser("imagine", help="想象路: 产概念")
    i.add_argument("--word", help="概念词(如 记忆调性)")
    i.add_argument("--pairs", nargs=2, help="词对(如 经济 信息)")
    i.add_argument("--depth", type=int, default=3, help="拆分深度 d")

    args = ap.parse_args()
    if args.path == "problem":
        run_problem(args)
    else:
        run_imagine(args)


if __name__ == "__main__":
    main()
