# -*- coding: utf-8 -*-
"""整理 tools/：按「谁在运行它」分到子目录，并更新全部引用。

原则：
  1. 分类判据是**运行关系**，不是名字好不好看。
  2. 移动后必须保证三处还能工作：
     - src/ask_dao_machine 的 _repo_tools()（它把 tools/ 加进 sys.path 再 import）
     - tools/run_resident.py（它按文件名 subprocess）
     - 文档里的 `tools/xxx.py` 路径引用
  3. 不动任何脚本的逻辑，只挪位置。

分类：
  core/      被 src/ 调用 —— 产品依赖，不能乱动
  engines/   被 run_resident 调用 —— 长跑链路
  build/     生成产物（站点 / PPT / 架构图 / logo）—— 手动入口
  maintain/  工程维护（重构 / 修复 / 补抓语料 / 索引）—— 手动入口
  research/  研究实验（提问题 / 扫描 / 验证 / 度量）
  archive/   没有任何运行者的历史脚本（先别删，可能是证据链）
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"

LAYOUT: dict[str, list[str]] = {
    # ── 被 src/ 调用：产品依赖 ──
    "core": [
        "question_refiner", "novelty_gate", "run_paths", "retrieve_browser",
        "retrieve_context", "oeis_index", "territory_scan", "perception_module",
        "word_understand",
    ],
    # ── 被 run_resident 调用：长跑链路 ──
    "engines": [
        "all_domains_engine", "parallel_factory", "field_fusion", "deep_fusion",
        "fusion_territories", "word_fusion", "imagination_sentence",
        "browser_mass_search", "oeis_batch_gate",
    ],
    # ── 生成产物（手动入口：python tools/build/xxx.py）──
    "build": [
        "make_site", "make_site_assets", "build_paths_viz", "build_site_problems",
        "build_tree_viz", "make_problem_tree", "tree_svg", "arch_diagram",
        "problem_lineage", "make_ledger", "make_logo", "art_logo", "banner_art",
        "design_ink", "deck_spec", "deck_figs", "make_deck", "make_pptx",
    ],
    # ── 工程维护（手动入口）──
    "maintain": [
        "tools_index", "install_integrations", "fetch_wiki", "fetch_biomed_paper",
        "refetch_wiki_api", "resolve_missing_wiki", "fix_wiki_titles",
        "recompute_entry_channel", "refresh_bridge_anchors",
        "rename_modules", "fix_multiname_imports", "alias_renamed_imports",
        "repair_alias_damage",
    ],
    # ── 研究实验 ──
    "research": [
        "ai4s_harness", "arxiv_miner", "big_score", "big_score_ev", "candidate_rank",
        "composition_demo", "conjecture_search", "corpus_to_problems", "crazy_scale",
        "cross_explore", "cross_md_v3", "cross_md_v4", "cross_multidomain",
        "daily_to_tree", "dedupe_survivors", "depth_batch", "depth_sentence",
        "discovery_pipeline", "extended_probe", "field_forge", "final_candidates",
        "frust6", "frustration_index", "fusion_matrix", "genspace_scan", "graph_space",
        "grade_unseen", "humanities_math", "humanities_sig", "imagination_batch_verify",
        "imagination_deep", "imagination_run1", "imagination_verify", "iterate",
        "lateral_scan", "llm_judge_pass", "llm_judgment", "mechanism_probe",
        "mega_branch_scan", "mega_filter", "mega_scan", "method3_gen_tension",
        "method3_unified", "oeis_check", "oeis_sweep", "oeis_sweep2", "omni_scan",
        "open_branch_gen", "open_mine", "p_A4", "p_A5_yanyi", "p_B_deep",
        "p_C_ev_regrade", "p_C_integrate", "p_C_round2", "palbase_scan",
        "pcset_entropy", "problem_gate", "problem_strata", "reconstruct",
        "reconstruct_compare", "reconstruct_judge", "reconstruct_sent", "s2_bounded",
        "scale_1e9", "scale_grid", "scale_hunt", "scihist_to_problems",
        "sentence_batch", "sentence_method", "significance_vs_random", "sparse_expand",
        "station3", "tension_detector", "tension_hist", "tension_v1", "tri_verifiers",
        "understand_deep", "verify_cross_md", "web_experience", "word_interpret",
        "word_structural", "constant_engine", "build_motif_map",
    ],
    # ── 没有运行者的历史脚本 ──
    "archive": [
        "verify_hero_ab", "verify_page_effects", "verify_page_shots",
        "verify_particle_footprint", "verify_screenshot", "verify_site_http",
        "verify_water_physics",
    ],
}
# 留根的（不能被挪：长跑总控与索引生成器本身就是入口）
KEEP_ROOT = {"run_resident", "tools_index"}

# 手动入口（靠 `python tools/.../xxx.py` 手跑，没有任何"引用"能检测到）
MANUAL = {
    "make_site", "make_site_assets", "build_paths_viz", "build_site_problems",
    "build_tree_viz", "make_problem_tree", "tree_svg", "arch_diagram",
    "make_deck", "make_pptx", "deck_spec", "deck_figs",
    "make_logo", "art_logo", "banner_art",
    "install_integrations", "tools_index", "run_resident", "make_ledger",
}


def target_of(stem: str) -> str | None:
    for sub, names in LAYOUT.items():
        if stem in names:
            return sub
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    files = sorted(p for p in TOOLS.glob("*.py"))
    plan: list[tuple[Path, Path]] = []
    unplaced: list[str] = []
    for p in files:
        stem = p.stem
        if stem in KEEP_ROOT:
            continue
        sub = target_of(stem)
        if not sub:
            unplaced.append(stem)
            continue
        plan.append((p, TOOLS / sub / f"{stem}.py"))

    print(f"=== 计划移动 {len(plan)} 个 ===")
    by_sub: dict[str, list[str]] = {}
    for s, d in plan:
        by_sub.setdefault(d.parent.name, []).append(s.name)
    for sub in sorted(by_sub):
        print(f"\n▌ tools/{sub}/  （{len(by_sub[sub])} 个）")
        print("   " + " · ".join(sorted(by_sub[sub])))
    if unplaced:
        print(f"\n=== 没归类的 {len(unplaced)} 个（留在根）===")
        print("   " + " · ".join(sorted(unplaced)))

    if not a.apply:
        print("\n[dry-run] 加 --apply 执行")
        return

    for s, d in plan:
        d.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(["git", "mv", str(s), str(d)], cwd=ROOT,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            s.rename(d)
    print(f"\n[apply] 移动 {len(plan)} 个文件")


if __name__ == "__main__":
    raise SystemExit(main())
