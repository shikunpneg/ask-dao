# -*- coding: utf-8 -*-
"""fetch_biomed_paper.py — 抓一篇真实、开放获取的生物医学全文（Europe PMC）。

只走公开接口，不绕过任何许可：
  检索: https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=...
  全文: https://www.ebi.ac.uk/europepmc/webservices/rest/<PMCID>/fullTextXML
产出: papers/biomed/<PMCID>.md（JATS → Markdown）+ <PMCID>.meta.json（含许可字段）

用法:
  python tools/maintain/fetch_biomed_paper.py                      # 默认抓演示用的那篇（PMC13331974）
  python tools/maintain/fetch_biomed_paper.py --query 'TITLE:"meta-analysis" AND OPEN_ACCESS:Y'
  python tools/maintain/fetch_biomed_paper.py --pmcid PMC13331974  # 直接指定
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "papers" / "biomed"
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
UA = {"User-Agent": "ask-dao-machine/0.5 (open-access demo fetcher)"}
DEFAULT_PMCID = "PMC13331974"
DEFAULT_QUERY = ('(TITLE:"association" OR TITLE:"cohort") AND (TITLE:"biomarker" OR '
                 'TITLE:"risk") AND (OPEN_ACCESS:Y) AND (SRC:MED) AND (HAS_FT:Y)')


def get(url: str, raw=False, tries=3, timeout=90):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                b = r.read()
            return b if raw else b.decode("utf-8", "replace")
        except Exception as e:                                  # noqa: BLE001
            print(f"    retry {i+1}: {type(e).__name__} {e}", file=sys.stderr)
            time.sleep(5)
    return None


def jats_to_text(xml: str) -> str:
    """JATS XML → Markdown 段落（标题 / 摘要 / 各章节）。"""
    root = ET.fromstring(xml)
    parts: list[str] = []

    def txt(el) -> str:
        return re.sub(r"\s+", " ", "".join(el.itertext())).strip()

    for t in root.iter("article-title"):
        parts.append("# " + txt(t))
        break
    for ab in root.iter("abstract"):
        parts.append("## Abstract")
        for p in ab.iter("p"):
            parts.append(txt(p))
        break
    for sec in root.iter("sec"):
        t = sec.find("title")
        if t is not None:
            parts.append("## " + txt(t))
        for p in sec.findall("p"):
            s = txt(p)
            if len(s) > 40:
                parts.append(s)
    return "\n\n".join(x for x in parts if x)


def license_of(xml: str) -> str:
    m = re.search(r"<license[^>]*>(.*?)</license>", xml, re.S)
    if m:
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(1))).strip()
    m = re.search(r"(CC BY[^<,;]{0,24}|Creative Commons[^<]{0,48})", xml)
    return m.group(1) if m else "未标注"


def search(query: str, n: int = 10):
    u = EPMC + "search?format=json&pageSize=%d&query=%s" % (n, urllib.parse.quote(query))
    s = get(u)
    if not s:
        return []
    return json.loads(s).get("resultList", {}).get("result", [])


def fetch_pmcid(pmcid: str) -> bool:
    xml = get(EPMC + f"{pmcid}/fullTextXML")
    if not xml or "<article" not in xml[:4000]:
        print(f"  {pmcid}: 没有开放全文 XML", file=sys.stderr)
        return False
    text = jats_to_text(xml)
    if len(text) < 8000:
        print(f"  {pmcid}: 正文太短（{len(text)} 字符），跳过", file=sys.stderr)
        return False
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{pmcid}.md").write_text(text, encoding="utf-8")
    meta = {"source": "Europe PMC fullTextXML", "pmcid": pmcid,
            "title": (text.split("\n")[0][2:200] if text else ""),
            "license": license_of(xml), "chars": len(text),
            "url": f"https://europepmc.org/article/PMC/{pmcid}",
            "retrieved": time.strftime("%Y-%m-%d")}
    (OUT / f"{pmcid}.meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1),
                                            encoding="utf-8")
    print(f"  → papers/biomed/{pmcid}.md  {len(text):,} 字符  许可: {meta['license'][:60]}")
    return True


def main(argv=None) -> int:
    from ask_dao_machine import _console
    _console.setup()
    ap = argparse.ArgumentParser(description="抓开放获取生物医学全文（Europe PMC）")
    ap.add_argument("--pmcid", default=None, help=f"直接指定 PMCID（默认 {DEFAULT_PMCID}）")
    ap.add_argument("--query", default=DEFAULT_QUERY, help="Europe PMC 检索式")
    ap.add_argument("--list", action="store_true", help="只列检索结果，不下载")
    a = ap.parse_args(argv)

    if a.pmcid:
        print(f"取指定 PMCID: {a.pmcid}")
        return 0 if fetch_pmcid(a.pmcid) else 2

    hits = search(a.query)
    print(f"检索命中 {len(hits)} 条：")
    for h in hits:
        print(f"  {h.get('pmcid')} | {h.get('journalTitle','')[:30]:30s} | {(h.get('title') or '')[:70]}")
    if a.list:
        return 0
    for h in [h for h in hits if h.get("pmcid")] :
        if fetch_pmcid(h["pmcid"]):
            return 0
    print("没有可用的开放全文。", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
