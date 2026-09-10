# -*- coding: utf-8 -*-
"""生成截图用副本: 去掉外部字体(离线渲染会挂住), hero 固定高度, 强制显示滚动动画元素。

用法: python tools/verify_page_shots.py
产出: out/hero.png(首屏) / out/page_full.png(整页) / out/page_hero_crop.png(道字区域)
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHROME = Path(r"C:\Users\16532\AppData\Local\ms-playwright\chromium-1234\chrome-win64\chrome.exe")
if not CHROME.exists():
    CHROME = Path(r"C:\Users\16532\AppData\Local\ms-playwright\chromium-1223\chrome-win64\chrome.exe")

OVERRIDE = """
<style id="verify-override">
.hero{height:900px !important;min-height:900px !important;}
.genesis-line,.struct-card,.model-card,.question-item,.section-label,
[data-delay],footer,.doc-card,.docs-grid{opacity:1 !important;transform:none !important;}
</style>
</head>"""


def build_copy(fix_hero=True):
    h = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    h = re.sub(r'\s*<link[^>]*fonts\.(googleapis|gstatic)[^>]*>', '', h)
    if fix_hero:
        h = h.replace("</head>", OVERRIDE, 1)
    p = ROOT / "docs" / "_verify.html"
    p.write_text(h, encoding="utf-8")
    return p


def shot(path, out, w, h):
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)
    subprocess.run([str(CHROME), "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                    "--force-device-scale-factor=1", f"--window-size={w},{h}",
                    f"--screenshot={out}", Path(path).as_uri()],
                   timeout=120, capture_output=True)
    print(f"{out.name}: {'OK ' + str(out.stat().st_size) + ' bytes' if out.exists() else '失败'}")


if __name__ == "__main__":
    p = build_copy()
    shot(p, ROOT / "out" / "hero.png", 1400, 900)
    shot(p, ROOT / "out" / "page_full.png", 1300, 4200)
    try:
        from PIL import Image
        f = Image.open(ROOT / "out" / "hero.png")
        f.crop((470, 190, 960, 660)).save(ROOT / "out" / "page_hero_crop.png")
        print("page_hero_crop.png: OK")
    except Exception as e:                       # noqa: BLE001
        print("裁剪失败:", e)
