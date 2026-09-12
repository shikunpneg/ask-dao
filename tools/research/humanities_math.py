# -*- coding: utf-8 -*-
"""tools/research/humanities_math.py — 数学 × 人文学科 交叉(计量文体学):
   用本库人文语料计算: 句长分布 / 字频Zipf指数 / 一阶字符熵 —— 经验纪录(可复算)。
   命题层: 把统计差异转成可检验的'文体-文本'问题(译文/体裁/口语度)。"""
import json
import math
import re
from pathlib import Path

TEXT = Path(r"E:\ask-dao\_text")
FILES = [
    ("哲学100问(通俗)", "哲学100问*.md"),
    ("中国哲学史第2版(教材)", "中国哲学史第2版.md"),
    ("手册-数学哲学(学术)", "handbook\\06_数学哲学.md"),
    ("手册-心理学(学术)", "handbook\\01_心理学与认知科学哲学.md"),
]


def load_sample(pat, n=300000):
    import glob
    hits = glob.glob(str(TEXT / pat))
    if not hits:
        return None
    raw = Path(hits[0]).read_text(encoding="utf-8", errors="ignore")
    raw = re.sub(r"(?m)^#.*$", "", raw)
    raw = raw.replace("`", "").replace("[图]", "")
    return raw[:n]


def stats(text):
    sents = [len(s) for s in re.split(r"[。！？!?；;\n]", text) if s.strip()]
    mlen = sum(sents) / len(sents)
    sdev = (sum((s - mlen) ** 2 for s in sents) / len(sents)) ** 0.5
    # 字频 Zipf: top200 log-log 斜率
    cnt = {}
    for ch in text:
        if ch.strip() and not ch.isascii():
            cnt[ch] = cnt.get(ch, 0) + 1
    top = sorted(cnt.values(), reverse=True)[:200]
    n_t = len(text)
    xs = [math.log10(i + 1) for i in range(len(top))]
    ys = [math.log10(v / n_t) for v in top]
    n2 = len(xs)
    mx, my = sum(xs) / n2, sum(ys) / n2
    slope = sum((xs[i] - mx) * (ys[i] - my) for i in range(n2)) / \
        sum((xs[i] - mx) ** 2 for i in range(n2))
    # 一阶字符熵(nats)
    H = -sum((c / n_t) * math.log(c / n_t) for c in cnt.values())
    return {"chars": n_t, "sents": len(sents), "mean_sent_len": round(mlen, 2),
            "std_sent_len": round(sdev, 2), "zipf_slope": round(slope, 4),
            "entropy1_nats": round(H, 4)}


def main():
    rows = []
    for name, pat in FILES:
        txt = load_sample(pat)
        if not txt:
            print("missing", pat)
            continue
        s = stats(txt)
        rows.append({"name": name, **s})
        print(f"{name}: 句长均{ s['mean_sent_len']}±{s['std_sent_len']} | Zipf斜率{s['zipf_slope']} | 熵{s['entropy1_nats']}")
    Path("out/demo/humanities_math.json").parent.mkdir(parents=True, exist_ok=True)
    Path("out/demo/humanities_math.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    md = ["# 数学 × 人文学科 交叉: 计量文体学纪录(可复算)", ""]
    for r in rows:
        md.append(f"## {r['name']}")
        md.append(f"- 句长均值 {r['mean_sent_len']} ± {r['std_sent_len']} 字符 | 字频Zipf斜率 {r['zipf_slope']} | 一阶字符熵 {r['entropy1_nats']} nats")
    md += ["",
           "## 由此生成的交叉问题(待判定路由: 文本统计+显著性检验)",
           "1. 通俗哲学(哲学100问) 与 学术手册 的 Zipf 斜率差是否稳健(子样本自举)? —— 可作'口语度/学术度'代理?",
           "2. 教材(中哲2版) 的句长 std 偏高是否源于引文与论述混排? —— 可检验'文体混杂度'指标?",
           "3. 手册各卷熵值差异能否聚类出译者/文体分组? —— 计量文体学的作者归属模板移用到译本。",
           "诚实: 以上均为'关于本语料的经验纪录', 新颖性弱, 价值=示范 数学(统计)×人文(语料) 交叉通道; 判定=显著性检验(可本机做)。"]
    Path("docs/humanities_math_demo.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
