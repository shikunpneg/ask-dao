# -*- coding: utf-8 -*-
"""tools/build_paths_viz.py — 两条路可视化: 节点连线树 + 概念论证（v0.4）

产出 docs/viz/paths.html（自包含, 双击可开）。
  一、两条路总览
  二、问题树（节点连线, 按领域; 展示生成来路）
  三、概念树（节点连线, 拆词深度 d 的来龙去脉）
  四、概念论证（定义→判断→比较→结论）
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "out/demo"
_td = HERE / "tools"
sys.path.insert(0, str(_td))
for _sd in _td.iterdir():
    if _sd.is_dir() and not _sd.name.startswith("_"):
        sys.path.insert(0, str(_sd))

from tree_svg import render_concept_tree, render_problem_tree  # noqa: E402

TPL = r"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8">
<title>问道 · 两条路</title>
<style>
:root{--bg:#0e1116;--panel:#171c24;--panel2:#1e2530;--ink:#e8edf4;--dim:#93a1b3;--line:#2a3340;
      --ok:#34d399;--open:#fbbf24;--info:#60a5fa;--accent:#c0392b;--gold:#d4a373}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.7 "Segoe UI","Microsoft YaHei",sans-serif}
header{padding:34px 28px 24px;text-align:center;border-bottom:1px solid var(--line);
       background:linear-gradient(180deg,#141a24,#0e1116)}
header img{width:118px;height:118px;border-radius:14px;box-shadow:0 6px 30px rgba(0,0,0,.65)}
header h1{margin:14px 0 4px;font-size:30px;letter-spacing:8px;font-weight:600}
header .slogan{color:var(--gold);font-size:14px;letter-spacing:2px;margin:6px 0 0}
.wrap{max-width:1180px;margin:0 auto;padding:26px 28px 60px}
h2{font-size:19px;margin:40px 0 6px;color:#cfe0f5;border-left:4px solid var(--accent);padding-left:12px}
.sub{color:var(--dim);font-size:13px;margin:6px 0 14px}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px}
.card h3{margin:0 0 8px;font-size:16px}
.card .tag{font-size:11px;padding:2px 8px;border-radius:9px;margin-left:6px}
.t-prob{background:rgba(96,165,250,.14);color:var(--info);border:1px solid var(--info)}
.t-imag{background:rgba(212,163,115,.16);color:var(--gold);border:1px solid var(--gold)}
.flow{color:var(--dim);font-size:13px;margin:9px 0 4px}
.flow b{color:#cfe0f5}
.tree-block{background:var(--panel);border:1px solid var(--line);border-radius:12px;
            padding:12px 14px;margin-bottom:16px;overflow-x:auto}
.tree-block h4{margin:0 0 4px;font-size:15px;color:var(--gold);letter-spacing:1px}
.tree-block .meta{color:var(--dim);font-size:12px;margin:0 0 8px}
.arg{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 20px;margin-bottom:14px}
.arg h4{margin:0 0 10px;color:var(--gold);letter-spacing:2px;font-size:16px}
.arg p{margin:9px 0;font-size:14px;line-height:1.9;color:#d6dee8}
.arg .k{color:var(--info);font-weight:600}
.arg .c{color:var(--accent);font-weight:600}
.arg .g{color:var(--ok);font-weight:600}
.foot{color:var(--dim);font-size:12.5px;margin-top:34px;border-top:1px solid var(--line);padding-top:16px}
code{background:#0b0f15;padding:1px 6px;border-radius:4px;color:#a7f3d0;font-size:12.5px}
</style></head><body>
<header>
  <img src="logo_web.png" alt="道">
  <h1>问道</h1>
  <p class="slogan">道生一，一生二，二生三，三生万物</p>
</header>
<div class="wrap">

<h2>一、两条路</h2>
<p class="sub">不是"问答机"——两条<strong>互相独立</strong>的路：一条生产<strong>问题</strong>（待解决），一条生产<strong>概念</strong>（待解释）。</p>
<div class="grid2">
  <div class="card"><h3>问题路<span class="tag t-prob">产问题 · 需解决</span></h3>
    <div class="flow">输入：<b>外部信息</b>（视觉/听觉/文本）· <b>日常问题</b> · <b>母题</b></div>
    <div class="flow">流水：日常问题 → 前问题 → 科学问题 → 基础领域 → 问题树 → 领域融合</div>
    <div class="flow">出口：可判问题清单（带判定路由）→ AI4S 执行</div>
    <div class="flow">标准：<b>答案成立 / 可判</b></div>
  </div>
  <div class="card"><h3>想象路<span class="tag t-imag">产概念 · 需解释</span></h3>
    <div class="flow">输入：<b>词</b></div>
    <div class="flow">流水：组词 → 拆词(深度d) → 还原造句 → 成段 → 解释</div>
    <div class="flow">出口：被理解的概念 / 理论</div>
    <div class="flow">标准：<b>语法正确 + 逻辑通畅 + 有推理判断</b></div>
    <div class="flow" style="color:var(--gold)">原则：每个词都有意义，只是缺想象力</div>
  </div>
</div>

<h2>二、问题树<span class="sub" style="display:inline"> · 生成来路（按领域）</span></h2>
<p class="sub" id="ptree-sub"></p>
<div id="ptree"></div>

<h2>三、概念树<span class="sub" style="display:inline"> · 拆词的来龙去脉</span></h2>
<p class="sub">看到词 → 问"它是什么?" → 拆实体 → 再问 → 拆到原子概念。深度 d 是变量。</p>
<div id="ctree"></div>

<h2>四、概念论证<span class="sub" style="display:inline"> · 定义 → 判断 → 比较 → 结论</span></h2>
<p class="sub">段落不是描述，是<strong>论证</strong>：解释现象、做出判断、与对立概念划界。</p>
<div id="args"></div>

<div class="foot">
  问道 · ask-dao-machine v0.4 —— 数据来自 <code>out/demo/*.json</code>；本页由 <code>tools/build_paths_viz.py</code> 生成。<br>
  <strong>诚实边界</strong>：机器至今未产出经三重门槛的世界新问题（N3 = 0）；"检索未见"不等于"新"。
</div>
</div>
<script>
const D = window.DATA;
/* 二、问题树: 每领域一棵 */
let pt = '';
D.problem_trees.forEach(t => {
  pt += '<div class="tree-block"><h4>'+t.domain+'</h4>'
      + '<p class="meta">'+t.n+' 条 · 判定路由示例：'+(t.route||'—')+'</p>'
      + t.svg + '</div>';
});
document.getElementById('ptree').innerHTML = pt;
document.getElementById('ptree-sub').textContent =
  '共 '+D.problem_total+' 条，覆盖 '+D.problem_trees.length+' 个领域';

/* 三、概念树 */
let ct = '';
D.concept_trees.forEach(t => {
  ct += '<div class="tree-block"><h4>'+t.name+'</h4>'
      + '<p class="meta">自然深度 d = '+t.depth+' · 从概念拆到原子</p>'
      + t.svg + '</div>';
});
document.getElementById('ctree').innerHTML = ct;

/* 四、概念论证 */
let at = '';
Object.keys(D.arguments).forEach(name => {
  const a = D.arguments[name];
  at += '<div class="arg"><h4>'+name+'</h4>'
      + '<p><span class="k">定义</span>　'+(a.define||'')+'</p>'
      + '<p><span class="k">据此可以推断</span>　'+(a.judge_1||'')+'</p>'
      + (a.judge_2 ? '<p><span class="k">更进一步</span>　'+a.judge_2+'</p>' : '')
      + (a.compare ? '<p><span class="c">但必须区分</span>　'+a.compare+'</p>' : '')
      + (a.conclude ? '<p><span class="g">因此</span>　'+a.conclude+'</p>' : '')
      + '</div>';
});
document.getElementById('args').innerHTML = at;
</script></body></html>
"""


def load(p, default=None):
    f = OUT / p
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else default


def main():
    manifest = load("discovery_manifest.json", {"problems": []})
    judge = load("reconstruct_judge.json", {})
    compare = load("reconstruct_compare.json", {})

    # 概念树(来自 depth_sentence / depth_batch 的真实树结构)
    from depth_sentence import TREE as TREE_A
    try:
        from depth_batch import TREES as TREE_B, tree_depth
    except Exception:
        TREE_B, tree_depth = {}, (lambda n: 3)

    trees = {}
    for name, t in TREE_A.items():
        trees[name] = {"raw": t, "depth": tree_depth(t)}
    for name, t in TREE_B.items():
        if name not in trees:
            trees[name] = {"raw": t, "depth": tree_depth(t)}

    concept_trees = []
    for name, t in trees.items():
        try:
            svg = render_concept_tree(t["raw"])
        except Exception as e:
            svg = f'<p class="meta">渲染失败: {e}</p>'
        concept_trees.append({"name": name, "depth": t["depth"], "svg": svg})

    # 问题树: 按领域分组, 每域最多 12 条
    by_dom = {}
    for p in manifest.get("problems", []):
        by_dom.setdefault(p.get("domain", "其他"), []).append(p)
    problem_trees = []
    for dom, ps in sorted(by_dom.items(), key=lambda kv: -len(kv[1])):
        shown = ps[:12]
        rows = [{"statement": (p.get("statement") or p.get("scientific_question") or "")[:18],
                 "status": p.get("status", "")[:8]} for p in shown]
        svg = render_problem_tree(dom, f"{len(ps)} 条", rows)
        route = shown[0].get("judge_route", "") if shown else ""
        problem_trees.append({"domain": dom, "n": len(ps), "route": route, "svg": svg})

    args = dict(judge)
    args.update(compare)

    data = {"problem_total": len(manifest.get("problems", [])),
            "problem_trees": problem_trees,
            "concept_trees": concept_trees,
            "arguments": args}

    from shutil import copyfile
    logo = HERE / "assets" / "logo_white.png"  # 深色页面用白底版
    html = TPL.replace("<script>\nconst D = window.DATA;",
                       "<script>\nwindow.DATA = " + json.dumps(data, ensure_ascii=False)
                       + ";\nconst D = window.DATA;")
    for viz in (OUT / "viz", HERE / "docs" / "viz"):
        viz.mkdir(parents=True, exist_ok=True)
        if logo.exists():
            copyfile(logo, viz / "logo_web.png")
        (viz / "paths.html").write_text(html, encoding="utf-8")
    print(f"问题树 {len(problem_trees)} 域 / 概念树 {len(concept_trees)} 个 / 论证 {len(args)} 个")
    print("saved:", HERE / "docs" / "viz" / "paths.html")


if __name__ == "__main__":
    main()
