# -*- coding: utf-8 -*-
"""perceive.py — 经验/感知入口：图像的结构 → 日常疑问 → 可判的科学问题

这是"第一手经验"这条输入的正式 CLI 入口（此前只能单独跑 tools/core/perception_module.py）。

做法（诚实：最小闭环，二值化 + 统计特征，**无深度学习**）：
  1. 读入图像（.png/.jpg/.jpeg/.bmp/.tif；无参数时用 numpy 造合成图，零依赖也能跑）
  2. 提取结构特征：前景密度 / 水平-垂直对称度 / 局部块熵 / 边界密度
  3. 特征触发器把"视觉里浮现的结构或异常"写成日常疑问
  4. 每条日常疑问加工成**带判定路由**的科学问题（统计测量 / 信息论 / 图像处理）

输出: <out>/problems_perceive.json（report.py 会自动汇总它）+ 一页人话报告

用法:
  python -m ask_dao_machine perceive                      # 合成图（零依赖）
  python -m ask_dao_machine perceive 图片.png 目录/         # 真实图像
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np

TRIGGERS = [
    ("对称性", lambda f: f["sym_h"] > 0.9 or f["sym_v"] > 0.9,
     "很对称",
     "该图像呈现高对称结构。真实自然/人造对象的对称度分布是什么？对称度与视觉复杂度的关系？",
     "统计测量：对图像库测对称度与熵，检验两者是否负相关"),
    ("复杂度-熵", lambda f: f["local_entropy"] > 3.0,
     "很复杂",
     "该图像的局部块熵接近上界。自然图像的块熵分布是什么？与人类复杂度感知是否一致？",
     "信息论：图像块熵 vs 人类复杂度评分（需行为实验）"),
    ("边界", lambda f: f["edge_density"] > 0.3,
     "纹理很密",
     "该图像边界密度高（纹理丰富）。边界密度与对象分割难度的定量关系是什么？",
     "图像处理：边界检测准确率 vs 边界密度（可做对照实验）"),
    ("密度异常", lambda f: f["density"] < 0.1 or f["density"] > 0.9,
     "很空或很满",
     "该图像前景占比极端。占空比与美学判断的关系是什么？是否存在偏好区间？",
     "统计：不同占空比下的人类美学评分分布"),
]

EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp")
_SKIP = {"readme.md"}


def synthetic_images() -> dict:
    """无参数时用 numpy 造几张典型结构图，保证零依赖可跑。"""
    rng = np.random.default_rng(7)
    n = 128
    yy, xx = np.mgrid[0:n, 0:n]
    checker = (((yy // 8) + (xx // 8)) % 2 * 255).astype(np.uint8)
    blobs = np.zeros((n, n), dtype=np.uint8)
    for _ in range(12):
        cy, cx, r = rng.integers(10, n - 10, 3)
        blobs[((yy - cy) ** 2 + (xx - cx) ** 2) < r * r * 0.3] = 255
    grad = (xx / n * 255).astype(np.uint8)
    noise = rng.integers(0, 256, (n, n), dtype=np.uint8)
    return {"synthetic:checkerboard": checker, "synthetic:blobs": blobs,
            "synthetic:gradient": grad, "synthetic:noise": noise}


def load_image(src: Path) -> np.ndarray:
    try:
        from PIL import Image                       # 真实图片需要 Pillow
    except Exception as e:                          # noqa: BLE001
        raise RuntimeError(f"读真实图片需要 Pillow（pip install pillow）：{e}") from e
    return np.asarray(Image.open(src).convert("L"))


def features(arr: np.ndarray) -> dict:
    """结构特征（与 tools/core/perception_module.py 同口径，便于对照）。

    注意：对称度是"二值化后镜像比对"，对**相位敏感**——棋盘格这类图案镜像后会错半个周期，
    测得对称度接近 0。这是方法的已知局限，不是图像的问题。
    """
    h, w = arr.shape
    b = (arr > arr.mean()).astype(np.float64)
    density = b.mean()
    sym_h = 1 - np.abs(b - b[:, ::-1]).mean()
    sym_v = 1 - np.abs(b - b[::-1, :]).mean()
    hh, ww = h // 2 * 2, w // 2 * 2
    blocks = b[:hh, :ww].reshape(h // 2, 2, w // 2, 2).transpose(0, 2, 1, 3).reshape(-1, 4)
    labels = blocks @ np.array([1, 2, 4, 8])
    cnt = Counter(labels.ravel())
    tot = sum(cnt.values()) or 1
    entropy = -sum((c / tot) * math.log2(c / tot) for c in cnt.values() if c)
    dx = np.abs(np.diff(b, axis=0))
    dy = np.abs(np.diff(b, axis=1))
    m = (min(dx.shape[0], dy.shape[0]), min(dx.shape[1], dy.shape[1]))
    edge_density = ((dx[:m[0], :m[1]] + dy[:m[0], :m[1]]) > 0).mean()
    return {"size": [h, w], "density": round(float(density), 3),
            "sym_h": round(float(sym_h), 3), "sym_v": round(float(sym_v), 3),
            "local_entropy": round(float(entropy), 3),
            "edge_density": round(float(edge_density), 3)}


def image_to_questions(arr: np.ndarray, name: str, idx: int) -> list[dict]:
    f = features(arr)
    out = []
    for k, (tname, cond, human, sci, route) in enumerate(TRIGGERS):
        if not cond(f):
            continue
        out.append({
            "id": f"PV{idx:02d}{k}",
            "source": name, "domain": "视觉感知", "type": "①经验→问题（视觉）",
            "is_author_stated": False,
            "signal": tname, "features": f, "trigger": tname,
            "evidence": f"{name} 的结构特征：密度 {f['density']} · 对称 {f['sym_h']}/{f['sym_v']} · "
                        f"块熵 {f['local_entropy']} · 边界 {f['edge_density']}",
            "daily_question": f"这张图（{name}）为什么看起来{human}？",
            "statement": sci,
            "route": route, "status": "待实验/待数据",
        })
    return out


def _median_mad(vals: list[float]) -> tuple[float, float]:
    import statistics
    if not vals:
        return 0.0, 0.0
    med = statistics.median(vals)
    mad = statistics.median([abs(v - med) for v in vals]) or 1e-6
    return med, mad


def batch_relative(batch: dict, name: str) -> list[dict]:
    """≥3 张图时：按各特征的 中位数/MAD 找离群；离群 → 出可判问题。"""
    if len(batch) < 3:
        return []
    feats = {n: features(a) for n, a in batch.items()}
    keys = ("sym_h", "sym_v", "local_entropy", "edge_density", "density")
    out = []
    for k in keys:
        med, mad = _median_mad([feats[n][k] for n in batch])
        v = feats[name][k]
        z = abs(v - med) / mad
        if z >= 3.0:                       # 明显的批内离群
            direction = "高" if v > med else "低"
            out.append({
                "id": f"PVB{abs(hash((name, k))) % 100:02d}",
                "source": name, "domain": "视觉感知", "type": "②批内离群（视觉）",
                "is_author_stated": False,
                "signal": f"{k} 离群",
                "evidence": f"{name}：{k}={v}，批内中位数 {round(med, 3)}、MAD {round(mad, 3)}（z≈{z:.1f}）",
                "daily_question": f"这张图（{name}）的 {k} 为什么比同批其它图明显偏{direction}？",
                "statement": f"该图 {k} 显著偏离同批基线（z≈{z:.1f}）。这属于个体差异还是该类对象的普遍规律？"
                             f"什么机制造成了这个{direction}偏？",
                "route": "统计测量：扩大样本量做分布检验（批内离群 → 全库基线）",
                "status": "待实验/待数据",
            })
    return out


def baseline_question(arr, name: str, idx: int) -> dict:
    """每张图至少出一条：它在特征空间里的位置（判定路由明确）。"""
    f = features(arr)
    return {
        "id": f"PVB{idx:02d}0",
        "source": name, "domain": "视觉感知", "type": "③分布位置（视觉，每图必有）",
        "is_author_stated": False, "signal": "基线",
        "evidence": f"{name} 结构特征：密度 {f['density']} · 对称 {f['sym_h']}/{f['sym_v']} · "
                    f"块熵 {f['local_entropy']} · 边界 {f['edge_density']}",
        "daily_question": f"这张图（{name}）在这个特征组合上算是「普通」还是「少见」？",
        "statement": "该图的结构特征（对称度 / 块熵 / 边界密度 / 前景占比）在同类图像库里处于什么位置？"
                     "是否存在一个可测的「正常区间」，越界对应可命名的视觉现象？",
        "route": "统计：与图像库基线比较（需 ≥3 张同批或外部基线）",
        "status": "待实验/待数据",
    }


def collect(paths) -> tuple[dict, list[Path]]:
    """返回 (图像集, 报错文件)。无路径 → 合成图。"""
    if not paths:
        return synthetic_images(), []
    imgs, bad = {}, []
    files: list[Path] = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            files += [f for f in sorted(p.rglob("*")) if f.suffix.lower() in EXTS
                      and f.name.lower() not in _SKIP]
        elif p.exists():
            files.append(p)
        else:
            bad.append(p)
    for f in files:
        try:
            imgs[f.name] = load_image(f)
        except Exception as e:                              # noqa: BLE001
            bad.append(f)
            print(f"[skip] {f.name}: {e}")
    return imgs, bad


def run(paths=None, out_dir="out/perceive", quiet=False) -> dict:
    from . import ui_console as _console
    _console.setup()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    imgs, bad = collect(paths or [])
    problems = []
    for i, (name, arr) in enumerate(imgs.items(), 1):
        qs = image_to_questions(arr, name, i)           # 绝对阈值触发
        qs += batch_relative(imgs, name)                # 批内离群（≥3 张）
        if not qs:
            qs = [baseline_question(arr, name, i)]      # 兜底：每图至少一条
        problems += qs
        if not quiet:
            f = features(arr)
            print(f"[{name}] {arr.shape[0]}x{arr.shape[1]} 密度{f['density']} "
                  f"对称{f['sym_h']}/{f['sym_v']} 熵{f['local_entropy']} 边界{f['edge_density']}"
                  f" -> 问题 {len(qs)} 条")
    payload = {
        "domain": "perceive", "generator": "ask-dao-machine/input_image.py",
        "files": list(imgs.keys()), "counts": {"total": len(problems),
                                               "machine_raised": len(problems)},
        "roots": [{"id": "PERCEIVE_ROOT", "label": f"经验输入：{len(imgs)} 张图像"}],
        "problems": problems,
    }
    dst = out / "problems_perceive.json"
    dst.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    if not quiet:
        print(f"\n合计 {len(problems)} 条（视觉经验 → 可判问题）→ {dst}")
        print("诚实：这是最小闭环（二值化 + 统计特征，无深度学习）；每条问题都要接判定路由才算可判。")
    return payload


def main(argv=None, out_dir="out/perceive") -> int:
    from . import ui_console as _console
    _console.setup()
    argv = list(sys.argv[1:] if argv is None else argv)
    payload = run(argv, out_dir=out_dir)
    per = payload.get("counts", {})
    if not per.get("total"):
        print("没有从这些图像里触发任何问题（特征未越阈）：换一组图像，或看图是否过小/过平。",
              file=sys.stderr)
        if argv:
            return 0
        return 2
    from . import output_report as report_mod
    report_mod.main(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
