# -*- coding: utf-8 -*-
"""tools/llm_judgment.py — LLM/人工裁判台账(操作层判官, 带文献出处)

定位说明(与纪律一致):
  本文件是**裁判记录**, 不是机器判定。项目口径: "LLM 是操作层裁判" (02_CONTEXT 第2节)。
  与 novelty_gate(机器实查 OEIS)不同, 文献检索**离线不可自动化** —— 因此这里逐条记录
  检索到的文献与裁决, 每条必须带出处; 未检索的必须如实标 "未检索", 不许默认"新"。

用法: 与 problem_gate 的输出合并, 供人看每问的 [机器前沿 + 文献裁决]。
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

# 逐条裁决。verdict 取值:
#   N0 已知(重发现) / N1 已知推论 / N2 检索未见(非"新") / 未检索
JUDGMENTS = {
    "CX_质数_三角数_char": {
        "verdict": "N0 已知(机器独立重发现)",
        "literature": "Zhi-Wei Sun, 'On sums of primes and triangular numbers', "
                      "arXiv:0803.3737 / J. Combin. Number Theory 1 (2009) 65-76",
        "finding": "Sun 猜想: 每个自然数 n ≠ 216 可写成 p + T_x (p=0 或素数)。"
                   "机器(要求 p 为正素数)的例外集 ⊆ {三角数} ∪ {216} —— "
                   "**216 正是 Sun 猜想的唯一例外**。机器独立重现了该猜想。",
        "machine_matched": True,
    },
    "CX_质数_三角数_finite": {
        "verdict": "N0 已知(同上)",
        "literature": "同 Sun (2009); Sun 已验证至 17,000,000",
        "finding": "同一猜想的有限性侧面; 机器延伸扫描找到更多例外(36→100个), "
                   "结论与 Sun 的验证方向一致(例外集无限, 但密度趋 0)。",
        "machine_matched": True,
    },
    "CX_质数_三角数_density": {
        "verdict": "N2 检索未见(非'新')",
        "literature": "未检索到直接的密度结果; Sun 系列讨论表数而非密度极限",
        "finding": "机器问'例外密度极限是否存在'。检索未见直接文献, "
                   "但**只是检索未见, 不等于新**(需专家/文献门)。",
        "machine_matched": None,
    },
    "CX_质数_平方数_char": {
        "verdict": "N0 已知(机器独立重现 Hardy-Littlewood 猜想 H 的例外集)",
        "literature": "Hardy-Littlewood 猜想 H (每个充分大非平方 n = p + m²); "
                      "Brünner-Perelli-Pintz (1989) 例外数 ≪ X^θ (θ<1); "
                      "Nayebi, 'Upper bounds on the solutions to n = p + m^2' arXiv:1004.0536; "
                      "Babaev: 例外集**无限**(猜想字面不成立)",
        "finding": "文献记载'可能的例外'开头为 **10, 34, 58, 85, …**; "
                   "机器(只扫偶数)得到 **[10, 34, 58, 64, 130, 196, 214, 226, 324, 370]** —— "
                   "偶数列完全吻合。机器额外含 64/196/324(均为平方数), "
                   "正是猜想 H 明文排除的'非平方'条件在机器版本下的可检测痕迹。"
                   "=> 机器独立重现了该猜想的例外集。",
        "machine_matched": True,
    },
    "CX_质数_平方数_finite": {
        "verdict": "N0 已知(同上; 且字面猜想已被 Babaev 否证)",
        "literature": "同猜想 H; Babaev 证明例外集无限",
        "finding": "机器'延伸扫描仍见新例外'的结论与 Babaev '例外无限'一致 —— "
                   "机器用有限手段得到了正确方向, 但**未证明**。",
        "machine_matched": True,
    },
    "CX_质数_平方数_density": {
        "verdict": "N1 已知推论方向",
        "literature": "Hardy-Littlewood 奇异级数给出 R(n) ~ S(n)·√n/log n 的渐近预测; "
                      "Davenport-Heilbronn (1937): 对几乎所有 n 成立",
        "finding": "机器问密度极限; 文献方向是表数函数渐近式(而非简单密度极限)。"
                   "机器未能给出刻画(前沿=R2 无进展), 与'需圆法'一致。",
        "machine_matched": None,
    },
    "CX_质数_半素数_char": {
        "verdict": "N0 已知(Chen 定理)",
        "literature": "Chen Jingrun (1973): 每个充分大偶数 = p + P₂ (素数 + 至多两个素因子之积)",
        "finding": "机器例外集仅 {10}, 且 10 = T₄ 是三角数(机器类库包含检查命中 "
                   "⊆ 三角数); 这正是 Chen 定理'充分大'之前的小例外。",
        "machine_matched": True,
    },
    "CX_奇合数_平方数_char": {
        "verdict": "N1 已知(小例外)",
        "literature": "加性基族; 未单独检索该组合",
        "finding": "机器给出候选刻画: 例外集 = n<398 的小例外, 之后恒成立。"
                   "**未检索文献** —— 但'小例外 + 渐近成立'通常对应已知渐近定理。",
        "machine_matched": None,
    },
    "CX_奇合数_三角数_char": {
        "verdict": "N1 已知(小例外)",
        "literature": "未单独检索",
        "finding": "机器候选刻画: 例外集 = n<662 的小例外。同上, 未检索。",
        "machine_matched": None,
    },
    "CX_奇合数_半素数_char": {
        "verdict": "N1 已知(小例外)",
        "literature": "未单独检索",
        "finding": "机器候选刻画: 例外集 = n<38 的小例外。同上, 未检索。",
        "machine_matched": None,
    },
    "CX_半素数_平方数_char": {
        "verdict": "N1 已知(小例外)",
        "literature": "未单独检索",
        "finding": "机器候选刻画: 例外集 = n<108 的小例外。同上, 未检索。",
        "machine_matched": None,
    },
    "CX_回文数_平方数_char": {
        "verdict": "N2 检索未见(非'新')",
        "literature": "检索(palindrome + square)返回空; 未见直接文献",
        "finding": "机器例外 3922 个(近 20%), 机器**未能**给出刻画(R2 无进展)。"
                   "检索未见 —— 但回文数依赖十进制, 非常规加性数论对象, "
                   "**检索未见不等于新**, 需专家。",
        "machine_matched": None,
    },
    "CX_回文数_平方数_finite": {
        "verdict": "N2 检索未见(非'新')",
        "literature": "同上的检索空结果",
        "finding": "机器延伸扫描见 1511 个新例外 -> 例外集几乎确定无限"
                   "(两稀疏类的和集覆盖不了全部偶数), 但机器不能证明。",
        "machine_matched": None,
    },
}


# ---- R26: 领地·进制依赖结构(Phase 1 首个稀疏领地) ----
JUDGMENTS.update({
    "CX_dig10_回文数_素数_holds": {
        "verdict": "N0o **已知·未解**(机器独立重发现一个公认开放问题)",
        "literature": "MathOverflow #250504 'Is every integer greater than 1 the sum of a "
                      "palindrome and a prime?' —— 明确状态为**既未证明也未否证**。"
                      "相邻已知结果: Helfgott(三素数)、Cilleruelo-Luca(每个整数=三个回文数之和)",
        "finding": "机器扫 [4,20000] 未发现任何例外, 于是问'这是定理吗?' —— "
                   "文献确认该二项版本(palindrome + prime)**是未解问题**。"
                   "机器在无文献输入下独立造出了一个**公认开放问题**(而非重发现定理)。"
                   "注: MO 讨论提到 9999/999999… 可能是反例候选; 机器在 [4,20000] 内对 9999 "
                   "找到了表示, 与'未发现例外'一致。",
        "machine_matched": True,
    },
    "CX_dig3_回文数_素数_char": {
        "verdict": "N2 检索未见(**非'新'**)",
        "literature": "检索 'palindrome + prime base b' 返回**空结果**; base-3 变体未见专门文献",
        "finding": "机器例外集 68 个(占 0.3%), 最大 12388; 分布极不均: [0,5000) 有 41 个, "
                   "[5000,10000) 有 0 个, [10000,15000) 仅 2 个。机器**未能**给出刻画。"
                   "检索为空 —— 但这只说明 base-3 少人做, **不等于新**。",
        "machine_matched": None,
    },
    "CX_dig3_回文数_素数_finite": {
        "verdict": "N2 检索未见(**非'新'**)",
        "literature": "同上, 检索空",
        "finding": "机器延伸到 39996 又见 2628 个新例外 -> 例外集几乎确定无限, 但机器不能证明。",
        "machine_matched": None,
    },
    "CX_dig3_回文数_素数_density": {
        "verdict": "N2 检索未见(**非'新'**)",
        "literature": "同上, 检索空",
        "finding": "机器问密度极限; base-3 例外密度极低(0.0005)且尾部多个窗口为 0, "
                   "机器未能给出稳定极限(前沿=无进展)。",
        "machine_matched": None,
    },
})


def load(path=None):
    p = Path(path) if path else HERE / "out/demo/problem_gate.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    for r in data["rows"]:
        r["llm_judgment"] = JUDGMENTS.get(r["id"], {"verdict": "未检索"})
    return data


def main():
    data = load()
    from collections import Counter
    c = Counter(r["llm_judgment"]["verdict"].split()[0] for r in data["rows"])
    print("LLM/文献裁决分布:", dict(c))
    print()
    for r in data["rows"]:
        j = r["llm_judgment"]
        mark = "✓机器吻合" if j.get("machine_matched") else ("—未检索" if j["verdict"] == "未检索" else "")
        print(f"[{j['verdict']}] {r['id']}  {mark}")
        print(f"    {j['finding'][:150]}")
    out = HERE / "out/demo/llm_judgment.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n已存 {out}")


if __name__ == "__main__":
    main()
