# -*- coding: utf-8 -*-
"""tools/research/imagination_batch_verify.py — 想象路批量验证：376 个疑似新概念查真实所指（R78）

想象路的验证 = 确认概念有真实领域支撑(非空想)。
对"疑似新(对象×操作)"批量查: 概念的核心词是否在本地语料(各领域手册/科学史)里被研究。

方法: 每个概念词 a+b, 在语料里搜 a 与 b 各自是否作为真实研究对象出现;
若两者都有真实所指, 概念"有领域支撑"; 若其一无, "待更强解释"。
"""
import glob
import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
CORPUS = Path(r"E:\ask-dao\_text")

# 从 imagination_verify.json 读"疑似新"
def load_terms():
    v = json.loads((HERE / "out/demo/imagination_verify.json").read_text(encoding="utf-8"))
    return [e["term"] for e in v if e["status"].startswith("疑似新")]


# 语料关键词命中表: 词 -> 该词在哪些领域语料出现
DOMAIN_FILES = {
    "数学": ["histmath.md", "06_数学哲学.md"],
    "物理": ["histphys.md", "08_物理学哲学_套装共3册.md"],
    "生物": ["02_生物学哲学.md"],
    "心理": ["01_心理学与认知科学哲学.md"],
    "语言": [], "信息": ["03_信息哲学_套装上下册.md"],
    "工程": ["04_技术与工程科学哲学_套装共3册.md"],
    "经济": [], "音乐": [], "艺术": [],
    "伦理": [], "逻辑": ["05_逻辑哲学_套装上下册.md"],
    "哲学": ["07_一般科学哲学_焦点主题.md", "中国哲学史第2版.md"],
}

# 词的领域归属(和 imagination_verify 一致)
WORDS_DOMAIN = {
    "公理化":"数学","测度":"数学","拓扑":"数学","同调":"数学","熵":"数学","不变量":"数学",
    "递推":"数学","极值":"数学","对称性":"物理","守恒":"物理","相变":"物理","场":"物理",
    "量子化":"物理","纠缠":"物理","临界":"物理","演化":"生物","选择":"生物","适应性":"生物",
    "共生":"生物","生态位":"生物","代谢":"生物","发育":"生物","催化":"化学","合成":"化学",
    "键合":"化学","平衡":"化学","周期律":"化学","认知":"心理","意识":"心理","记忆":"心理",
    "学习":"心理","情绪":"心理","动机":"心理","语法":"语言","语义":"语言","语用":"语言",
    "转喻":"语言","隐喻":"语言","话语":"语言","编码":"信息","信道":"信息","压缩":"信息",
    "冗余":"信息","反馈":"信息","噪声":"信息","工业化":"工程","标准化":"工程","自动化":"工程",
    "模块化":"工程","可维护性":"工程","优化":"工程","资本":"经济","市场":"经济","效率":"经济",
    "分配":"经济","增长":"经济","稀缺":"经济","和声":"音乐","节奏":"音乐","对位":"音乐",
    "旋律":"音乐","调性":"音乐","美学":"艺术","形式":"艺术","风格":"艺术","再现":"艺术",
    "表现":"艺术","责任":"伦理","规范":"伦理","价值":"伦理","善":"伦理","正义":"伦理",
    "可判定":"逻辑","一致":"逻辑","完备":"逻辑","模型":"逻辑","公设":"逻辑","本体":"哲学",
    "认识":"哲学","现象":"哲学","本质":"哲学","自由":"哲学",
}

# 预载语料缓存
_cache = {}
def _corpus_text():
    if not _cache:
        for fn in glob.glob(str(CORPUS / "*.md")):
            _cache[fn] = Path(fn).read_text(encoding="utf-8", errors="ignore")[:50000]
        for fn in glob.glob(str(CORPUS / "handbook" / "*.md")):
            _cache[fn] = Path(fn).read_text(encoding="utf-8", errors="ignore")[:100000]
        for fn in glob.glob(str(CORPUS / "scihist" / "*.md")):
            _cache[fn] = Path(fn).read_text(encoding="utf-8", errors="ignore")[:30000]
    return _cache


def has_reference(word):
    """词在语料里是否有真实所指(出现即算, 且在其领域语料或全局)。"""
    texts = list(_corpus_text().values())
    # 出现次数(全部语料)
    n = sum(t.count(word) for t in texts)
    return n, (n >= 3)   # 出现>=3次算有真实所指


def main():
    terms = load_terms()
    corpus = _corpus_text()
    print("=" * 100)
    print(f"想象路批量验证 —— {len(terms)} 个'疑似新'概念查真实所指")
    print("=" * 100)
    print(f"  语料: {len(corpus)} 个文件")

    results = []
    for term in terms:
        # 拆词: 找第二词(操作词)
        parts = []
        for w in WORDS_DOMAIN:
            if term.startswith(w):
                rest = term[len(w):]
                if rest in WORDS_DOMAIN:
                    parts = (w, rest)
                    break
        if not parts:
            continue
        a, b = parts
        na, oka = has_reference(a)
        nb, okb = has_reference(b)
        both = oka and okb
        results.append({"term": term, "a": a, "b": b, "a_domain": WORDS_DOMAIN[a],
                        "b_domain": WORDS_DOMAIN[b], "a_refs": na, "b_refs": nb,
                        "grounded": both})

    grounded = [r for r in results if r["grounded"]]
    ungrounded = [r for r in results if not r["grounded"]]
    print(f"\n  验证 {len(results)} 个概念")
    print(f"  **有真实领域支撑(两个词都真实被研究): {len(grounded)}**")
    print(f"  弱支撑(至少一词缺): {len(ungrounded)}")

    print("\n== 有真实支撑的概念(抽样 20) ==")
    for r in grounded[:20]:
        print(f"  「{r['term']}」 ({r['a_domain']}×{r['b_domain']}) "
              f"{r['a']}:{r['a_refs']}次 {r['b']}:{r['b_refs']}次")

    print("\n诚实: '有真实支撑' = 两词都在语料被研究(非空想); 概念本身是否新仍需文献门。")
    (HERE / "out/demo/imagination_batch_verify.json").write_text(
        json.dumps({"grounded": grounded, "ungrounded": ungrounded},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n已存 out/demo/imagination_batch_verify.json")


if __name__ == "__main__":
    main()
