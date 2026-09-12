# -*- coding: utf-8 -*-
"""tools/banner_art.py — 湖面艺术化 banner（真实湖泊图 + 道字 + 雾化水墨）

参考 OJO Design Skills: 真实素材 + 文化符号 + 反 AI 味。
用 front/湖泊.jpg 做 README/首页 hero 背景:
  1. 裁 16:9 / 宽幅
  2. 青蓝-墨色调(湖面金属光泽)
  3. 叠加"道"字(楷体, 水墨相融, 半透明)
  4. 底部渐变雾化(衔接正文)
  5. 提暗 + 增强对比(避免廉价渐变感)
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent.parent
SRC = HERE / "front" / "湖泊.jpg"
ASSETS = HERE / "assets"
FONT = "C:/Windows/Fonts/simkai.ttf"   # 楷体


def art_banner(w=1400, h=640, char="道", out="banner_lake.png", font_size=200):
    im = Image.open(SRC).convert("RGB")
    # 裁到目标比例
    cw, ch = im.size
    tr = w / h
    if cw / ch > tr:
        nw = int(ch * tr); x0 = (cw - nw) // 2
        im = im.crop((x0, 0, x0 + nw, ch))
    else:
        nh = int(cw / tr); y0 = (ch - nh) // 2
        im = im.crop((0, y0, cw, y0 + nh))
    im = im.resize((w, h), Image.LANCZOS)

    # 青蓝-墨色 tone(冷调, 反 AI 味渐变)
    r, g, b = im.split()
    r = r.point(lambda v: int(v * 0.82))
    b = b.point(lambda v: int(v * 1.08))
    im = Image.merge("RGB", (r, g, b))

    # 对比 + 微柔(水面)
    im = ImageEnhance.Contrast(im).enhance(1.06)
    im = im.filter(ImageFilter.GaussianBlur(0.4))

    # 顶部提亮(雾), 底部压暗(衔接正文)
    overlay = Image.new("RGB", (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    for y in range(h):
        a = int(120 * (1 - y / h))      # 上亮
        draw.line([(0, y), (w, y)], fill=(255, 255, 255, a))
        b2 = int(140 * (y / h))          # 下暗
        draw.line([(0, y), (w, y)], fill=(4, 10, 18, b2))
    im = Image.alpha_composite(im.convert("RGBA"), overlay)

    # "道"字: 水墨半透, 居左偏中
    dao = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dao)
    font = ImageFont.truetype(FONT, font_size)
    bbox = dd.textbbox((0, 0), char, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    x = int(w * 0.14 - tw / 2 - bbox[0])
    y = int(h / 2 - th / 2 - bbox[1])
    dd.text((x, y), char, font=font, fill=(255, 255, 255, 200))
    # 墨影(衬底)
    dd.text((x+3, y+3), char, font=font, fill=(0, 0, 0, 90))
    im = Image.alpha_composite(im, dao)

    # 右侧小字: 道生一…
    sub = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sub)
    sf = ImageFont.truetype(FONT, 34)
    txt = "道生一，一生二，二生三，三生万物"
    sb = sd.textbbox((0, 0), txt, font=sf)
    sd.text((w - int(w*0.15) - (sb[2]-sb[0]) - sb[0], y + font_size + 26),
            txt, font=sf, fill=(235, 225, 205, 180))
    im = Image.alpha_composite(im, sub)

    ASSETS.mkdir(parents=True, exist_ok=True)
    im.convert("RGB").save(ASSETS / out, quality=92)
    print(f"saved {ASSETS / out} ({im.size})")


def main():
    art_banner(1400, 640, "道", "banner_lake.png", 230)
    art_banner(900, 420, "道", "banner_lake_small.png", 150)


if __name__ == "__main__":
    main()
