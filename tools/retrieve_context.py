# -*- coding: utf-8 -*-
"""tools/retrieve_context.py — 想象模块的"经验文本检索器"

方案2(用户确认): 想象的翻译输入接现实经验。对组合词 a×b, 用 arXiv API
检索相关文献摘要, 作为翻译的脚手架(不是裁判)。

设计:
  - query = f'all:{a} AND all:{b}' (或 OR, 视命中率回退)
  - 取回 1-3 篇摘要, 截取与 a/b 相关的片段
  - 输出: {a, b, query, hits: [{title, abstract片段}]}
  - 网络失败 -> 返回空 hits(理解退化为无脚手架), 不崩溃

只检索, 不做任何价值判断。可判性留给下游领地协议。
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
ARXIV = "http://export.arxiv.org/api/query"
CACHE_FILE = HERE / "out" / "demo" / "retrieve_cache.json"

# 进程内节流: 两次 arXiv 请求至少间隔 N 秒(防 429)
_last_req = [0.0]
MIN_INTERVAL = 3.0
# 熔断: 连续失败 3 次 -> 本轮不再打 arXiv(直接本地语料), 避免限流下空等
_consec_fail = [0]
CIRCUIT_BREAK = 3


def _throttle():
    import time as _t
    dt = _t.time() - _last_req[0]
    if dt < MIN_INTERVAL:
        _t.sleep(MIN_INTERVAL - dt)
    _last_req[0] = _t.time()

# 中文词 -> 英文检索词(arXiv 是英文库, 必须映射)
EN_MAP = {
    "公理化": "axiom", "测度": "measure", "拓扑": "topology", "同调": "homology",
    "熵": "entropy", "不变量": "invariant", "递推": "recurrence", "极值": "extremum",
    "对称性": "symmetry", "守恒": "conservation", "相变": "phase transition",
    "场": "field", "量子化": "quantization", "纠缠": "entanglement", "临界": "criticality",
    "演化": "evolution", "选择": "selection", "适应性": "adaptation", "共生": "symbiosis",
    "生态位": "niche", "代谢": "metabolism", "发育": "development", "催化": "catalysis",
    "合成": "synthesis", "键合": "bonding", "平衡": "equilibrium", "周期律": "periodicity",
    "认知": "cognition", "意识": "consciousness", "记忆": "memory", "学习": "learning",
    "情绪": "emotion", "动机": "motivation", "语法": "grammar", "语义": "semantics",
    "语用": "pragmatics", "转喻": "metonymy", "隐喻": "metaphor", "话语": "discourse",
    "编码": "encoding", "信道": "channel", "压缩": "compression", "冗余": "redundancy",
    "反馈": "feedback", "噪声": "noise", "工业化": "industrialization",
    "标准化": "standardization", "自动化": "automation", "模块化": "modularity",
    "可维护性": "maintainability", "优化": "optimization", "资本": "capital",
    "市场": "market", "效率": "efficiency", "分配": "allocation", "增长": "growth",
    "稀缺": "scarcity", "和声": "harmony", "节奏": "rhythm", "对位": "counterpoint",
    "旋律": "melody", "调性": "tonality", "美学": "aesthetics", "形式": "form",
    "风格": "style", "再现": "representation", "表现": "expression", "责任": "responsibility",
    "规范": "norm", "价值": "value", "善": "goodness", "正义": "justice",
    "可判定": "decidability", "一致": "consistency", "完备": "completeness",
    "模型": "model", "公设": "postulate", "本体": "ontology", "认识": "epistemology",
    "现象": "phenomenon", "本质": "essence", "自由": "freedom",
}

# 词的本质描述(英文检索用: 把本质里的关键词也纳入 query)
# 直接从 word_understand 的 WORDS 拿本质, 这里留空, 检索时动态取


def _en(w):
    return EN_MAP.get(w, w)


def query_arxiv(q, n=3, retries=2):
    """arXiv API 检索, 返回 [{title, summary}]。失败返回 []。带节流防 429 + 熔断。"""
    if _consec_fail[0] >= CIRCUIT_BREAK:
        return []  # 熔断: 本轮不再打 arXiv
    url = ARXIV + "?" + urllib.parse.urlencode({
        "search_query": q, "max_results": n,
        "sortBy": "relevance", "sortOrder": "descending"})
    for attempt in range(retries):
        _throttle()
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                body = r.read().decode("utf-8", "replace")
            ns = {"a": "http://www.w3.org/2005/Atom"}
            root = ET.fromstring(body)
            out = []
            for ent in root.findall("a:entry", ns)[:n]:
                title = (ent.findtext("a:title", default="", namespaces=ns) or "").strip()
                summ = (ent.findtext("a:summary", default="", namespaces=ns) or "").strip()
                out.append({"title": re.sub(r"\s+", " ", title),
                            "summary": re.sub(r"\s+", " ", summ)})
            if out:
                _consec_fail[0] = 0  # 成功, 复位熔断
            return out
        except Exception:
            _consec_fail[0] += 1
            time.sleep(5)  # 限流/网络失败退避
    return []


def build_query(a, b):
    """用英文检索词: 先 AND, 若太窄回退 OR。"""
    ea, eb = _en(a), _en(b)
    if ea == a and eb == b:
        # 中文词没有映射(可能是英文词本身), 直接用
        return f'all:{a} AND all:{b}'
    return f'all:{ea} AND all:{eb}'


def clip(text, a, b, max_chars=500, mode="and"):
    """截取摘要中最相关的片段(AND: 含双词优先; OR: 含任一即可)。"""
    if not text:
        return ""
    sents = re.split(r"(?<=[。.;；])", text)
    scored = []
    for i, s in enumerate(sents):
        if mode == "and":
            sc = (1 if a in s else 0) + (1 if b in s else 0)
        else:
            sc = 1 if (a in s or b in s) else 0
        if sc:
            scored.append((sc, i, s.strip()))
    if scored:
        scored.sort(key=lambda x: (-x[0], x[1]))
        chosen = scored[0][2]
    else:
        chosen = text[:max_chars]
    return chosen[:max_chars]


def local_text(a, b, max_sents=2):
    """本地语料回退: 扫 out/demo 的 json(含大量项目文本), 找含 a 或 b 的片段。"""
    picked = []
    for jf in sorted((HERE / "out" / "demo").glob("*.json")):
        if jf.name in ("retrieve_cache.json", "oeis_batch_gate.json"):
            continue
        try:
            text = jf.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        sents = re.split(r"(?<=[。.；;])", text)
        for s in sents:
            if (a in s or b in s) and len(s) > 20 and len(s) < 300:
                picked.append({"title": f"本地语料 {jf.name}", "fragment": s.strip()})
                if len(picked) >= max_sents:
                    return picked
    return picked


def _load_cache():
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_cache(cache):
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")


def retrieve(a, b, cache_path=None):
    """对 a×b 检索经验文本。缓存优先, arXiv AND, OR 回退, 本地语料兜底。"""
    key = f"{a}×{b}"
    cache = _load_cache()
    if key in cache:
        return {"a": a, "b": b, "query": cache[key].get("query", ""), "hits": cache[key]["hits"]}
    ea, eb = _en(a), _en(b)
    q = build_query(a, b)
    entries = query_arxiv(q, n=3)
    mode = "and"
    if not entries and q != f'all:{ea} OR all:{eb}':
        q = f'all:{ea} OR all:{eb}'
        entries = query_arxiv(q, n=3)
        mode = "or"
    hits = []
    for e in entries:
        title = e["title"]
        frag = clip(e["summary"], ea, eb, mode=mode)
        if frag:
            hits.append({"title": title, "fragment": frag})
    if not hits:
        hits = local_text(a, b)
    result = {"a": a, "b": b, "query": q, "hits": hits}
    cache[key] = result
    _save_cache(cache)
    return result


if __name__ == "__main__":
    # 冒烟测试
    for pair in [("熵", "选择"), ("责任", "催化")]:
        r = retrieve(*pair)
        print(f"== {pair[0]}×{pair[1]} ==")
        print("  query:", r["query"])
        for h in r["hits"][:2]:
            print("  ·", h["title"][:60])
            print("   ", h["fragment"][:150])
