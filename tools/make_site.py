"""从 tools/site/home.html 生成最终首页 docs/index.html.

占位符:
  __TITLE__         页面标题
  __CURATED_JSON__  分级展示数据（K1/K2/K3/想象路/跨域/复核/负结果）

数据源优先级:
  1. tools/site/problems_curated.json —— 由 tools/build_site_problems.py 从
     out/demo/*.json（各域问题、harness 裁决、grown/derived 母题、张力、想象路）
     整理出的"分级 + 问题/命题形态"数据（入库，保证新克隆也能重建首页）
  2. 若它不存在，退回只含原始问题清单的 tools/site/problems_snapshot.json（兼容旧结构）
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "tools" / "site" / "home.html"
OUT = ROOT / "docs" / "index.html"
CURATED = ROOT / "tools" / "site" / "problems_curated.json"
LEGACY = ROOT / "tools" / "site" / "problems_snapshot.json"

TITLE = "问道 · ask-dao-machine —— 一台知识发现机器"


def _legacy_to_curated(rows):
    """旧的扁平问题快照 → 单层 K1 结构，保证模板仍能渲染。"""
    items = []
    for i, r in enumerate(rows):
        items.append({
            "tier": "K1", "domain": r.get("domain") or "未分类",
            "id": r.get("id") or f"Q{i+1}",
            "display": r.get("statement", ""), "claim": r.get("statement", ""),
            "evidence": r.get("evidence", ""), "status": r.get("status", ""),
            "cls": "num", "route": r.get("judge_route", "—"), "edge": "",
            "src": "problems_snapshot.json",
        })
    return {"counts": {}, "tiers": [
        {"key": "K1", "name": "K1 · 提出的问题", "en": "NEW PROBLEMS",
         "desc": "把困惑/数据改造成可判的问题。"}], "items": items}


def load_curated():
    if CURATED.exists():
        print("数据源:", CURATED.name)
        return json.loads(CURATED.read_text(encoding="utf-8"))
    if LEGACY.exists():
        print("数据源: 旧快照", LEGACY.name)
        return _legacy_to_curated(json.loads(LEGACY.read_text(encoding="utf-8")))
    print("! 找不到分级数据，问题区将为空:", CURATED, "/", LEGACY)
    return {"counts": {}, "tiers": [], "items": []}


def main():
    html = TPL.read_text(encoding="utf-8")
    data = load_curated()
    payload = json.dumps(data, ensure_ascii=False)
    html = html.replace("__TITLE__", TITLE)
    html = html.replace("__CURATED_JSON__", payload)
    for ph in ("__CURATED_JSON__", "__PROBLEMS_JSON__"):     # 兜底：残留占位不炸 JS
        if ph in html:
            html = html.replace(ph, "[]" if ph == "__PROBLEMS_JSON__" else "{}")
    OUT.write_text(html, encoding="utf-8")
    n = len(data.get("items") or [])
    print(f"wrote {OUT} {len(html)} chars; {n} 条分级条目; "
          f"{len(data.get('tiers') or [])} 个分级")
    print("计数:", data.get("counts"))


if __name__ == "__main__":
    main()
