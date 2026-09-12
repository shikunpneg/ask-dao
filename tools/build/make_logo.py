# -*- coding: utf-8 -*-
"""tools/make_logo.py — 生成项目 logo:「道」(行书) on 宣纸

用户: 初始形象是书法的「道」。
用系统中文字体(华文行楷 STXINGKA)渲染, 加宣纸纹理。
输出 assets/logo.png (640x640) 与 assets/logo_small.png (200x200)。
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent.parent
ASSETS = HERE / "assets"
FONT = "C:/Windows/Fonts/STXINGKA.TTF"   # 华文行楷
W = 640


def paper_bg(w, seed=7):
    """宣纸底色 + 细噪点纹理。"""
    rnd = random.Random(seed)
    img = Image.new("RGB", (w, w), (238, 227, 200))
    px = img.load()
    for y in range(w):
        for x in range(w):
            n = rnd.randint(-10, 10)
            r, g, b = px[x, y]
            px[x, y] = (max(0, min(255, r + n)),
                        max(0, min(255, g + n)),
                        max(0, min(255, b + n)))
    return img


def make_logo(w=W, font_size=470, char="道", out="logo.png"):
    img = paper_bg(w)
    font = ImageFont.truetype(FONT, font_size)
    d = ImageDraw.Draw(img)
    bbox = d.textbbox((0, 0), char, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((w - tw) / 2 - bbox[0], (w - th) / 2 - bbox[1]),
           char, font=font, fill=(22, 18, 16))
    # 淡红印章(右下): 小方块 + 问
    seal = Image.new("RGB", (86, 86), (238, 227, 200))
    sd = ImageDraw.Draw(seal)
    sf = ImageFont.truetype(FONT, 60)
    sb = sd.textbbox((0, 0), "问", font=sf)
    sd.text(((86 - (sb[2] - sb[0])) / 2 - sb[0], (86 - (sb[3] - sb[1])) / 2 - sb[1]),
            "问", font=sf, fill=(178, 44, 38))
    img.paste(seal, (w - 110, w - 110))
    ASSETS.mkdir(parents=True, exist_ok=True)
    img.save(ASSETS / out)
    print(f"saved {ASSETS / out} ({img.size})")


def main():
    make_logo(W, 470, "道", "logo.png")
    make_logo(200, 150, "道", "logo_small.png")


if __name__ == "__main__":
    main()
