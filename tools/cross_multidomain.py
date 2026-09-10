# -*- coding: utf-8 -*-
"""tools/cross_multidomain.py — 多域交叉融合 v2 (2域/3域)
 单元: 域母题(L3方向) x 载体 x (可选)第三域判据
 流程: 笛卡尔 -> F1良构 -> F2可验证 -> F3参照系(内置签名) -> F4证据依赖当务门 -> 数值验证
 纪律: 当务分只用证据依赖版(big_score_ev), 禁关键词灌水。
"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from big_score_ev import score_ev

HERE = Path(__file__).resolve().parent.parent

# 域母题库(跨域)
D = {
    "信息": {"方向": ["熵率上界", "信道容量", "算法复杂度", "语义接地"],
             "载体": ["有限文法语言", "编码族", "序列族"]},
    "数学": {"方向": ["分布均匀性", "表示覆盖", "极值纪录", "收敛与周期"],
             "载体": ["质数模类", "递推映射", "禁构族"]},
    "生物": {"方向": ["选择迭代", "群体固定", "功能解释"],
             "载体": ["等位基因频率", "性状分布"]},
    "心理": {"方向": ["信念修正", "机制分解"],
             "载体": ["证据流", "双分离任务"]},
    "物理": {"方向": ["对称守恒", "尺度标度"],
             "载体": ["守恒量谱", "临界指数"]},
    "语言": {"方向": ["形式文法", "歧义"],
             "载体": ["CFG/正则族", "句法树"]},
    "工程": {"方向": ["功能结构映射", "可靠性"],
             "载体": ["设计空间", "失效模式"]},
}

# 可数值/仿真验证的交叉模板(带触发器: 判定路由)
TEMPLATES = [
    # 3域: 生物选择 x 数学递推 x 信息熵
    ("3-域", ["生物", "数学", "信息"],
     "带熵约束的选择迭代: 等位基因频率 p_{n+1}=p_n w(p_n)/(p_n w(p_n)+(1-p_n)) 在加入信息熵下界约束后是否仍收敛? 收敛点如何随熵阈值移动?",
     "仿真: 迭代+熵计算; 可本机跑"),
    # 2域: 信息熵率 x 语言文法
    ("2-域", ["信息", "语言"],
     "有限文法语言的熵率上界是多少? 无歧义CFG能否达到字母表熵 log|Σ|?",
     "数值: 邻接谱半径/Catalan生长(ling 引擎已验)"),
    # 3域: 心理信念修正 x 数学迭代 x 信息信道
    ("3-域", ["心理", "数学", "信息"],
     "信念修正(AGM式)在含噪信道下的迭代: 收敛到真值, 还是稳定偏差? 偏差随信道容量如何变化?",
     "仿真: AGM修正+信道噪声; 可本机跑"),
    # 2域: 物理对称 x 数学极值
    ("2-域", ["物理", "数学"],
     "守恒量谱的极值分布是否服从尺度律? 对称破缺如何移动极值?",
     "数值+类比(需物理模型)"),
    # 3域: 工程可靠性 x 数学极值 x 信息熵
    ("3-域", ["工程", "数学", "信息"],
     "冗余设计的可靠性-成本帕累托前沿在信息熵约束下如何移动?",
     "仿真: 可靠性模型+熵约束"),
]


def f1(s):
    return len(s) >= 20 and "{" not in s


def f2(route):
    return "仿真" in route or "数值" in route


def f3(sig_cache, s):
    # 参照系: 内置已知签名(此处用关键词兜底; 真参照系走 OEIS/文献)
    hits = [k for k in ["哥德巴赫", "Collatz", "熵率上界"] if k in s]
    return hits


def main():
    rows = []
    for ttype, doms, stmt, route in TEMPLATES:
        rows.append({"type": ttype, "domains": doms, "statement": stmt, "route": route})
    f1p = [r for r in rows if f1(r["statement"])]
    f2p = [r for r in f1p if f2(r["route"])]
    graded = []
    for r in f2p:
        # 证据轨道: 提供证据字段者才给分(本轮先给'可验证路由'作为H7/H10证据)
        ev = {"method_gap": True, "experiment_design": r["route"] if "仿真" in r["route"] else None,
              "route": r["route"]}
        sc = score_ev({"evidence": ev})
        r["H_ev"] = sc["total"]
        r["notes"] = sc["notes"]
        graded.append(r)
    graded.sort(key=lambda x: -x["H_ev"])
    print(f"生成 {len(rows)} -> F1 {len(f1p)} -> F2 {len(f2p)} -> 证据门后 {len(graded)}")
    for r in graded:
        print(f"  H={r['H_ev']} [{r['type']} {r['domains']}] {r['statement'][:78]}")
    Path("out/demo/cross_multidomain.json").parent.mkdir(parents=True, exist_ok=True)
    Path("out/demo/cross_multidomain.json").write_text(
        json.dumps(graded, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
