# -*- coding: utf-8 -*-
"""tools/_particle_footprint.py — 决定性实验: 粒子到底覆盖了哪些像素?

把 dotSprite 换成不透明品红, 截图后统计品红像素的分布:
  - 若覆盖形状与 assets/dao_mask.png 相似  → 粒子化道字正确
  - 若覆盖成一个矩形                      → 采样/绘制有 bug（字变成色块）
"""
import re
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent.parent
CHROME = Path(r"C:\Users\16532\AppData\Local\ms-playwright\chromium-1234\chrome-win64\chrome.exe")
if not CHROME.exists():
    CHROME = Path(r"C:\Users\16532\AppData\Local\ms-playwright\chromium-1223\chrome-win64\chrome.exe")

html = (HERE / "docs" / "index.html").read_text(encoding="utf-8")
html = re.sub(r'\s*<link[^>]*fonts\.(googleapis|gstatic)[^>]*>', '', html)

# dotSprite 改成不透明品红方块
pat = re.compile(
    r"const g = c\.createRadialGradient\(13, 13, 0, 13, 13, 13\);.*?c\.fillRect\(0, 0, 26, 26\);",
    re.S)
html2, n = pat.subn("c.fillStyle = 'rgba(255,0,255,1)';\n    c.fillRect(0, 0, 26, 26);", html)
print("dotSprite 已替换:", n, "处")

# 顺便把鼠标高光关掉, 排除干扰
html2 = html2.replace("if(mouseActive){", "if(false){")

p = HERE / "docs" / "_footprint.html"
p.write_text(html2, encoding="utf-8")
out = HERE / "out" / "footprint.png"
out.unlink(missing_ok=True)
subprocess.run([str(CHROME), "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                "--force-device-scale-factor=1", "--window-size=1400,900",
                f"--screenshot={out}", p.as_uri()], timeout=90, capture_output=True)
print("截图:", out.exists())

im = Image.open(out).convert("RGB")
a = np.asarray(im, dtype=np.int16)
mag = (a[..., 0] > 150) & (a[..., 2] > 150) & (a[..., 1] < 110)
print(f"品红像素占比={100*mag.mean():.2f}%  总数={int(mag.sum())}")
ys, xs = np.where(mag)
if len(xs):
    bw, bh = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
    print(f"覆盖率(bounding box 内): {100*mag[ys.min():ys.max()+1, xs.min():xs.max()+1].mean():.1f}%"
          f"  ← 接近 100% 就是实心色块, 越低说明越像笔画")
    print(f"外框 {bw}x{bh} 位置=({xs.min()},{ys.min()})")
    Image.fromarray((mag * 255).astype(np.uint8)).save(HERE / "out" / "footprint_mask.png")

    N = 96
    fm = np.asarray(Image.fromarray((mag * 255).astype(np.uint8))
                    .crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
                    .resize((N, N), Image.LANCZOS), dtype=np.float32) / 255.0
    f = (fm > 0.3).astype(np.float32)
    mask = np.asarray(Image.open(HERE / "assets" / "dao_mask.png").convert("L").resize((N, N),
                                                                                      Image.LANCZOS))
    real = (mask > 90).astype(np.float32)

    def iou(x, y, span=14):
        b = 0.0
        for dy in range(-span, span + 1, 2):
            for dx in range(-span, span + 1, 2):
                r = np.roll(np.roll(y, dy, 0), dx, 1)
                u = float(((x + r) > 0).sum())
                if u:
                    b = max(b, float((x * r).sum()) / u)
        return b

    print(f"粒子覆盖形状 vs 真实墨迹 IoU = {iou(f, real):.3f}")
    print(f"粒子覆盖形状 vs 镜像墨迹 IoU = {iou(f, np.fliplr(real)):.3f}")
    sm = np.asarray(Image.fromarray((mag * 255).astype(np.uint8))
                    .crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
                    .resize((58, 30), Image.LANCZOS), dtype=np.float32) / 255.0
    ramp = "@%#*+=-:. "      # 索引 0 = 墨最多
    print("=== 粒子覆盖形状 (@ = 粒子, 空白 = 无粒子) ===")
    for r in range(30):
        print("".join(ramp[max(0, 9 - int(sm[r, c] * 9.99))] for c in range(58)))
