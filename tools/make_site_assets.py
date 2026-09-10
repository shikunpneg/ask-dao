# -*- coding: utf-8 -*-
"""tools/make_site_assets.py — 站点素材生成器（全部来自真实素材，不用字体冒充书法）

素材来源:
  front/道.png      真实书法"道"字（实为 JPEG, 369x420）
  front/树.png      树（实为 WEBP, 513x401）
  front/湖泊.jpg    真实湖面照片（1024x683）
  front/银白色水麦.jpg 银白金属质感（800x533）

产出（assets/ 与 docs/assets/ 双份）:
  dao_mask.png    墨迹掩膜: L 通道 = 墨的浓度, 用于 WebGL 涟漪里的"水墨相融"
  dao_ink.png     白墨 + 透明底: WebGL 不可用时的降级图 / 极简 logo 底图
  lake.jpg        冷调金属湖面（真实照片裁切 + 色调 + 对比）
  favicon.png     从真实书法派生的极简 favicon
  logo.png        极简 logo: 墨色书法（深底用）
  logo_white.png  极简 logo: 银色书法（浅底/README 用）
  logo_small.png  小尺寸 logo
  dao_original.png 原始书法归档

用法: python tools/make_site_assets.py
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageEnhance

HERE = Path(__file__).resolve().parent.parent
FRONT = HERE / "front"
ASSETS = HERE / "assets"
DOCS_ASSETS = HERE / "docs" / "assets"


# ────────────────────────────── 工具 ──────────────────────────────
def ascii_preview(arr, cols=46, label=""):
    """把掩膜按行降采样成 ASCII，用字符密度代替看图。"""
    h, w = arr.shape
    rows = max(6, int(cols * h / w * 0.5))
    ys = np.linspace(0, h, rows + 1).astype(int)
    xs = np.linspace(0, w, cols + 1).astype(int)
    ramp = " .:-=+*#%@"
    lines = []
    for i in range(rows):
        line = ""
        for j in range(cols):
            blk = arr[ys[i]:ys[i + 1], xs[j]:xs[j + 1]]
            v = float(blk.mean()) if blk.size else 0.0
            line += ramp[min(len(ramp) - 1, int(v * len(ramp)))]
        lines.append(line)
    print(f"--- {label} ({w}x{h}) ---")
    print("\n".join(lines))
    print()


def _otsu(a):
    hist, _ = np.histogram(a, bins=256, range=(0, 256))
    tot = a.size
    sum_all = float(np.dot(np.arange(256), hist))
    sum_b, w_b, best, thr = 0.0, 0, 0.0, 128
    for t in range(256):
        w_b += hist[t]
        if w_b == 0:
            continue
        w_f = tot - w_b
        if w_f == 0:
            break
        sum_b += t * hist[t]
        m_b, m_f = sum_b / w_b, (sum_all - sum_b) / w_f
        var = w_b * w_f * (m_b - m_f) ** 2
        if var > best:
            best, thr = var, t
    return thr


def _components(mask):
    """8-邻域连通域标注, 返回 (label 图, 面积列表)。"""
    h, w = mask.shape
    lab = np.zeros((h, w), dtype=np.int32)
    cur = 0
    sizes = {}
    for y0 in range(h):
        for x0 in range(w):
            if not mask[y0, x0] or lab[y0, x0]:
                continue
            cur += 1
            stack, size = [(y0, x0)], 0
            lab[y0, x0] = cur
            while stack:
                y, x = stack.pop()
                size += 1
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not lab[ny, nx]:
                            lab[ny, nx] = cur
                            stack.append((ny, nx))
            sizes[cur] = size
    return lab, sizes


def ink_mask_from_photo(path, blur=1.8, thresh_gain=1.12, min_frac=0.004, smooth=0.7):
    """极简处理: 从真实书法照片里抠出**干净的墨迹**, 不留纸底灰阶与纸纹噪点。

    源图是干笔书法（纸底亮 ~180，笔画淡且有飞白），直接局部对比度会抠过头成糊块。
    步骤（都是"极简"取向: 只做必要处理, 不描摹不改字形）:
      1. 高斯模糊去纸纹
      2. 1/99 分位对比拉伸（把淡墨拉开）
      3. Otsu 阈值 × 小幅增益（保住飞白又不过度膨胀）
      4. 连通域去碎点（小于总墨面积 min_frac 的噪点丢掉）
      5. 闭运算补飞白 → 开运算去毛刺
      6. 轻微高斯做抗锯齿边缘
    返回 float32 HxW, 取值 0..1（1 = 墨）。
    """
    im = Image.open(path).convert("L").filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(im, dtype=np.float32)
    lo, hi = np.percentile(a, 1), np.percentile(a, 99)
    a = np.clip((a - lo) / max(hi - lo, 1.0) * 255.0, 0, 255)
    thr = _otsu(a) * thresh_gain
    m = a < thr

    lab, sizes = _components(m)
    total = sum(sizes.values()) or 1
    keep = np.zeros_like(m)
    for cid, size in sizes.items():
        if size >= min_frac * total:
            keep |= (lab == cid)
    m = keep

    mi = Image.fromarray((m * 255).astype(np.uint8))
    mi = mi.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))   # 闭: 补飞白
    mi = mi.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))   # 开: 去毛刺
    ink = np.asarray(mi, dtype=np.float32) / 255.0
    if smooth:
        ink = np.asarray(Image.fromarray((ink * 255).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(smooth)), dtype=np.float32) / 255.0
    print(f"[极简处理] {Path(path).name}: Otsu×{thresh_gain:.2f} → {thr:.0f}, "
          f"连通域 {len(sizes)} → 保留 {int((keep.sum() > 0))}, 墨占比 {100*ink.mean():.2f}%")
    return ink


def square_canvas(ink, size=1024, pad=0.06):
    """裁到墨迹外框 → 等比放进正方形画布（留白 pad），返回 uint8 灰度掩膜。"""
    ys, xs = np.where(ink > 0.06)
    if len(xs) == 0:
        raise SystemExit("未在素材中找到墨迹，请检查阈值")
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    crop = ink[y0:y1 + 1, x0:x1 + 1]
    h, w = crop.shape
    inner = int(size * (1 - 2 * pad))
    scale = inner / max(h, w)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    im = Image.fromarray((np.clip(crop, 0, 1) * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("L", (size, size), 0)
    canvas.paste(im, ((size - nw) // 2, (size - nh) // 2))
    # 去边缘噪点: 轻微阈值再柔化，保留笔锋飞白
    a = np.asarray(canvas, dtype=np.float32) / 255.0
    a = np.where(a > 0.10, a, 0.0)
    a = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(0.6)), dtype=np.float32) / 255.0
    return (np.clip(a, 0, 1) * 255).astype(np.uint8), (x0, y0, x1, y1), (w, h)


def metal_lake(size=(1600, 1000)):
    """真实湖面照片 → 冷调金属湖面：去暖、压天空、提水面高光、加轻微胶片颗粒。"""
    im = Image.open(FRONT / "湖泊.jpg").convert("RGB")
    w, h = size
    # 裁到目标比例
    cw, ch = im.size
    tr = w / h
    if cw / ch > tr:
        nw = int(ch * tr)
        x0 = (cw - nw) // 2
        im = im.crop((x0, 0, x0 + nw, ch))
    else:
        nh = int(cw / tr)
        y0 = (ch - nh) // 2
        im = im.crop((0, y0, cw, y0 + nh))
    im = im.resize((w, h), Image.LANCZOS)

    a = np.asarray(im, dtype=np.float32)
    lum = a.mean(axis=2, keepdims=True)
    # 金属化: 大幅去饱和, 再压入青蓝-墨色
    a = lum * 0.58 + a * 0.42
    a[..., 2] *= 1.10
    a[..., 0] *= 0.86
    a[..., 1] *= 0.96
    # 提水面镜面反差(金属光泽): 高于均值的更亮, 低于的更暗
    m = lum / (lum.mean() + 1e-6)
    a *= np.clip(0.55 + 0.75 * np.clip(m, 0, 2.2), 0.5, 1.75)
    # 暗角
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = w / 2, h / 2
    r = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2)
    a *= np.clip(1.0 - 0.42 * np.clip(r - 0.35, 0, 2) ** 1.7, 0.25, 1.0)[..., None]
    # 细颗粒(避免廉价平滑渐变)
    rng = np.random.default_rng(7)
    a += rng.normal(0, 2.1, a.shape)
    a = np.clip(a, 0, 255).astype(np.uint8)
    return Image.fromarray(a)


# ────────────────────────────── 主流程 ──────────────────────────────
def main():
    ASSETS.mkdir(exist_ok=True)
    DOCS_ASSETS.mkdir(parents=True, exist_ok=True)
    report = []

    # 1. 书法归档
    Image.open(FRONT / "道.png").convert("RGB").save(ASSETS / "dao_original.png")
    Image.open(FRONT / "道.png").convert("RGB").save(DOCS_ASSETS / "dao_original.png")

    # 2. 墨迹掩膜
    ink = ink_mask_from_photo(FRONT / "道.png")
    mask, bbox, osize = square_canvas(ink, 1024)
    Image.fromarray(mask, "L").save(ASSETS / "dao_mask.png")
    Image.fromarray(mask, "L").save(DOCS_ASSETS / "dao_mask.png")
    cov = float((mask > 64).mean())
    print(f"[报告] dao_mask.png 墨占比={cov*100:.2f}%  原图={osize}  墨迹外框={bbox}")
    report.append(f"dao_mask.png 墨占比={cov*100:.2f}%  原图={osize}  墨迹外框={bbox}")
    ascii_preview(np.asarray(Image.fromarray(mask).resize((92, 92))), 52, "真实书法提取的 dao_mask")
    # 对照: 用楷体渲染同一个字, 确认提取的字形与朝向正确
    from PIL import ImageDraw, ImageFont
    try:
        ref = Image.new("L", (256, 256), 0)
        f = ImageFont.truetype("C:/Windows/Fonts/simkai.ttf", 220)
        ImageDraw.Draw(ref).text((128, 128), "道", font=f, fill=255, anchor="mm")
        ascii_preview(np.asarray(ref.resize((92, 92))), 52, "对照: 楷体渲染的『道』")
    except Exception as e:      # noqa: BLE001
        report.append(f"对照渲染失败: {e}")

    # 3. 白墨透明底（WebGL 降级 / logo 底图）
    white = np.zeros((1024, 1024, 4), dtype=np.uint8)
    white[..., 0:3] = 255
    white[..., 3] = mask
    Image.fromarray(white, "RGBA").save(ASSETS / "dao_ink.png")
    Image.fromarray(white, "RGBA").save(DOCS_ASSETS / "dao_ink.png")

    # 4. 湖面
    lake = metal_lake()
    lake.save(ASSETS / "lake.jpg", quality=88, optimize=True)
    lake.save(DOCS_ASSETS / "lake.jpg", quality=88, optimize=True)
    report.append(f"lake.jpg {lake.size}")

    # 5. logo（三档，全部来自真实书法）
    dao = Image.fromarray(mask, "L")
    for name, color, scale in (("logo.png", (18, 22, 28), 512),
                               ("logo_white.png", (237, 241, 247), 512),
                               ("logo_small.png", (237, 241, 247), 160),
                               ("favicon.png", (237, 241, 247), 64)):
        big = dao.resize((scale, scale), Image.LANCZOS)
        arr = np.asarray(big, dtype=np.uint8)
        rgba = np.zeros((scale, scale, 4), dtype=np.uint8)
        rgba[..., 0], rgba[..., 1], rgba[..., 2] = color
        rgba[..., 3] = arr
        Image.fromarray(rgba, "RGBA").save(ASSETS / name)
        Image.fromarray(rgba, "RGBA").save(DOCS_ASSETS / name)
    report.append("logo.png / logo_white.png / logo_small.png / favicon.png 已由真实书法派生")

    # 6. 架构图与可视化同步进 docs/assets
    import shutil
    for src in (HERE / "assets" / "architecture.svg", HERE / "docs" / "viz" / "architecture.svg"):
        if src.exists():
            for dst in (ASSETS / "architecture.svg", DOCS_ASSETS / "architecture.svg"):
                if src.resolve() != dst.resolve():
                    shutil.copy2(src, dst)
    for extra in ("logo_banner.png",):
        p = ASSETS / extra
        if p.exists():
            shutil.copy2(p, DOCS_ASSETS / extra)

    print("\n".join(report))
    print("完成 →", ASSETS, "/", DOCS_ASSETS)


if __name__ == "__main__":
    main()
