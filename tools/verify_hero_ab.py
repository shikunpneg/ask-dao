# -*- coding: utf-8 -*-
"""tools/_ab_ink.py — A/B 渲染: 切出"墨迹层", 客观验证首屏的『道』确实是真实书法。

做法: 生成两份页面副本（仅粒子采样条件不同），headless 截图后相减，
      差值图 = 墨迹粒子层；再与 assets/dao_mask.png 比形状。
"""
import re
import subprocess
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent.parent
CHROME = Path(r"C:\Users\16532\AppData\Local\ms-playwright\chromium-1234\chrome-win64\chrome.exe")
if not CHROME.exists():
    CHROME = Path(r"C:\Users\16532\AppData\Local\ms-playwright\chromium-1223\chrome-win64\chrome.exe")


def strip_fonts(html):
    return re.sub(r'\s*<link[^>]*fonts\.(googleapis|gstatic)[^>]*>', '', html)


def shot(path, out, w=1400, h=900):
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)
    subprocess.run([str(CHROME), "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--hide-scrollbars", "--force-device-scale-factor=1",
                    f"--window-size={w},{h}", f"--screenshot={out}", path.as_uri()],
                   timeout=90, capture_output=True)
    return out.exists()


def binz(a, pct):
    return (a <= np.percentile(a, pct)).astype(np.float32)


def best_iou(a, b, span=18):
    best = 0.0
    for dy in range(-span, span + 1, 2):
        for dx in range(-span, span + 1, 2):
            r = np.roll(np.roll(b, dy, 0), dx, 1)
            u = float(((a + r) > 0).sum())
            if u:
                best = max(best, float((a * r).sum()) / u)
    return best


src = (HERE / "docs" / "index.html").read_text(encoding="utf-8")
base = strip_fonts(src)

# 变体 1: 原样   变体 2: 关掉粒子采样（墨迹层）
(HERE / "docs" / "_ab_ink.html").write_text(base, encoding="utf-8")
patched, n = re.subn(r'if\(a > 60\)\{', 'if(false){', base)
if n == 0:
    patched, n = re.subn(r'if\s*\(\s*a\s*>\s*60\s*\)', 'if(false)', base)
print(f"粒子采样分支被关掉 {n} 处")
(HERE / "docs" / "_ab_noink.html").write_text(patched, encoding="utf-8")

ok1 = shot(HERE / "docs" / "_ab_ink.html", HERE / "out" / "ab_ink.png")
ok2 = shot(HERE / "docs" / "_ab_noink.html", HERE / "out" / "ab_noink.png")
print("截图:", "墨迹版" if ok1 else "墨迹版失败", "/", "无墨迹版" if ok2 else "无墨迹版失败")
if not (ok1 and ok2):
    sys.exit(1)

A = np.asarray(Image.open(HERE / "out" / "ab_ink.png").convert("L"), dtype=np.float32)
B = np.asarray(Image.open(HERE / "out" / "ab_noink.png").convert("L"), dtype=np.float32)
heroH = int(A.shape[0] * 0.62)
diff = np.clip(B[:heroH] - A[:heroH], 0, 255)      # 无墨迹更亮 → 差值即墨迹
print(f"差值图: 最大 {diff.max():.0f}, >12 的像素占 {100*(diff>12).mean():.2f}%")
Image.fromarray((255 - np.clip(diff * 6, 0, 255)).astype(np.uint8)).save(HERE / "out" / "ab_ink_layer.png")

ys, xs = np.where(diff > 12)
if len(xs):
    print(f"墨迹层外框: x {xs.min()}..{xs.max()} ({xs.max()-xs.min()+1}px), "
          f"y {ys.min()}..{ys.max()} ({ys.max()-ys.min()+1}px), 画面 {A.shape[1]}x{heroH}")

N = 96
ink_layer = np.asarray(Image.fromarray(diff.astype(np.uint8)).resize((N, N), Image.LANCZOS),
                       dtype=np.float32)
lay = (ink_layer > np.percentile(ink_layer, 88)).astype(np.float32)
mask = np.asarray(Image.open(HERE / "assets" / "dao_mask.png").convert("L").resize((N, N),
                                                                                  Image.LANCZOS))
real = (mask > 90).astype(np.float32)

from PIL import ImageDraw, ImageFont
ref = Image.new("L", (512, 512), 0)
ImageDraw.Draw(ref).text((256, 256), "道", font=ImageFont.truetype("C:/Windows/Fonts/simkai.ttf", 430),
                         fill=255, anchor="mm")
kai = (np.asarray(ref.convert("L").resize((N, N), Image.LANCZOS), dtype=np.float32) > 90).astype(np.float32)

circ = Image.new("L", (N, N), 0)
ImageDraw.Draw(circ).ellipse((6, 6, N - 6, N - 6), fill=255)
circle = (np.asarray(circ) > 90).astype(np.float32)

print()
print(f"{'墨迹层 vs':<32}{'IoU':>8}")
res = {
    "真实墨迹 dao_mask": best_iou(lay, real),
    "楷体『道』参照": best_iou(lay, kai),
    "真实墨迹镜像(方向对照)": best_iou(lay, np.fliplr(real)),
    "实心圆斑(阴性对照)": best_iou(lay, circle),
}
for k, v in res.items():
    print(f"{k:<32}{v:>8.3f}")
print()
good = res["真实墨迹 dao_mask"]
neg = res["实心圆斑(阴性对照)"]
flip = res["真实墨迹镜像(方向对照)"]
verdict = ("通过: 首屏墨迹层与真实书法『道』高度相似, 且优于镜像与阴性对照"
           if good > max(neg, flip) + 0.05 and good > 0.25
           else "未通过: 墨迹层形状与真实书法不够相似, 需要人工看图判断")
print("结论:", verdict)
