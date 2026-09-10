# -*- coding: utf-8 -*-
"""tools/verify_screenshot.py — 数值化验证首页渲染结果（不依赖视觉模型）。

输出:
  1. 画面统计（是否空白 / 是否有真实照片纹理）
  2. 粗粒度亮度 ASCII 图（可判断 hero 布局与"道"字是否出现）
  3. 与 assets/dao_mask.png 的形状相关度（确认道字确实由真实墨迹渲染出来）
"""
import sys
import numpy as np
from pathlib import Path
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent.parent


def ascii_lum(a, cols=64, rows=30, label=""):
    h, w = a.shape
    small = np.asarray(Image.fromarray(a.astype(np.uint8)).resize((cols, rows * 2), Image.LANCZOS),
                       dtype=np.float32)
    ramp = "@%#*+=-:. "
    print(f"--- {label} ({w}x{h}) mean={a.mean():.1f} std={a.std():.1f} ---")
    for r in range(rows):
        print("".join(ramp[min(9, int(small[r * 2:r * 2 + 2, c].mean() / 255 * 10))]
                      for c in range(cols)))
    print()


def main(path):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im)
    lum = a.mean(axis=2)
    print(f"# {path}: {im.size}, 颜色数={len(np.unique(a.reshape(-1,3), axis=0))}, "
          f"亮度 mean={lum.mean():.1f} std={lum.std():.1f}")
    # 空白检测: 单一颜色 / 极低方差
    if lum.std() < 3:
        print("!! 疑似空白画面")
    # 真实照片纹理检测: 高频能量（拉普拉斯）
    lap = np.asarray(Image.fromarray(lum.astype(np.uint8)).filter(
        ImageFilter.FIND_EDGES), dtype=np.float32)
    print(f"边缘能量={lap.mean():.1f} (真实照片通常 > 5, 纯色渐变 < 1)")

    hero_h = int(im.height * 0.62)
    ascii_lum(lum[:hero_h], 64, 26, "首屏 (hero)")

    # 道字: hero 区域内的暗粒子块
    hero = lum[:hero_h]
    thr = np.percentile(hero, 6)
    ink = (hero <= thr).astype(np.float32)
    ys, xs = np.where(ink > 0)
    if len(xs):
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        bw, bh = x1 - x0 + 1, y1 - y0 + 1
        print(f"hero 暗区(<P6={thr:.0f}) 占比={100*ink.mean():.1f}% 外框={bw}x{bh} "
              f"位置=({x0},{y0}) 中心=({(x0+x1)//2},{(y0+y1)//2}) 画面中心=({im.width//2},{hero_h//2})")
        cx0, cx1 = max(0, im.width // 2 - 260), min(im.width, im.width // 2 + 260)
        cy0, cy1 = max(0, hero_h // 2 - 300), min(hero_h, hero_h // 2 + 300)
        blob = ink[cy0:cy1, cx0:cx1]
        print(f"中心窗口内暗区占比={100*blob.mean():.1f}%  (道字若成粒子化渲染, 应在 8-35%)")

    # 与真实墨迹掩膜的形状对比（都二值化到 64x64, 允许平移）
    mask = np.asarray(Image.open(HERE / "assets" / "dao_mask.png").convert("L")
                      .resize((64, 64), Image.LANCZOS), dtype=np.float32) / 255.0
    m = (mask > 0.35).astype(np.float32)
    hero_small = np.asarray(Image.fromarray(hero.astype(np.uint8)).resize((64, 64), Image.LANCZOS),
                            dtype=np.float32)
    hs = (hero_small <= np.percentile(hero_small, 12)).astype(np.float32)
    best, arg = 0.0, None
    for dy in range(-10, 11, 2):
        for dx in range(-10, 11, 2):
            r = np.roll(np.roll(hs, dy, 0), dx, 1)
            u = float(((m + r) > 0).sum())
            if not u:
                continue
            v = float((m * r).sum()) / u
            if v > best:
                best, arg = v, (dy, dx)
    print(f"与真实 dao_mask 的最优 IoU={best:.3f} (平移 {arg}); >0.2 说明首屏确实出现该字形轮廓")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(HERE / "out" / "verify_hero.png"))
