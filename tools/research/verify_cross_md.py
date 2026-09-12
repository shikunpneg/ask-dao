# -*- coding: utf-8 -*-
"""tools/research/verify_cross_md.py — 三域交叉候选的仿真验证
候选: 信念修正(心理) x 迭代(数学) x 含噪信道(信息)
命题: 在信道质量 q 下做贝叶斯式信念更新: 模型正确 -> 收敛真值; 模型低估噪声 -> 稳定偏差; 偏差随信道容量变化?
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def capacity(q):
    """BSC(q) 容量(bit)"""
    if q <= 0 or q >= 1:
        return 0.0
    h = lambda p: -p * math.log2(p) - (1 - p) * math.log2(1 - p) if 0 < p < 1 else 0.0
    return 1 - h(q)


def run_belief(q_true, q_hat, p0=0.5, T=20000, seed=11):
    import random
    rnd = random.Random(seed)
    p = p0
    for _ in range(T):
        bit = 1 if rnd.random() < q_true else 0  # 真值为1时观测正确的概率=q_true
        # 用假设 q_hat 做贝叶斯更新
        lik1 = q_hat if bit == 1 else (1 - q_hat)
        lik0 = (1 - q_hat) if bit == 1 else q_hat
        num = lik1 * p
        den = num + lik0 * (1 - p)
        p = num / den if den else p
    return p


def main():
    rows = []
    for q in (0.55, 0.6, 0.7, 0.8, 0.9, 0.99):
        C = capacity(q)
        p_correct = run_belief(q, q)          # 模型正确
        p_low = run_belief(q, max(0.5, q - 0.15))  # 低估噪声(以为信道更好)
        p_high = run_belief(q, min(0.99, q + 0.15))  # 高估噪声
        rows.append({"q": q, "capacity_bit": round(C, 4),
                     "belief_model_correct": round(p_correct, 4),
                     "belief_underest_noise": round(p_low, 4),
                     "belief_overest_noise": round(p_high, 4),
                     "bias_underest": round(1 - p_low, 4)})
    print("q    容量   模型正确  低估噪声  高估噪声  (后验p)")
    for r in rows:
        print(f"{r['q']:.2f} {r['capacity_bit']:.3f}  {r['belief_model_correct']:.4f}   "
              f"{r['belief_underest_noise']:.4f}   {r['belief_overest_noise']:.4f}")
    Path(HERE / "out/demo/cross_md_belief.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    # 判定
    conv = all(r["belief_model_correct"] > 0.99 for r in rows)
    bias = [r["bias_underest"] for r in rows]
    print("\n判定: 模型正确是否收敛到真值(>0.99):", conv)
    print("      低估噪声时的稳定偏差序列:", bias, "是否随容量单调↓:", all(bias[i] >= bias[i+1] for i in range(len(bias)-1)))


if __name__ == "__main__":
    main()
