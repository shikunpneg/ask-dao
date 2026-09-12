# -*- coding: utf-8 -*-
"""在 HTTP 下验证站点（线上同源条件）：水面模式 / 物理 / 整页背景统一 / 粒子存在。

验证副本写进 docs/（已被 .gitignore 忽略），通过 http://127.0.0.1:8000/docs/ 访问。
"""
import json
import re
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CHROME = Path(r"C:\Users\16532\AppData\Local\ms-playwright\chromium-1234\chrome-win64\chrome.exe")
if not CHROME.exists():
    CHROME = Path(r"C:\Users\16532\AppData\Local\ms-playwright\chromium-1223\chrome-win64\chrome.exe")
BASE = "http://127.0.0.1:8123/docs/"

PROBE = r"""
<script>
(function(){
  function report(o){ var d=document.createElement('div'); d.id='probe';
    d.textContent=JSON.stringify(o); document.body.appendChild(d); }
  function wait(ms){ return new Promise(function(r){ setTimeout(r,ms); }); }
  async function run(){
    var t0 = Date.now();
    while(Date.now()-t0 < 12000 && !window.__lakeReady) await wait(100);
    await wait(1200);
    var out = { lakeReady: !!window.__lakeReady, waterMode: window.__waterMode || null,
                lakeSize: window.__lakeSize || null, hasWaterApi: !!window.__water };
    var cv = document.getElementById('lakeGL');
    if(cv && cv.getContext){
      var g = null; try{ g = cv.getContext('webgl'); }catch(e){}
      out.canvasSize = [cv.width, cv.height];
      if(g){
        var pts = [];
        [[.12,.25],[.5,.4],[.85,.7]].forEach(function(p){
          var b = new Uint8Array(4);
          g.readPixels(Math.floor(cv.width*p[0]), Math.floor(cv.height*p[1]), 1,1,
                       g.RGBA, g.UNSIGNED_BYTE, b);
          pts.push(Array.from(b.slice(0,3)));
        });
        out.canvasPixels = pts;
      }
    }
    // 道字粒子：采样成功时 canvas 上应有笔画；失败则显示真实书法图
    out.daoFallbackShown = !!(document.getElementById('daoFallback') &&
                              document.getElementById('daoFallback').classList.contains('on'));
    // 全页墨点层是否有内容（触发一次合成指针事件后再看）
    var ink = document.getElementById('inkLayer');
    out.inkLayerSize = ink ? [ink.width, ink.height] : null;
    // 指针事件路径
    for(var k=0;k<12;k++){
      document.dispatchEvent(new PointerEvent('pointermove',
        {clientX: 200 + k*12, clientY: 300 + k*8, bubbles: true, pointerType:'mouse', isPrimary:true}));
      await wait(30);
    }
    await wait(500);
    out.inkCountAfterPointer = (window.__ink ? window.__ink.count() : -1);
    // 直接注入路径（接口自检）
    if(window.__ink){
      var before = window.__ink.alphaSum();
      window.__ink.spawn(400, 300, 60);
      await wait(250);
      out.inkAlphaBefore = before;
      out.inkAlphaAfter = window.__ink.alphaSum();
    }
    report(out);
  }
  addEventListener('load', function(){ run(); });
})();
</script>
</body>"""

SELFTEST = r"""
<script>
(function(){
  function report(o){ var d=document.createElement('div'); d.id='selftest';
    d.textContent=JSON.stringify(o); document.body.appendChild(d); }
  function wait(ms){ return new Promise(function(r){ setTimeout(r,ms); }); }
  async function run(){
    for(var i=0;i<80 && !(window.__water && window.__lakeReady); i++) await wait(100);
    if(!window.__water){ report({ok:false, mode:window.__waterMode||'none'}); return; }
    var W = window.__water;
    function settle(n){ for(var i=0;i<n;i++) W.step(1,true); }
    function stepQ(n){ for(var i=0;i<n;i++) W.step(1,true); }
    function field(){ return W.readHeight(); }
    function maxGrad(f){ var g=0;
      for(var y=0;y<f.h;y++) for(var x=1;x<f.w;x++){ var d=Math.abs(f.data[y*f.w+x]-f.data[y*f.w+x-1]); if(d>g)g=d; }
      for(var y2=1;y2<f.h;y2++) for(var x2=0;x2<f.w;x2++){ var d2=Math.abs(f.data[y2*f.w+x2]-f.data[(y2-1)*f.w+x2]); if(d2>g)g=d2; }
      return +g.toFixed(5); }
    function peakOf(f){ var p=0; for(var i=0;i<f.data.length;i++){ var a=Math.abs(f.data[i]); if(a>p)p=a; } return +p.toFixed(4); }
    function radial(f){ var cx=(f.w-1)/2, cy=(f.h-1)/2, B=6, nb=Math.ceil(Math.max(f.w,f.h)/2/B)+1;
      var sum=new Float64Array(nb), cnt=new Float64Array(nb);
      for(var y=0;y<f.h;y++) for(var x=0;x<f.w;x++){ var d=Math.hypot(x-cx,y-cy), b=Math.floor(d/B);
        if(b<nb){ sum[b]+=Math.abs(f.data[y*f.w+x]); cnt[b]++; } }
      var out=[]; for(var i=1;i<nb;i++) if(cnt[i]) out.push({r:i*B, m:sum[i]/cnt[i]});
      return out; }
    function frontR(pr){ var best=0,br=0; for(var i=0;i<pr.length;i++) if(pr[i].m>best){best=pr[i].m;br=pr[i].r;} return br; }
    function bandMean(f,x0,x1){ var cy=Math.floor(f.h/2), s=0,c=0;
      for(var y=cy-6;y<=cy+6;y++) for(var x=Math.floor(f.w*x0);x<Math.floor(f.w*x1);x++){
        if(y<0||y>=f.h) continue; s+=Math.abs(f.data[y*f.w+x]); c++; } return c?+(s/c).toFixed(5):0; }
    // 环带平均（以水花落点为中心）
    function ringMean(f, r0, r1){
      var cx=Math.floor(f.w*0.5), cy=Math.floor(f.h*0.5), s=0, c=0;
      for(var y=0;y<f.h;y++) for(var x=0;x<f.w;x++){
        var d=Math.hypot(x-cx,y-cy); if(d>=r0 && d<r1){ s+=Math.abs(f.data[y*f.w+x]); c++; } }
      return c? s/c : 0;
    }

    settle(1200);
    var f0 = field();
    var flat = {maxGrad: maxGrad(f0), peak: peakOf(f0)};
    W.drop(0.5,0.5,0.24,0.040);
    var trace=[], series=[], acc=0;
    var ks=[]; for(var kk=10; kk<=420; kk+=10) ks.push(kk);
    ks.forEach(function(k){ stepQ(k-acc); acc=k;
      var f=field();
      trace.push({k:k, peak:peakOf(f), b40:+ringMean(f,30,50).toFixed(5),
                  b100:+ringMean(f,90,110).toFixed(5), b180:+ringMean(f,170,190).toFixed(5)});
      series.push([k, ringMean(f,30,50), ringMean(f,90,110), ringMean(f,170,190)]);
    });
    function argmaxTime(idx){ var best=-1, bk=0;
      series.forEach(function(r){ if(r[idx]>best){best=r[idx]; bk=r[0];} }); return {k:bk, v:+best.toFixed(5)}; }
    var arr60 = argmaxTime(1), arr120 = argmaxTime(2), arr200 = argmaxTime(3);
    settle(1600); W.drop(0.36,0.5,0.24,0.040); stepQ(150);
    var one = {mid: bandMean(field(),0.45,0.55), peak: peakOf(field())};
    settle(1600); W.drop(0.36,0.5,0.24,0.040); W.drop(0.64,0.5,0.24,0.040); stepQ(150);
    var two = {mid: bandMean(field(),0.45,0.55), peak: peakOf(field())};
    report({ok:true, mode:window.__waterMode, sim:W.size(), flat:flat, trace:trace, one:one, two:two,
      arrival:{r60:arr60, r120:arr120, r200:arr200},
      verdict:{ flat_ok: flat.maxGrad < 0.005,
                propagates: arr60.k < arr120.k && arr120.k <= arr200.k + 10
                            && arr120.v > 0.004,
                decays: trace[trace.length-1].peak < Math.max(trace[0].peak, 0.001),
                interference: two.mid > one.mid*1.2 }});
  }
  addEventListener('load', function(){ run(); });
})();
</script>
</body>"""

STYLE = ("<style id='v'>.hero{height:900px !important;min-height:900px !important;}"
         ".card,.path-card,.doc,.figure,.label,.g-line,.g-divider,.q-item,#heroLine"
         "{opacity:1 !important;transform:none !important;}")


def build(name, extra="", style=""):
    html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    html = re.sub(r'\s*<link[^>]*fonts\.(googleapis|gstatic)[^>]*>', '', html)
    if style:
        html = html.replace("</head>", style + "</style></head>", 1)
    if extra:
        html = html.replace("</body>", extra, 1)
    p = ROOT / "docs" / name
    p.write_text(html, encoding="utf-8")
    return BASE + name


def dom(url, budget=22000, size="900,700"):
    r = subprocess.run([str(CHROME), "--headless=new", "--disable-gpu", "--no-sandbox",
                        "--enable-unsafe-swiftshader", "--use-gl=angle", "--use-angle=swiftshader",
                        f"--window-size={size}", f"--virtual-time-budget={budget}", "--dump-dom", url],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
    return r.stdout or ""


def shot(url, out, w=1000, h=1500):
    out.unlink(missing_ok=True)
    p = subprocess.Popen([str(CHROME), "--headless=new", "--disable-gpu", "--no-sandbox",
                          "--enable-unsafe-swiftshader", "--use-gl=angle", "--use-angle=swiftshader",
                          "--hide-scrollbars", "--force-device-scale-factor=1",
                          f"--window-size={w},{h}", f"--screenshot={out}", url],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        p.wait(timeout=120)
    except subprocess.TimeoutExpired:
        p.kill(); return False
    return out.exists()


# 1) 模式/纹理/粒子探针
u = build("_v_probe.html", PROBE)
d = dom(u)
m = re.search(r'<div id="probe">(.*?)</div>', d, re.S)
print("=== 1. 运行模式与纹理探针 ===")
print(json.dumps(json.loads(m.group(1)), ensure_ascii=False, indent=1) if m else "未取回")

# 2) 水面物理自检
u = build("_v_water.html", SELFTEST)
d = dom(u, budget=30000)
m = re.search(r'<div id="selftest">(.*?)</div>', d, re.S)
print("\n=== 2. 水面物理自检（HTTP/WebGL） ===")
if m:
    w = json.loads(m.group(1))
    print(json.dumps(w, ensure_ascii=False, indent=1))
    if w.get("ok"):
        print("判定:", " ".join(f"{k}={'PASS' if v else 'FAIL'}" for k, v in w["verdict"].items()))
else:
    print("未取回")

# 3) 整页背景统一（水面开/关对照，逐段）
print("\n=== 3. 整页背景统一性（逐段，内容位移法） ===")
print(f"{'位移':>6}{'水面版细节':>12}{'关水面版':>10}{'差异':>8}{'水面版均值':>11}")
for offset in (0, 1500, 3000, 4500):
    css = STYLE + (f"section{{margin-top:-{offset}px;}}" if offset else "")
    u_on = build(f"_v_on_{offset}.html", "", css)
    u_off = build(f"_v_off_{offset}.html", "", css + "#lakeGL{display:none !important;}")
    a_png, b_png = ROOT / "out" / f"h_{offset}_on.png", ROOT / "out" / f"h_{offset}_off.png"
    if not (shot(u_on, a_png) and shot(u_off, b_png)):
        print(f"{offset:>6}  截图失败")
        continue
    A = np.asarray(Image.open(a_png).convert("L"), dtype=np.float32)
    B = np.asarray(Image.open(b_png).convert("L"), dtype=np.float32)
    cols = np.r_[0:110, 890:1000]
    da = np.abs(np.diff(A[:, cols], axis=1)).mean()
    db = np.abs(np.diff(B[:, cols], axis=1)).mean()
    print(f"{offset:>6}{da:>12.3f}{db:>10.3f}{np.abs(A-B).mean():>8.1f}{A.mean():>11.1f}")

