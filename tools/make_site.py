"""从 tools/site/home.html 生成最终首页 docs/index.html.
占位符: __TITLE__ __PROBLEMS_JSON__.
问题数据源: out/demo/parallel_factory.json (UTF-8);
  仓库里没有 out/ 时（out/ 被 .gitignore 忽略），回退到 tools/site/problems_snapshot.json，
  这样新克隆的仓库也能重新生成首页。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "tools" / "site" / "home.html"
OUT = ROOT / "docs" / "index.html"
PRIMARY = ROOT / "out" / "demo" / "parallel_factory.json"
SNAPSHOT = ROOT / "tools" / "site" / "problems_snapshot.json"

TITLE = "问道 · ask-dao-machine —— 一台知识发现机器"


def load_problems():
    src = PRIMARY if PRIMARY.exists() else SNAPSHOT
    if not src.exists():
        print("! 找不到问题数据源，首页问题区将为空:", PRIMARY, "/", SNAPSHOT)
        return []
    with open(src, encoding="utf-8") as f:
        rows = json.load(f)
    if src == SNAPSHOT:            # 快照已是成品格式
        print("数据源: 快照", src.name)
        return rows
    print("数据源:", src)
    probs = []
    for i, r in enumerate(rows):
        ev = r.get("evidence") or {}
        parts = []
        if isinstance(ev, dict):
            if ev.get("count"):
                parts.append(f"例外 {ev['count']} 个")
            if ev.get("exceptions"):
                parts.append("前几个: " + ", ".join(map(str, ev["exceptions"][:6])))
            if ev.get("last"):
                parts.append(f"最后例外 {ev['last']}")
        elif ev:
            parts.append(str(ev))
        dom = r.get("domain", "")
        param = r.get("param")
        probs.append({
            "id": f"{dom}/{param}" if dom and param is not None else (dom or f"Q{i+1}"),
            "domain": dom,
            "type": r.get("type", ""),
            "statement": r.get("statement", ""),
            "evidence": " · ".join(parts),
            "judge_route": r.get("judge_route", "—"),
            "status": r.get("status", ""),
        })
    return probs


def main():
    html = TPL.read_text(encoding="utf-8")
    probs = load_problems()
    probs_json = json.dumps(probs, ensure_ascii=False)
    html = html.replace("__TITLE__", TITLE)
    html = html.replace("__PROBLEMS_JSON__", probs_json)
    # 安全：若有残留占位则回退为空数组，避免 JS 崩溃
    if "__PROBLEMS_JSON__" in html:
        html = html.replace("__PROBLEMS_JSON__", "[]")
    OUT.write_text(html, encoding="utf-8")
    print("wrote", OUT, len(html), "bytes;", len(probs), "problems")


if __name__ == "__main__":
    main()
