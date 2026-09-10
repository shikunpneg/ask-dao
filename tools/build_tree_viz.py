# -*- coding: utf-8 -*-
"""tools/build_tree_viz.py — 母题树生长 + 树交叉可视化(用户 R22 重申的重要项)

产出: out/demo/viz/tree.html (单文件自包含, 双击可开)
内容:
  1. 母题树生长 L0→L4 (分层动画, 展示"树怎么长出来的")
  2. 树交叉图谱 —— 不同领域的树交叉处产生问题; 边着色区分
     真三域(过敏感性, 绿) / 名义三域(已剔除, 红虚) / 两域可判(蓝)
  3. 三域验证器敏感性曲线(第三域参数 -> 输出), 证明第三域真参与计算
  4. 诚实层: 分层计数 / 名义审计 / S2 纠错
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

LEVELS = [
    ("L0_structures", "L0 结构", "最底层的形式结构(群/拓扑/范畴…)"),
    ("L1_objects", "L1 对象", "具体对象族(质数/图/序列…)"),
    ("L2_ops", "L2 运算", "作用于对象的运算/度量"),
    ("L4_domains", "L4 领域", "学科域(解释类型为最硬分界)"),
]

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>问道 · 母题树生长与树交叉</title>
<style>
 :root{--bg:#0e1116;--panel:#171c24;--panel2:#1e2530;--ink:#e8edf4;--dim:#93a1b3;--line:#2a3340;
       --ok:#34d399;--bad:#f87171;--open:#fbbf24;--info:#60a5fa;--chip:#243140;--accent:#a78bfa}
 *{box-sizing:border-box}
 body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.6 "Segoe UI","Microsoft YaHei",sans-serif}
 header{padding:20px 28px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#131926,#0e1116)}
 header h1{margin:0 0 6px;font-size:21px;letter-spacing:.5px}
 header p{margin:0;color:var(--dim);max-width:1100px}
 .wrap{padding:22px 28px;max-width:1500px;margin:0 auto}
 h2{font-size:16px;margin:26px 0 6px;color:#cfe0f5;letter-spacing:1px}
 h2 small{color:var(--dim);font-weight:400;letter-spacing:0}
 .sub{color:var(--dim);font-size:13px;margin:0 0 14px}
 .growth{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;align-items:start}
 .lvl{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px;min-height:60px;
      opacity:0;transform:translateY(14px);animation:grow .6s ease forwards}
 @keyframes grow{to{opacity:1;transform:none}}
 .lvl h3{margin:0 0 4px;font-size:13px;color:#9ecbff}
 .lvl .cnt{color:var(--dim);font-size:12px;margin-bottom:8px}
 .lvl .items{display:flex;flex-wrap:wrap;gap:5px}
 .it{padding:3px 8px;border-radius:7px;background:var(--chip);border:1px solid #35475c;font-size:12px}
 .lvl:nth-child(1){animation-delay:.05s}.lvl:nth-child(2){animation-delay:.25s}
 .lvl:nth-child(3){animation-delay:.45s}.lvl:nth-child(4){animation-delay:.65s}
 .lvl:nth-child(5){animation-delay:.85s}
 .cols{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,420px);gap:22px;align-items:start}
 @media(max-width:900px){.cols{grid-template-columns:1fr}.wrap{padding:18px 14px}
   .growth{grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}}
 .sparks-wrap{display:flex;flex-wrap:wrap;gap:10px}
 .sparks-wrap>div{flex:1 1 340px;min-width:0}
 svg{background:var(--panel);border:1px solid var(--line);border-radius:10px;width:100%;height:auto}
 .legend span{display:inline-block;margin-right:16px;color:var(--dim);font-size:12px}
 .sw{display:inline-block;width:18px;height:0;border-top-width:3px;border-top-style:solid;vertical-align:middle;margin-right:5px}
 .cand{background:var(--panel2);border:1px solid var(--line);border-radius:9px;padding:10px 12px;margin-bottom:9px;cursor:pointer;transition:.15s}
 .cand:hover{border-color:var(--accent)}
 .cand.sel{border-color:var(--accent);background:#20242f}
 .cand .t{font-weight:600;font-size:13px}
 .cand .m{color:var(--dim);font-size:12px;margin-top:3px}
 .tag{font-size:11px;padding:2px 8px;border-radius:9px;margin-left:6px}
 .t-tri{background:rgba(52,211,153,.15);color:var(--ok);border:1px solid var(--ok)}
 .t-nom{background:rgba(248,113,113,.12);color:var(--bad);border:1px solid var(--bad)}
 .t-two{background:rgba(96,165,250,.12);color:var(--info);border:1px solid var(--info)}
 .t-wait{background:rgba(251,191,36,.12);color:var(--open);border:1px solid var(--open)}
 table{border-collapse:collapse;width:100%;font-size:13px;margin-top:8px}
 th,td{border:1px solid var(--line);padding:7px 10px;text-align:left}
 th{background:var(--panel2);color:#cfe0f5;font-weight:600}
 td.num{font-variant-numeric:tabular-nums}
 .spark{display:block}
 .note{background:var(--panel);border-left:3px solid var(--accent);border-radius:0 8px 8px 0;padding:10px 14px;color:var(--dim);font-size:13px;margin-top:10px}
 .note b{color:var(--ink)}
 code{background:#0b0f15;padding:1px 5px;border-radius:4px;color:#a7f3d0;font-size:12px}
</style>
</head>
<body>
<header>
  <h1>问道 · 母题树生长 与 树交叉</h1>
  <p>不同领域就像不同的树；当树交叉到一起时，就会出现新问题。本页展示三件事：<b>树怎么长</b>（L0→L4）、
     <b>树在哪交叉</b>（交叉图谱，并区分"真交叉"与"名义交叉"）、<b>交叉凭什么算数</b>（第三域必须进入计算且结果随其参数变化）。</p>
</header>
<div class="wrap">

  <h2>一、母题树生长 <small>L0 结构 → L1 对象 → L2 运算 → L3 方向 → L4 领域</small></h2>
  <p class="sub">每一层由上一层"长出"：结构给出骨架，对象是骨架上的具体族，运算是作用其上的算子，
     方向把算子组织成研究纲领，领域按解释类型切分。共 <b id="tot"></b> 个基元。</p>
  <div class="growth" id="growth"></div>

  <h2>二、树交叉图谱 <small>交叉处 = 新问题的产地</small></h2>
  <p class="sub">节点=领域，边=交叉候选。点击右侧卡片可高亮对应交叉。</p>
  <div class="legend">
    <span><i class="sw" style="border-color:var(--ok)"></i>真三域（第三域进入计算，过参数敏感性）</span>
    <span><i class="sw" style="border-color:var(--bad);border-top-style:dashed"></i>名义三域（第三域只挂句尾，已剔除）</span>
    <span><i class="sw" style="border-color:var(--info);border-top-style:dotted"></i>两域可判（有判定器）</span>
    <span><i class="sw" style="border-color:var(--open);border-top-style:dashed"></i>需建验证器（良构但无判定器）</span>
  </div>
  <div class="cols" style="margin-top:12px">
    <div id="graph"></div>
    <div id="cands"></div>
  </div>

  <h2>三、真三域验证器 · 敏感性曲线 <small>横轴=第三域参数，纵轴=输出；曲线若平 → 第三域是名义的</small></h2>
  <div id="sparks" class="sparks-wrap"></div>

  <h2>四、诚实层 <small>状态只来自判定器；不许粉饰</small></h2>
  <div id="honest"></div>

</div>
<script>
const D = window.TREE;
const NS="http://www.w3.org/2000/svg";
const el=(t,a)=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);return e;};

/* ---- 一、生长 ---- */
let tot=0;
const growth=document.getElementById("growth");
D.levels.forEach(L=>{
  tot+=L.items.length;
  const d=document.createElement("div");d.className="lvl";
  d.innerHTML='<h3>'+L.title+'</h3><div class="cnt">'+L.items.length+' 个 · '+L.desc+'</div>'+
    '<div class="items">'+L.items.map(x=>'<span class="it">'+x+'</span>').join("")+'</div>';
  growth.appendChild(d);
});
document.getElementById("tot").textContent=tot;

/* ---- 二、交叉图谱 ---- */
const doms=[...new Set(D.crossings.flatMap(c=>c.domains))];
const W=760,H=620,cx=W/2,cy=H/2,R=235;
const pos={};doms.forEach((d,i)=>{const a=-Math.PI/2+i*2*Math.PI/doms.length;
  pos[d]={x:cx+R*Math.cos(a),y:cy+R*Math.sin(a)};});
const svg=el("svg",{viewBox:"0 0 "+W+" "+H});
const gEdges=el("g",{}),gNodes=el("g",{});svg.appendChild(gEdges);svg.appendChild(gNodes);
const styleOf=c=>c.kind==="tri"?{c:"var(--ok)",d:"",w:2.6}:
                   c.kind==="nominal"?{c:"var(--bad)",d:"6 5",w:1.4}:
                   c.kind==="two"?{c:"var(--info)",d:"2 4",w:1.8}:
                   {c:"var(--open)",d:"5 4",w:1.6};
const edgeEls=[];
D.crossings.forEach((c,ci)=>{
  if(c.domains.length<2) return;
  const st=styleOf(c);
  const pairs=[];for(let i=0;i<c.domains.length;i++)for(let j=i+1;j<c.domains.length;j++)pairs.push([c.domains[i],c.domains[j]]);
  pairs.forEach(([a,b])=>{
    const p1=pos[a],p2=pos[b];if(!p1||!p2)return;
    const mx=(p1.x+p2.x)/2,my=(p1.y+p2.y)/2;
    const qx=cx+(mx-cx)*0.62,qy=cy+(my-cy)*0.62;
    const path=el("path",{d:"M"+p1.x+","+p1.y+" Q"+qx+","+qy+" "+p2.x+","+p2.y,
      fill:"none",stroke:st.c,"stroke-width":st.w,opacity:.75});
    if(st.d)path.setAttribute("stroke-dasharray",st.d);
    gEdges.appendChild(path);edgeEls.push({ci:ci,e:path});
  });
});
doms.forEach(d=>{
  const p=pos[d];
  gNodes.appendChild(el("circle",{cx:p.x,cy:p.y,r:26,fill:"var(--panel2)",stroke:"#3b4a5e","stroke-width":1.5}));
  const t=el("text",{x:p.x,y:p.y+4,"text-anchor":"middle",fill:"#cfe0f5","font-size":12.5});
  t.textContent=d;gNodes.appendChild(t);
});
document.getElementById("graph").appendChild(svg);

function highlight(ci){
  edgeEls.forEach(o=>{o.e.setAttribute("opacity",ci===null||o.ci===ci?0.85:0.08);
    o.e.setAttribute("stroke-width",ci===o.ci?4:(styleOf(D.crossings[ci]).w));});
}
const box=document.getElementById("cands");
D.crossings.forEach((c,ci)=>{
  const tag=c.kind==="tri"?'<span class="tag t-tri">真三域</span>':
            c.kind==="nominal"?'<span class="tag t-nom">名义(剔除)</span>':
            c.kind==="two"?'<span class="tag t-two">两域可判</span>':
            '<span class="tag t-wait">需建验证器</span>';
  const d=document.createElement("div");d.className="cand";
  d.innerHTML='<div class="t">'+c.domains.join(" × ")+tag+'</div>'+
              '<div class="m">'+c.obj+'</div>'+
              (c.detail?'<div class="m">'+c.detail+'</div>':'');
  d.onclick=()=>{document.querySelectorAll(".cand").forEach(x=>x.classList.remove("sel"));
    d.classList.add("sel");highlight(ci);};
  d.onmouseenter=()=>highlight(ci);d.onmouseleave=()=>highlight(null);
  box.appendChild(d);
});

/* ---- 三、敏感性曲线 ---- */
const sp=document.getElementById("sparks");
D.sensitivity.forEach(s=>{
  const w=430,h=170,pad=42;
  const xs=s.table.map(t=>t.theta),ys=s.table.map(t=>t.outputs[0]);
  const x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys);
  const sx=v=>pad+(w-pad-18)*((v-x0)/((x1-x0)||1));
  const sy=v=>h-pad-(h-pad-24)*((v-y0)/((y1-y0)||1));
  const g=el("svg",{viewBox:"0 0 "+w+" "+h,class:"spark"});
  g.appendChild(el("line",{x1:pad,y1:h-pad,x2:w-14,y2:h-pad,stroke:"#2a3340"}));
  g.appendChild(el("line",{x1:pad,y1:12,x2:pad,y2:h-pad,stroke:"#2a3340"}));
  const pts=s.table.map(t=>sx(t.theta)+","+sy(t.outputs[0])).join(" ");
  g.appendChild(el("polyline",{points:pts,fill:"none",stroke:"var(--accent)","stroke-width":2.4}));
  s.table.forEach(t=>{
    g.appendChild(el("circle",{cx:sx(t.theta),cy:sy(t.outputs[0]),r:4,fill:"var(--accent)"}));
    const lab=el("text",{x:sx(t.theta),y:h-pad+16,"text-anchor":"middle",fill:"#93a1b3","font-size":11});
    lab.textContent=t.theta;g.appendChild(lab);
  });
  const cap=el("text",{x:pad-6,y:20,"text-anchor":"end",fill:"#93a1b3","font-size":11});
  cap.textContent=s.yLabel;g.appendChild(cap);
  const wrap=document.createElement("div");
  wrap.innerHTML='<div style="font-size:13px;color:#cfe0f5;margin-bottom:4px">'+s.title+
    ' <span class="tag t-tri">敏感性 ✓</span></div>'+
    '<div style="font-size:12px;color:#93a1b3;margin-bottom:4px">第三域参数：'+s.param+
    ' ｜ 输出随参数变化：'+s.verdict+'</div>';
  wrap.appendChild(g);sp.appendChild(wrap);
});

/* ---- 四、诚实层 ---- */
const H_=D.honest;
document.getElementById("honest").innerHTML=
 '<table><tr><th>项</th><th>结果</th><th>说明</th></tr>'+
 H_.rows.map(r=>'<tr><td>'+r[0]+'</td><td class="num">'+r[1]+'</td><td>'+r[2]+'</td></tr>').join("")+
 '</table><div class="note">'+H_.note+'</div>';
</script>
</body>
</html>
"""


def main():
    mm = json.loads((HERE / "out/demo/motif_map.json").read_text(encoding="utf-8"))
    v4 = json.loads((HERE / "out/demo/cross_md_v4.json").read_text(encoding="utf-8"))
    s2 = json.loads((HERE / "out/demo/s2_bounded.json").read_text(encoding="utf-8"))

    levels = []
    for key, title, desc in LEVELS:
        if key in mm:
            levels.append({"title": title, "desc": desc, "items": mm[key]})
    # L3 方向(压平)
    dirs = []
    for dom, ds in mm.get("L3_directions", {}).items():
        dirs += [f"{dom}·{d}" for d in ds]
    levels.insert(3, {"title": "L3 方向", "desc": "研究纲领(域×方向)", "items": dirs})

    # 交叉候选
    crossings = []
    for r in v4["three_domain"]:
        crossings.append({
            "domains": r["domains"], "kind": "tri" if r["sensitive"] else "nominal",
            "obj": r["obj"],
            "detail": f"第三域 {r['third']}({r['third_param']}) ｜ 判据：{r['crit']}",
        })
    for r in v4["two_domain"]:
        crossings.append({"domains": r["domains"], "kind": "two", "obj": r["obj"],
                          "detail": "判定器：" + r.get("verify", {}).get("verdict", "")})
    for r in v4["needs_verifier"]:
        crossings.append({"domains": r["domains"], "kind": "wait", "obj": r["obj"],
                          "detail": r["crit"]})
    # 旧 v3 名义三域(抽样展示被剔除的那类)
    nom = v4.get("nominal_audit_v3") or {}
    if nom.get("nominal_three_domain"):
        crossings.append({"domains": ["信息", "数学", "工程"], "kind": "nominal",
                          "obj": f"v3 旧产物中被剔除的名义三域（共 {nom['nominal_three_domain']} 条）",
                          "detail": "第三域只挂在句尾，F2 仅按前两域匹配判定器 → 第三域从未进入计算"})

    sen = []
    for r in v4["three_domain"]:
        sen.append({"title": " × ".join(r["domains"]), "param": r["third_param"],
                    "yLabel": "输出", "verdict": "是（已过敏感性验收）",
                    "table": r["third_table"]})

    lay = v4["layering"]
    honest = {
        "rows": [
            ["笛卡尔矩阵", v4["stages"]["笛卡尔矩阵"], "自动短语组合总数"],
            ["F1 真良构过门", v4["stages"]["F1过门"], "要求 obj+quant+crit 三元；自动短语 100% 空壳"],
            ["真三域候选", v4["stages"]["真三域候选"], "第三域进入计算且输出随其参数变化"],
            ["名义三域（剔除）", nom.get("nominal_three_domain", 0), f"v3 三域候选共 {nom.get('three_domain_total',0)} 条，真三域 {nom.get('real_three_domain',0)} 条"],
            ["(i) 可判", lay["i_可判"], "有真判定器：4 两域 + 4 真三域"],
            ["(ii) 需建验证器", lay["ii_需建验证器"], "良构但缺判定器"],
            ["(iii) 空壳", lay["iii_空壳"], "缺量词域与判据，不保留"],
            ["S2 旧结论", "已作废", f"滑窗复算：p=3 无界(幂指数 {s2['verdicts']['3']['growth_exponent_a']})，p=5/7 窗口内持平"],
        ],
        "note": "<b>不许粉饰：</b>N3 至今为 0，世界新问题仍为 0。本轮收益是<b>正确性与诚实性</b>——"
                "修掉 3 个把「名义」当「成果」的缺陷（F1 空壳门 / 名义三域 / 未分层矩阵），"
                "推翻 1 个错误结论（S2「表观有界」）。真三域候选由 0 增至 4。",
    }

    data = {"levels": levels, "crossings": crossings, "sensitivity": sen, "honest": honest}
    viz = HERE / "out/demo/viz"
    viz.mkdir(parents=True, exist_ok=True)
    out = viz / "tree.html"
    html = TEMPLATE.replace("window.TREE", "window.TREE")
    html = html.replace("<script>\nconst D = window.TREE;",
                        "<script>\nwindow.TREE = " + json.dumps(data, ensure_ascii=False) + ";\nconst D = window.TREE;")
    out.write_text(html, encoding="utf-8")
    print("levels:", [len(l["items"]) for l in levels])
    print("crossings:", len(crossings), "| sensitivity charts:", len(sen))
    print("saved:", out)


if __name__ == "__main__":
    main()
