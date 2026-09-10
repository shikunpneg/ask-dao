# -*- coding: utf-8 -*-
"""tools/art_logo.py — 对书法原图(道.png)做艺术化处理，生成 logo（R91）

输入: 道.png (书法原图, 369x420)
输出: assets/logo.png (主 logo, 方形) / logo_small.png / logo_banner.png (横幅)

处理:
  1. 裁掉多余边距，居中
  2. 宣纸底色统一(去原图杂色边缘)
  3. 提高墨色对比(让笔画更黑更清晰)
  4. 轻微暖调光晕(岁月感)
  5. 加朱红「问」印章
  6. 圆角
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

HERE = Path(__file__).resolve().parent.parent
SRC = HERE / "道.png"
ASSETS = HERE / "assets"
PAPER = (240, 229, 204)


def load_ink():
    im = Image.open(SRC).convert("RGB")
    w, h = im.size
    # 裁边(4%)去掉扫描杂边
    m = int(min(w, h) * 0.03)
    im = im.crop((m, m, w - m, h - m))
    # 提对比 + 降饱和(让墨更黑、纸更净)
    im = ImageEnhance.Contrast(im).enhance(1.35)
    im = ImageEnhance.Color(im).enhance(0.85)
    im = ImageEnhance.Brightness(im).enhance(1.06)
    return im


def square(im, side, pad_ratio=0.10):
    """居中放入方形宣纸底, 留边。"""
    canvas = Image.new("RGB", (side, side), PAPER)
    inner = int(side * (1 - pad_ratio * 2))
    w, h = im.size
    s = min(inner / w, inner / h)
    im2 = im.resize((max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)
    canvas.paste(im2, ((side - im2.width) // 2, (side - im2.height) // 2))
    return canvas


def warm_glow(im):
    """淡淡的暖调光晕(岁月感)。"""
    glow = im.filter(ImageFilter.GaussianBlur(18))
    glow = ImageEnhance.Brightness(glow).enhance(1.04)
    return Image.blend(im, glow, 0.18)


def add_seal(im, text="问道", size_ratio=0.16, margin_ratio=0.055):
    """右下角朱红印章(竖排两字)。"""
    w = im.width
    ss = int(w * size_ratio)
    margin = int(w * margin_ratio)
    seal = Image.new("RGBA", (ss, ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(seal)
    d.rounded_rectangle([0, 0, ss - 1, ss - 1], radius=int(ss * 0.12),
                        fill=(176, 42, 36, 235))
    try:
        f = ImageFont.truetype("C:/Windows/Fonts/STXINGKA.TTF", int(ss * 0.40))
    except Exception:
        f = ImageFont.load_default()
    for i, ch in enumerate(text):
        b = d.textbbox((0, 0), ch, font=f)
        tw, th = b[2] - b[0], b[3] - b[1]
        cy = ss * (0.28 + i * 0.44)
        d.text(((ss - tw) / 2 - b[0], cy - th / 2 - b[1]), ch, font=f,
               fill=(255, 240, 232, 250))
    im = im.convert("RGBA")
    im.alpha_composite(seal, (w - ss - margin, im.height - ss - margin))
    return im.convert("RGB")


def rounded(im, r_ratio=0.07):
    w, h = im.size
    r = int(min(w, h) * r_ratio)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255)
    out = Image.new("RGB", (w, h), PAPER)
    out.paste(im, (0, 0), mask)
    return out


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    ink = load_ink()

    # 主 logo: 640 方形 + 印章 + 圆角
    logo = square(ink, 640, pad_ratio=0.09)
    logo = warm_glow(logo)
    logo = add_seal(logo, "问道")
    logo = rounded(logo, 0.075)
    logo.save(ASSETS / "logo.png")
    print("logo.png", logo.size)

    # 小图(网页/avatar): 无印章, 净版
    small = square(ink, 240, pad_ratio=0.07)
    small = rounded(small, 0.09)
    small.save(ASSETS / "logo_small.png")
    print("logo_small.png", small.size)

    # 横幅(README 顶部): 左道右字
    bw, bh = 1100, 300
    banner = Image.new("RGB", (bw, bh), PAPER)
    b_ink = square(ink, bh - 40, pad_ratio=0.05)
    banner.paste(b_ink, (60, 20))
    d = ImageDraw.Draw(banner)
    try:
        f1 = ImageFont.truetype("C:/Windows/Fonts/STXINGKA.TTF", 74)
        f2 = ImageFont.truetype("C:/Windows/Fonts/STXINGKA.TTF", 30)
    except Exception:
        f1 = f2 = ImageFont.load_default()
    d.text((bh + 40, 78), "问道", font=f1, fill=(28, 22, 18))
    d.text((bh + 48, 186), "道生一，一生二，二生三，三生万物", font=f2, fill=(122, 96, 62))
    banner.save(ASSETS / "logo_banner.png")
    print("logo_banner.png", banner.size)


if __name__ == "__main__":
    main()
