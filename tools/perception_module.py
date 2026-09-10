# -*- coding: utf-8 -*-
"""tools/perception_module.py — 感知/经验模块(用户愿景的"第一手经验"入口)

用户最初的愿景 + 本轮重申:
  摄像头视觉/收音机听觉 -> 解析一手感觉 -> 结构化自然语言(实体/属性/结构)
  -> 日常疑问 -> 真问题 -> 接问题生成器 -> AI4S求解 -> 论文。

本模块实现"视觉经验 -> 结构 -> 科学问题"的**最小闭环**:
  1. 输入图像(本地图或 skimage 内置)
  2. 提取结构特征: 对称度 / 局部复杂度(熵) / 边界密度 / 分布均匀性 / 周期模式
  3. 把"视觉中浮现的异常或结构"写成日常疑问
  4. 加工成科学问题(带判定路由, 接 discovery 清单)

关键: 不是"看图说话"(那是描述), 而是"从图像的结构里挖出可判的科学问题"。
"""
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent.parent


def load_image(src):
    """加载图像 -> 灰度 numpy 数组(二维)。支持路径或 skimage 内置名。"""
    from skimage import data, color
    if src.endswith(('.png', '.jpg', '.jpeg')):
        from PIL import Image
        arr = np.array(Image.open(src).convert('L'))
        return arr
    img = getattr(data, src)()
    if img.ndim == 3:
        img = color.rgb2gray(img)
    return img


def features(arr):
    """提取图像的结构特征。"""
    h, w = arr.shape
    arr = (arr > arr.mean()).astype(np.float64)   # 二值化(简化)
    n = h * w
    # 1) 前景占比
    density = arr.mean()
    # 2) 对称度: 水平/垂直/对角镜像差异
    sym_h = 1 - np.abs(arr - arr[:, ::-1]).mean()
    sym_v = 1 - np.abs(arr - arr[::-1, :]).mean()
    # 3) 局部复杂度: 2x2 块的经验熵
    blocks = arr[:h // 2 * 2, :w // 2 * 2].reshape(h // 2, 2, w // 2, 2).transpose(0, 2, 1, 3).reshape(h // 2, w // 2, 4)
    blabels = blocks @ np.array([1, 2, 4, 8])
    cnt = Counter(blabels.ravel())
    tot = sum(cnt.values()) or 1
    H = -sum((c / tot) * math.log2(c / tot) for c in cnt.values() if c)
    # 4) 边界密度: 相邻像素变化比例(两者都裁到 (h-1, w-1))
    dx = np.abs(np.diff(arr, axis=0))          # (h-1, w)
    dy = np.abs(np.diff(arr, axis=1))          # (h, w-1)
    edge = (dx[:dx.shape[0] - 1, :dx.shape[1] - 1] + dy[:dx.shape[0] - 1, :dx.shape[1] - 1]) > 0
    edge_dens = edge.mean()
    # 5) 周期模式: 行差分的自相关(粗略)
    return {
        "size": [h, w], "density": round(float(density), 3),
        "sym_h": round(float(sym_h), 3), "sym_v": round(float(sym_v), 3),
        "local_entropy": round(float(H), 3), "edge_density": round(float(edge_dens), 3),
    }


# 特征 -> 科学问题的模板(带判定路由)
PROBLEM_TEMPLATES = [
    ("对称性", lambda f: f["sym_h"] > 0.9 or f["sym_v"] > 0.9,
     "该图像呈现高对称。真实自然/人造对象的对称度分布是什么? 对称度与视觉复杂度的关系?",
     "统计测量: 对图像库测对称/熵, 看两者是否负相关"),
    ("复杂度-熵", lambda f: f["local_entropy"] > 3.0,
     "该图像的局部块熵接近上界(高复杂度)。自然图像的熵分布? 与人类复杂度感知是否一致?",
     "信息论: 图像块熵 vs 人类复杂度评分(需实验)"),
    ("边界", lambda f: f["edge_density"] > 0.3,
     "该图像边界密度高(纹理丰富)。边界密度与对象分割难度的关系?",
     "图像处理: 边界检测准确率 vs 密度"),
    ("密度异常", lambda f: f["density"] < 0.1 or f["density"] > 0.9,
     "该图像前景占比极端(极空/极满)。占空比与美学判断的关系?",
     "统计: 不同占空比下的人类美学评分"),
]


def image_to_questions(arr, name):
    f = features(arr)
    qs = []
    for tname, cond, q, route in PROBLEM_TEMPLATES:
        if cond(f):
            qs.append({"source": name, "domain": "视觉感知",
                       "features": f, "trigger": tname,
                       "daily_question": f"这张{name}为什么看起来{ {'对称性':'很对称','复杂度-熵':'很复杂','边界':'纹理很密','密度异常':'很空或很满'}[tname] }?",
                       "scientific_question": q,
                       "judge_route": route,
                       "status": "待实验/待数据"})
    return qs


def main():
    print("=" * 100)
    print("感知/经验模块 —— 视觉 -> 结构 -> 日常疑问 -> 科学问题")
    print("=" * 100)
    images = ["camera", "coins", "checkerboard", "astronaut", "coffee", "brick",
              "grass", "binary_blobs"]
    all_q = []
    for img in images:
        arr = load_image(img)
        qs = image_to_questions(arr, img)
        f = features(arr)
        print(f"\n  [{img}] {arr.shape} 密度{f['density']} 对称H/V={f['sym_h']}/{f['sym_v']} "
              f"熵{f['local_entropy']} 边界{f['edge_density']}")
        for q in qs:
            print(f"    · 日常: {q['daily_question']}")
            print(f"    · 科学: {q['scientific_question'][:80]}")
        all_q += qs
    print(f"\n  共产生 {len(all_q)} 条视觉->科学问题")

    # 接入 discovery manifest
    man = HERE / "out/demo/discovery_manifest.json"
    if man.exists():
        d = json.loads(man.read_text(encoding="utf-8"))
        d["problems"] += all_q
        d["count"] = len(d["problems"])
        man.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  已并入 discovery_manifest (总数 {d['count']})")

    print("\n诚实: 这是**视觉经验 -> 问题**的最小闭环(二值化+统计特征, 无深度学习);")
    print("  科学问题需接判定路由(统计/实验/信息论) 才能被 AI4S harness 解。")
    (HERE / "out/demo/perception_questions.json").write_text(
        json.dumps(all_q, ensure_ascii=False, indent=1), encoding="utf-8")
    print("  已存 out/demo/perception_questions.json")


if __name__ == "__main__":
    main()
