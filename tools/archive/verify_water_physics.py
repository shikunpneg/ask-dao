# -*- coding: utf-8 -*-
"""水面自检 v2：径向剖面度量（波前位置 = 环带平均幅度最大的半径），并检查叠加干涉。

注入自检脚本 → headless Chrome --dump-dom 取回结果。不依赖视觉模型。
"""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHROME = Path(r"C:\Users\16532\AppData\Local\ms-playwright\chromium-1234\chrome-win64\chrome.exe")
if not CHROME.exists():
    CHROME = Path(r"C:\Users\16532\AppData\Local\ms-playwright\chromium-1223\chrome-win64\chrome.exe")

SELFTEST = r"""
<script>
(function(){
  function report(obj){
    var d = document.createElement('div'); d.id = 'selftest';
    d.textContent = JSON.stringify(obj); document.body.appendChild(d);
  }
  function wait(ms){ return new Promise(function(r){ setTimeout(r, ms); }); }

  async function run(){
    for(var i=0;i<80 && !(window.__water && window.__lakeReady); i++) await wait(100);
    if(!window.__water){ report({ok:false, why:'no-webgl'}); return; }
    var W = window.__water;
    function settle(n){ for(var i=0;i<n;i++) W.step(1,true); }
    function stepQ(n){ for(var i=0;i<n;i++) W.step(1,true); }
    function field(){ return W.readHeight(); }

    // 视觉相关的是"相邻格高度差"（决定法线/高光），而不是峰值本身
    function maxGrad(f){
      var g = 0;
      for(var y=0;y<f.h;y++) for(var x=1;x<f.w;x++){
        var d = Math.abs(f.data[y*f.w+x] - f.data[y*f.w+x-1]); if(d>g) g=d;
      }
      for(var y2=1;y2<f.h;y2++) for(var x2=0;x2<f.w;x2++){
        var d2 = Math.abs(f.data[y2*f.w+x2] - f.data[(y2-1)*f.w+x2]); if(d2>g) g=d2;
      }
      return +g.toFixed(5);
    }
    function peakOf(f){
      var p=0; for(var i=0;i<f.data.length;i++){ var a=Math.abs(f.data[i]); if(a>p)p=a; }
      return p;
    }
    // 径向剖面：每 6 个格一个环带，返回 [{r, m}]
    function radial(f){
      var cx=(f.w-1)/2, cy=(f.h-1)/2, B=6, nb=Math.ceil(Math.max(f.w,f.h)/2/B)+1;
      var sum=new Float64Array(nb), cnt=new Float64Array(nb);
      for(var y=0;y<f.h;y++) for(var x=0;x<f.w;x++){
        var d=Math.hypot(x-cx,y-cy), b=Math.floor(d/B);
        if(b<nb){ sum[b]+=Math.abs(f.data[y*f.w+x]); cnt[b]++; }
      }
      var out=[]; for(var i=1;i<nb;i++){ if(cnt[i]) out.push({r:i*B, m:+(sum[i]/cnt[i]).toFixed(5)}); }
      return out;
    }
    function frontR(prof){
      var best=0,br=0;
      for(var i=0;i<prof.length;i++) if(prof[i].m>best){ best=prof[i].m; br=prof[i].r; }
      return {r:br, m:best};
    }
    function bandMean(f, x0, x1, y0, y1){
      var s=0,c=0;
      for(var y=Math.floor(f.h*y0);y<Math.floor(f.h*y1);y++)
        for(var x=Math.floor(f.w*x0);x<Math.floor(f.w*x1);x++){
          if(y<0||y>=f.h||x<0||x>=f.w) continue; s+=Math.abs(f.data[y*f.w+x]); c++;
        }
      return c? +(s/c).toFixed(5):0;
    }

    // 1) 静水（静默步进，不含环境水花）
    settle(1200);
    var f0 = field();
    var flat = { peak:+peakOf(f0).toFixed(4), maxGrad:maxGrad(f0) };

    // 2) 单点水花 → 波前随时间外扩（用径向剖面测）
    W.drop(0.5, 0.5, 0.24, 0.040);
    var trace=[], acc=0;
    [40, 80, 140, 220, 320, 420].forEach(function(k){
      stepQ(k-acc); acc=k;
      var f=field(), prof=radial(f), fr=frontR(prof);
      trace.push({k:k, frontR:fr.r, frontM:fr.m, peak:+peakOf(f).toFixed(4)});
    });

    // 3) 叠加干涉：等波前跑到中点再比较
    settle(1600);
    W.drop(0.36,0.5,0.24,0.040);
    stepQ(150);
    var one = { mid: bandMean(field(), 0.45,0.55, 0.42,0.58), peak:+peakOf(field()).toFixed(4) };
    settle(1600);
    W.drop(0.36,0.5,0.24,0.040); W.drop(0.64,0.5,0.24,0.040);
    stepQ(150);
    var two = { mid: bandMean(field(), 0.45,0.55, 0.42,0.58), peak:+peakOf(field()).toFixed(4) };

    report({
      ok:true, sim:W.size(), flat:flat, trace:trace, one:one, two:two,
      verdict:{
        flat_ok: flat.maxGrad < 0.005,   // 视觉上已是静水
        front_expands: trace[trace.length-1].frontR > trace[0].frontR + 18,
        flat_detail: 'maxGrad=' + flat.maxGrad,
        decays: trace[trace.length-1].frontM < trace[0].frontM,
        interference: two.mid > one.mid * 1.2
      }
    });
  }
  addEventListener('load', function(){ run(); });
})();
</script>
</body>"""


def build():
    html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    html = re.sub(r'\s*<link[^>]*fonts\.(googleapis|gstatic)[^>]*>', '', html)
    html = html.replace("</body>", SELFTEST, 1)
    p = ROOT / "docs" / "_selftest.html"
    p.write_text(html, encoding="utf-8")
    return p


p = build()
r = subprocess.run([str(CHROME), "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--enable-unsafe-swiftshader", "--use-gl=angle", "--use-angle=swiftshader",
                    "--virtual-time-budget=30000", "--dump-dom", p.as_uri()],
                   capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
m = re.search(r'<div id="selftest">(.*?)</div>', r.stdout or "", re.S)
if not m:
    print("未取回结果，DOM 长度:", len(r.stdout or ""))
    raise SystemExit(1)
d = json.loads(m.group(1))
print(json.dumps(d, ensure_ascii=False, indent=1))
if d.get("ok"):
    print("\n=== 判定 ===")
    for k, v in d["verdict"].items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
