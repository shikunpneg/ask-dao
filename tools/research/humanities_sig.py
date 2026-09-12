# -*- coding: utf-8 -*-
"""tools/research/humanities_sig.py — 数学x人文 第二步: 置换检验
判: '学术手册句长 > 通俗哲学句长' 是否统计显著(不依赖分布假设)。"""
import random
import re
from pathlib import Path

TEXT = Path(r"E:\ask-dao\_text")


def sentences_of(pat, n_chars=200000):
    import glob
    hits = glob.glob(str(TEXT / pat))
    if not hits:
        return []
    raw = Path(hits[0]).read_text(encoding="utf-8", errors="ignore")[:n_chars]
    raw = re.sub(r"(?m)^#.*$", "", raw)
    return [len(s) for s in re.split(r"[。！？!?；;\n]", raw) if s.strip()]


def perm_p(a, b, iters=4000, seed=7):
    rnd = random.Random(seed)
    obs = sum(a) / len(a) - sum(b) / len(b)
    allv = a + b
    n = len(a)
    m = len(allv) - n
    cnt = 0
    for _ in range(iters):
        rnd.shuffle(allv)
        d = sum(allv[:n]) / n - sum(allv[n:]) / m
        if abs(d) >= abs(obs):
            cnt += 1
    return obs, (cnt + 1) / (iters + 1)


def main():
    popular = sentences_of("哲学100问*.md")
    academic = []
    for pat in ("handbook\\06_数学哲学.md", "handbook\\01_心理学与认知科学哲学.md"):
        academic += sentences_of(pat)
    popular = popular[:4000]
    academic = academic[:4000]
    obs, p = perm_p(popular, academic)
    md = Path("docs/humanities_math_demo.md")
    line = (f"## 显著性检验(置换4000次)\n"
            f"- 通俗句长均值 {sum(popular)/len(popular):.1f} vs 学术 {sum(academic)/len(academic):.1f} 字符\n"
            f"- 均值差 obs={obs:.1f}, 置换p值={p:.4f} -> "
            f"{'差异显著(可作体裁分类特征)' if p < 0.05 else '差异不显著'}\n")
    with md.open("a", encoding="utf-8") as f:
        f.write(line)
    print(line)


if __name__ == "__main__":
    main()
