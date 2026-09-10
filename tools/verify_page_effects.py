# -*- coding: utf-8 -*-
"""收尾验证（轻量）：水面物理判定 + 截图级粒子/涟漪 + 整页背景统一。

截图级验证才是"鼠标动起来真的有效果"的证据：先注入墨点/水花，再截图数像素。
"""
import json
import re
import subprocess
import sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CHROME = Path(r"C:\Users\16532\AppData\Local\ms-playwright\chromium-1234\chrome-win64\chrome.exe")
if not CHROME.exists():
    CHROME = Path(r"C:\Users\16532\AppData\Local\ms-playwright\chromium-1223\chrome-win64\chrome.exe")
BASE = "http://127.0.0.1:8123/docs/"
STYLE = ("<style id='v'>.hero{height:900px !important;min-height:900px !important;}"
         ".card,.path-card,.doc,.figure,.label,.g-line,.g-divider,.q-item,#heroLine"
         "{opacity:1 !important;transform:none !important;}")
FLAGS = ["--headless=new", "--disable-gpu", "--no-sandbox", "--enable-unsafe-swiftshader",
         "--use-gl=angle", "--use-angle=swiftshader", "--hide-scrollbars",
         "--force-device-scale-factor=1"]


def build(name, extra="", css=""):
    html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    html = re.sub(r'\s*<link[^>]*fonts\.(googleapis|gstatic)[^>]*>', '', html)
    if css:
        html = html.replace("</head>", css + "</style></head>", 1)
    if extra:
        html = html.replace("</body>", extra, 1)
    (ROOT / "docs" / name).write_text(html, encoding="utf-8")
    return BASE + name


def shot(url, out, w=1000, h=760, timeout=100):
    out.unlink(missing_ok=True)
    p = subprocess.Popen([str(CHROME)] + FLAGS + [f"--window-size={w},{h}",
                                                  f"--screenshot={out}", url],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        p.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill(); return False
    return out.exists()


WHICH = sys.argv[1] if len(sys.argv) > 1 else "all"

# ── A. 截图级：墨点粒子（鼠标到哪儿哪儿有） ─────────────────────────────
if WHICH in ("all", "ink"):
    INK = r"""
<script>
(function(){
  function wait(ms){ return new Promise(function(r){ setTimeout(r,ms); }); }
  addEventListener('load', async function(){
    for(var i=0;i<60 && !window.__ink; i++) await wait(100);
    await wait(600);
    // 沿一条曲线注入墨点（等价于鼠标划过）
    if(window.__ink){
      for(var k=0;k<40;k++){
        var x = 160 + k*16, y = 300 + Math.sin(k/5)*70;
        window.__ink.spawn(x, y, 3);
      }
    }
  });
})();
</script>
</body>"""
    ok1 = shot(build("_v_ink.html", INK), ROOT / "out" / "ink_on.png")
    ok2 = shot(build("_v_ink_off.html", "", STYLE.replace("<style id='v'>",
                 "<style id='v'>#inkLayer{display:none !important;}")), ROOT / "out" / "ink_off.png")
    print("=== A. 墨点粒子（截图级）===", "截图:", ok1, ok2)
    if ok1 and ok2:
        A = np.asarray(Image.open(ROOT / "out" / "ink_on.png").convert("L"), dtype=np.float32)
        B = np.asarray(Image.open(ROOT / "out" / "ink_off.png").convert("L"), dtype=np.float32)
        d = B - A                                    # 打开的版本更暗（有墨点）
        strong = (d > 25).sum()
        print(f"  墨点像素(比无墨点层暗>25): {strong}   差>6 的像素: {(d>6).sum()}   平均差={d.mean():.2f}")
        ys, xs = np.where(d > 25)
        if len(xs):
            print(f"  墨点分布外框: x {xs.min()}..{xs.max()}  y {ys.min()}..{ys.max()} "
                  f"(注入路径 x 160..784, y 230..370)")

# ── B. 截图级：水花涟漪（注入后画面出现环形高光） ──────────────────────
if WHICH in ("all", "ripple"):
    RIP = r"""
<script>
(function(){
  function wait(ms){ return new Promise(function(r){ setTimeout(r,ms); }); }
  addEventListener('load', async function(){
    for(var i=0;i<60 && !window.__water; i++) await wait(100);
    await wait(500);
    if(window.__water){
      window.__water.drop(0.5, 0.45, 0.55, 0.05);
      for(var k=0;k<8;k++) window.__water.drop(0.5, 0.45, 0.30, 0.045);
    }
  });
})();
</script>
</body>"""
    ok1 = shot(build("_v_rip.html", RIP), ROOT / "out" / "rip_on.png")
    ok2 = shot(build("_v_rip_off.html", "", STYLE.replace("<style id='v'>",
                 "<style id='v'>#lakeGL{display:none !important;}")), ROOT / "out" / "rip_off.png")
    print("\n=== B. 涟漪（截图级）===", "截图:", ok1, ok2)
    if ok1 and ok2:
        A = np.asarray(Image.open(ROOT / "out" / "rip_on.png").convert("L"), dtype=np.float32)
        B = np.asarray(Image.open(ROOT / "out" / "rip_off.png").convert("L"), dtype=np.float32)
        print(f"  水面版均值={A.mean():.1f} 无水面版均值={B.mean():.1f} 差异={np.abs(A-B).mean():.1f}")
        hero = A[:int(A.shape[0] * 0.75)]
        print(f"  首屏局部细节(横向梯度均值)={np.abs(np.diff(hero, axis=1)).mean():.3f} "
              f"最亮像素占比(波峰高光)={100*(hero>np.percentile(hero,99.5)).mean():.2f}%")

# ── C. 整页背景统一（2 段足够说明问题） ────────────────────────────────
if WHICH in ("all", "bg"):
    print("\n=== C. 整页背景统一（逐段）===")
    print(f"{'位移':>6}{'水面版细节':>12}{'无水面':>9}{'差异':>8}{'均值':>8}")
    for offset in (0, 3000):
        css_on = STYLE + (f"section{{margin-top:-{offset}px;}}" if offset else "")
        css_off = css_on.replace("<style id='v'>", "<style id='v'>#lakeGL{display:none !important;}")
        u_on, u_off = build(f"_v_bg_on_{offset}.html", "", css_on), build(f"_v_bg_off_{offset}.html", "", css_off)
        a_png, b_png = ROOT / "out" / f"bg_{offset}_on.png", ROOT / "out" / f"bg_{offset}_off.png"
        if not (shot(u_on, a_png, 1000, 1400) and shot(u_off, b_png, 1000, 1400)):
            print(f"{offset:>6}  截图失败"); continue
        A = np.asarray(Image.open(a_png).convert("L"), dtype=np.float32)
        B = np.asarray(Image.open(b_png).convert("L"), dtype=np.float32)
        cols = np.r_[0:110, 890:1000]
        print(f"{offset:>6}{np.abs(np.diff(A[:, cols], axis=1)).mean():>12.3f}"
              f"{np.abs(np.diff(B[:, cols], axis=1)).mean():>9.3f}"
              f"{np.abs(A - B).mean():>8.1f}{A.mean():>8.1f}")
