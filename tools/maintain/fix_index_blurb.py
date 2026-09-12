# -*- coding: utf-8 -*-
"""修 tools_index.py 的两处：(1) blurb 剥离前缀支持子目录 (2) 加手动入口白名单。"""
from pathlib import Path

TI = Path(r"E:\ask-dao\ask-dao-machine\tools\tools_index.py")
t = TI.read_text(encoding="utf-8")

# (1) blurb：原来的 ^[\w/\.]+\.py\s*—\s* 无法匹配 "tools/core/xxx.py — "（含 - 和目录）
old = '    line = re.sub(r"^[\\w/\\.]+\\.py\\s*—\\s*", "", line)      # 去掉 "xxx.py — " 前缀'
new = '    line = re.sub(r"^(?:[\\w/\\.\\-]+[/\\\\])?[\\w\\.\\-]+\\.py\\s*[—\\-]+\\s*", "", line)\n' \
      '    line = re.sub(r"^(?:tools[/\\\\])?(?:core|engines|build|maintain|research|archive|site)[/\\\\]?[\\w\\.\\-]*\\.py\\s*[—\\-]+\\s*", "", line)'
if old in t:
    t = t.replace(old, new)
    print("  ✓ blurb 前缀剥离已支持子目录路径")
else:
    # 兜底：直接按行找
    import re
    t2 = re.sub(r'\n\s*line = re\.sub\(r"\^\[\\w/\\\.\]\+\\\.py.*?\n',
                '\n    line = re.sub(r"^(?:[\\w/\\.\\-]+[/\\\\])?[\\w\\.\\-]+\\.py\\s*[—\\-]+\\s*", "", line)\n',
                t, count=1)
    if t2 != t:
        t = t2
        print("  ✓ blurb 前缀剥离已修（正则回退路径）")
    else:
        print("  ! 没找到 blurb 那行，请人工看一眼")

# (2) 手动入口白名单
if "MANUAL = {" not in t:
    anchor = "\nlive = sources()\n"
    add = '''
# 手动入口白名单：靠 `python tools/<sub>/xxx.py` 手跑，没有任何「引用」能检测到。
# 这是上一版审计的盲点 —— 它们被误判进「没有运行者」，其实是被手跑的。
MANUAL = {
    "make_site", "make_site_assets", "build_paths_viz", "build_site_problems",
    "build_tree_viz", "make_problem_tree", "tree_svg", "arch_diagram",
    "make_deck", "make_pptx", "deck_spec", "deck_figs", "design_ink",
    "make_logo", "art_logo", "banner_art", "make_ledger",
    "install_integrations", "tools_index", "run_resident",
    "reorganize_tools", "fix_tools_layout_refs", "fix_tools_layout_refs2",
}
'''
    t = t.replace(anchor, add + "\nlive = sources()\nfor _n in MANUAL:\n    live.setdefault(_n, set()).add(\"手动入口\")\n", 1)
    print("  ✓ 已加手动入口白名单")
else:
    print("  · 白名单已存在")

TI.write_text(t, encoding="utf-8")
print("完成")
