# -*- coding: utf-8 -*-
"""tools/art_logo.py — 极简 logo: 书法「道」去纸纹、纯墨色（v0.5）

用户: logo 要更简约、极简风。
做法: 取书法原图 -> 二值化提墨 -> 去纸纹 -> 纯墨色 on 透明/白底 -> 细边圆角。
不加印章、不加光晕、不加暖调。
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageOps

HERE = Path(__file__).resolve().parent.parent
SRC = HERE / "assets" / "dao_original.png"  # 书法原图(已归档)
ASSETS = HERE / "assets"
INK = (17, 17, 17)
WHITE = (255, 255, 255)


def _drop_specks(bw, min_area):
    """去掉小于 min_area 的孤立斑点(纸纹噪点), 保留笔画。"""
    w, h = bw.size
    px = bw.load()
    seen = [[False] * w for _ in range(h)]
    out = Image.new("L", (w, h), 255)
    opx = out.load()
    for sy in range(h):
        for sx in range(w):
            if seen[sy][sx] or px[sx, sy] != 0:
                continue
            # flood fill 该连通块
            stack, comp = [(sx, sy)], []
            seen[sy][sx] = True
            while stack:
                x, y = stack.pop()
                comp.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] \
                            and px[nx, ny] == 0:
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            if len(comp) >= min_area:
                for x, y in comp:
                    opx[x, y] = 0
    return out


def extract_ink(min_speck=26):
    """把书法原图提成纯墨色笔画（去纸纹 + 去斑点）。"""
    im = Image.open(SRC).convert("L")
    w, h = im.size
    m = int(min(w, h) * 0.045)
    im = im.crop((m, m, w - m, h - m))
    im = ImageOps.autocontrast(im, cutoff=1)
    im = im.filter(ImageFilter.MedianFilter(3))
    bw = im.point(lambda p: 0 if p < 118 else 255).convert("L")
    bw = _drop_specks(bw, min_speck)          # 去小斑
    bw = bw.filter(ImageFilter.MedianFilter(3))
    alpha = ImageOps.invert(bw)
    return bw, alpha


def make(size, bg=None, pad_ratio=0.12, radius_ratio=0.10, name="logo.png"):
    bw, alpha = extract_ink()
    w, h = bw.size
    inner = int(size * (1 - pad_ratio * 2))
    s = min(inner / w, inner / h)
    nw, nh = max(1, int(w * s)), max(1, int(h * s))
    a = alpha.resize((nw, nh), Image.LANCZOS)

    base = Image.new("RGBA", (size, size), (bg + (255,)) if bg else (0, 0, 0, 0))
    if bg:
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            [0, 0, size - 1, size - 1], radius=int(size * radius_ratio), fill=255)
        base.putalpha(mask)

    ink = Image.new("RGBA", (nw, nh), INK + (255,))
    ink.putalpha(a)
    base.alpha_composite(ink, ((size - nw) // 2, (size - nh) // 2))
    base.save(ASSETS / name)
    print(f"{name} {base.size}")


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    # 主 logo: 透明底(README 深浅主题都能用)
    make(512, bg=None, name="logo.png")
    # 白底圆角版(社交/avatar)
    make(512, bg=WHITE, radius_ratio=0.11, name="logo_white.png")
    make(256, bg=None, pad_ratio=0.10, name="logo_small.png")
    # 小图标(纯墨, 无留白, 用于 favicon)
    bw, alpha = extract_ink()
    s = 128
    a = alpha.resize((s, s), Image.LANCZOS)
    ic = Image.new("RGBA", (s, s), INK + (255,))
    ic.putalpha(a)
    ic.save(ASSETS / "favicon.png")
    print("favicon.png", ic.size)


if __name__ == "__main__":
    main()
