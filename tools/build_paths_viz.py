# -*- coding: utf-8 -*-
"""tools/build_paths_viz.py — 两条路可视化: 问题树 + 概念树 + 概念论证（v0.3）

产出 out/demo/viz/paths.html（自包含, 双击可开）。
内容:
  一、两条路总览（问题路 / 想象路）
  二、问题树（来自 discovery_manifest）
  三、概念树（深度展开, 来自 depth_batch）
  四、概念论证（定义→判断→比较→结论, 来自 reconstruct_*）
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "out/demo"

TPL = r"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8">
<title>问道 · 两条路</title>
<style>
:root{--bg:#0e1116;--panel:#171c24;--panel2:#1e2530;--ink:#e8edf4;--dim:#93a1b3;--line:#2a3340;
      --ok:#34d399;--open:#fbbf24;--info:#60a5fa;--accent:#c0392b;--gold:#d4a373}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.7 "Segoe UI","Microsoft YaHei",serif}
header{padding:36px 28px 24px;text-align:center;border-bottom:1px solid var(--line);
       background:linear-gradient(180deg,#141a24,#0e1116)}
header img{width:104px;height:104px;border-radius:12px;box-shadow:0 4px 26px rgba(0,0,0,.6)}
header h1{margin:12px 0 4px;font-size:30px;letter-spacing:6px;font-weight:600}
header .slogan{color:var(--gold);font-size:14px;letter-spacing:1.5px;margin:6px 0 0}
@media(max-width:640px){header h1{letter-spacing:4px;font-size:25px}
  .wrap{padding:18px 14px 44px} .grid2{grid-template-columns:1fr}}
.wrap{max-width:1180px;margin:0 auto;padding:26px 28px 60px}
h2{font-size:19px;margin:38px 0 6px;color:#cfe0f5;border-left:4px solid var(--accent);padding-left:12px}
.sub{color:var(--dim);font-size:13px;margin:6px 0 16px}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px}
.card h3{margin:0 0 8px;font-size:16px}
.card .tag{font-size:11px;padding:2px 8px;border-radius:9px;margin-left:6px}
.t-prob{background:rgba(96,165,250,.14);color:var(--info);border:1px solid var(--info)}
.t-imag{background:rgba(212,163,115,.16);color:var(--gold);border:1px solid var(--gold)}
.flow{color:var(--dim);font-size:13px;margin:10px 0 4px}
.flow b{color:#cfe0f5}
table{border-collapse:collapse;width:100%;font-size:13.5px;margin-top:10px}
th,td{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}
th{background:var(--panel2);color:#cfe0f5;font-weight:600}
tr:hover td{background:#1b222c}
.pill{font-size:11px;padding:1px 7px;border-radius:8px;white-space:nowrap}
.p-open{background:rgba(251,191,36,.13);color:var(--open)}
.p-ok{background:rgba(52,211,153,.13);color:var(--ok)}
.p-n{background:rgba(147,161,179,.14);color:var(--dim)}
.ct{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 18px;margin-bottom:12px}
.ct h4{margin:0 0 6px;font-size:15px;color:var(--gold);letter-spacing:2px}
.ct .para{font-size:13.5px;color:#cfd8e3;line-height:1.85}
.ct .d{font-size:12px;color:var(--dim);display:block;margin-top:6px}
.arg{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 20px;margin-bottom:14px}
.arg h4{margin:0 0 10px;color:var(--gold);letter-spacing:2px;font-size:16px}
.arg p{margin:8px 0;font-size:14px;line-height:1.9;color:#d6dee8}
.arg .k{color:var(--info);font-weight:600}
.arg .c{color:var(--accent);font-weight:600}
.arg .g{color:var(--ok);font-weight:600}
.bar{display:inline-block;height:9px;border-radius:5px;background:var(--gold);vertical-align:middle;margin-right:6px}
.foot{color:var(--dim);font-size:12.5px;margin-top:34px;border-top:1px solid var(--line);padding-top:16px}
code{background:#0b0f15;padding:1px 6px;border-radius:4px;color:#a7f3d0;font-size:12.5px}
</style></head><body>
<header>
  <img src="../logo_web.png" alt="道">
  <h1>问道</h1>
  <p class="slogan">道生一，一生二，二生三，三生万物</p>
</header>
<div class="wrap">

<h2>一、两条路</h2>
<p class="sub">系统不是"问答机"，而是两条<strong>互相独立</strong>的路：一条生产<strong>问题</strong>（待解决），一条生产<strong>概念</strong>（待解释）。</p>
<div class="grid2">
  <div class="card">
    <h3>问题路<span class="tag t-prob">产问题 · 需解决</span></h3>
    <div class="flow">输入：<b>外部信息</b>（视觉/听觉/文本）· <b>日常问题</b> · <b>母题</b></div>
    <div class="flow">流水：日常问题 → 前问题 → 科学问题 → 基础领域 → 问题树 → 领域融合</div>
    <div class="flow">出口：可判问题清单（带判定路由）→ AI4S 执行</div>
    <div class="flow">标准：<b>答案成立 / 可判</b></div>
  </div>
  <div class="card">
    <h3>想象路<span class="tag t-imag">产概念 · 需解释</span></h3>
    <div class="flow">输入：<b>词</b></div>
    <div class="flow">流水：组词 → 拆词(深度d) → 还原造句 → 成段 → 解释</div>
    <div class="flow">出口：被理解的概念 / 理论</div>
    <div class="flow">标准：<b>语法正确 + 逻辑通畅 + 有推理判断</b></div>
    <div class="flow" style="color:var(--gold)">原则：每个词都有意义，只是缺想象力</div>
  </div>
</div>

<h2>二、问题树<span class="sub" style="display:inline"> · 机器产出的问题（含判定路由）</span></h2>
<p class="sub" id="ptree-sub"></p>
<div id="ptree"></div>

<h2>三、概念树<span class="sub" style="display:inline"> · 拆词（深度 d）</span></h2>
<p class="sub">看到词 → 问"它是什么?" → 拆实体 → 再问 → 拆到原子概念。深度是变量。</p>
<div id="ctree"></div>

<h2>四、概念论证<span class="sub" style="display:inline"> · 定义 → 判断 → 比较 → 结论</span></h2>
<p class="sub">段落不是描述，是<strong>论证</strong>：它解释现象、做出判断、与对立概念划界。</p>
<div id="args"></div>

<div class="foot">
  问道 · ask-dao-machine v0.3 —— 数据来自 <code>out/demo/*.json</code>；本页由
  <code>tools/build_paths_viz.py</code> 生成。<br>
  <strong>诚实边界</strong>：机器至今未产出经三重门槛的世界新问题（N3 = 0）；
  "检索未见"不等于"新"。
</div>
</div>
<script>
const D = window.DATA;

/* 问题树: 按领域分组 */
const byDom = {};
D.problems.forEach(p => { (byDom[p.domain] = byDom[p.domain] || []).push(p); });
const doms = Object.keys(byDom).sort((a,b)=>byDom[b].length-byDom[a].length);
let pt = '<table><tr><th style="width:96px">领域</th><th>问题（含判定路由）</th></tr>';
doms.forEach(d => {
  const rows = byDom[d];
  pt += '<tr><td><b>'+d+'</b><br><span class="pill p-n">'+rows.length+' 条</span></td><td>';
  rows.slice(0,6).forEach(p => {
    const st = (p.status||'');
    const cls = st.indexOf('开放')>=0?'p-open':(st.indexOf('验证')>=0?'p-ok':'p-n');
    pt += '<div style="margin-bottom:7px">'+ (p.statement||'').slice(0,110)
        + ' <span class="pill '+cls+'">'+st.slice(0,10)+'</span>'
        + '<div class="flow" style="margin:2px 0 0">路由：'+(p.judge_route||'—')+'</div></div>';
  });
  if (rows.length > 6) pt += '<div class="flow">… 另有 '+(rows.length-6)+' 条</div>';
  pt += '</td></tr>';
});
pt += '</table>';
document.getElementById('ptree').innerHTML = pt;
document.getElementById('ptree-sub').textContent =
  '共 '+D.problems.length+' 条，覆盖 '+doms.length+' 个领域';

/* 概念树 */
let ct = '';
Object.keys(D.concepts).forEach(name => {
  const c = D.concepts[name];
  ct += '<div class="ct"><h4>'+name+'</h4><div class="para">'+c.para+'</div>'
      + '<span class="d">自然深度 d = '+c.depth+'</span></div>';
});
document.getElementById('ctree').innerHTML = ct;

/* 概念论证 */
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
    if not f.exists():
        return default
    return json.loads(f.read_text(encoding="utf-8"))


def main():
    manifest = load("discovery_manifest.json", {"problems": []})
    depth = load("depth_batch.json", {})
    judge = load("reconstruct_judge.json", {})
    compare = load("reconstruct_compare.json", {})

    # 合并论证(compare 更全, judge 补充)
    args = {}
    for k, v in judge.items():
        args[k] = v
    for k, v in compare.items():
        args[k] = v

    concepts = {}
    for name, v in depth.items():
        concepts[name] = {"depth": v.get("depth", 3), "para": v.get("para", "")}

    data = {"problems": manifest.get("problems", []),
            "concepts": concepts, "arguments": args}

    # 输出两份: out/(gitignored, 本地用) 与 docs/viz/(入库, README 引用)
    html = TPL.replace("<script>\nconst D = window.DATA;",
                       "<script>\nwindow.DATA = " + json.dumps(data, ensure_ascii=False)
                       + ";\nconst D = window.DATA;")
    from shutil import copyfile
    logo = HERE / "assets" / "logo.png"
    for viz in (OUT / "viz", HERE / "docs" / "viz"):
        viz.mkdir(parents=True, exist_ok=True)
        if logo.exists():
            copyfile(logo, viz / "logo_web.png")
        (viz / "paths.html").write_text(html, encoding="utf-8")
    print(f"问题 {len(data['problems'])} 条 | 概念树 {len(concepts)} 个 | 论证 {len(args)} 个")
    print("saved:", OUT / "viz" / "paths.html", "|", HERE / "docs" / "viz" / "paths.html")


if __name__ == "__main__":
    main()
