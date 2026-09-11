# -*- coding: utf-8 -*-
"""paper.py — 输入论文，输出问题（三种机制，两类来源分开标注）

支持的输入格式（零依赖优先，缺库时给明确指引）：
  .md / .txt / .text        直接读
  .docx                     zip + XML（标准库）
  .epub                     zip + (x)html（标准库）
  .pdf                      pypdf / PyPDF2 / pdftotext 任一可用即可；都没有则用内置尽力提取
  目录                      递归收集以上格式

三种机制（诚实标注来源）：
  ① 作者自陈未解   —— 抓 open problem / remains unclear / 尚不明确 / 有待研究 …
                       【作者已经提出】，所以**不算新问题**
  ② 文本张力       —— 抓 然而/但是/却/相反/矛盾/conflicting/yet/whereas 处的分歧
                       → 形式化追问（能否统一？冲突在哪一层？）【作者未提出】
  ③ 结构追问       —— 对文中的"结论句"（所有/等价/单调/上界/收敛/守恒 …）套四类追问
                       （范围 / 反例 / 机制 / 定量）【作者未提出】

用法:
  python -m ask_dao_machine paper <文件或目录...> [--out out/papers]
"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

# ── 信号词 ────────────────────────────────────────────────────────────
OPEN_SIGNALS = [
    (r"open problem", "open problem"), (r"open question", "open question"),
    (r"remains? (unclear|unknown|challenging|elusive|an open)", "remains unclear"),
    (r"unresolved", "unresolved"), (r"not yet (known|understood|clear)", "not yet known"),
    (r"further (research|study|work|investigation)", "further research"),
    (r"future work", "future work"), (r"we leave .{0,20}(open|unanswered)", "left open"),
    (r"尚不明确", "尚不明确"), (r"有待(研究|解决|进一步)", "有待研究"),
    (r"需要进一步(研究|验证|探索)", "需要进一步研究"), (r"至今(尚未|未)(解决|清楚)", "尚未解决"),
    (r"仍未(解决|明确)", "仍未解决"), (r"尚未(解决|明确)", "尚未解决"), (r"有待商榷", "有待商榷"),
]
TENSION_SIGNALS = [
    (r"\bhowever\b", "however"), (r"\bwhereas\b", "whereas"), (r"\byet\b", "yet"),
    (r"\bcontradic\w*", "contradiction"), (r"\bconflict\w*", "conflict"),
    (r"\binconsisten\w*", "inconsistent"), (r"\bon the contrary\b", "on the contrary"),
    (r"然而", "然而"), (r"但是", "但是"), (r"相反", "相反"), (r"矛盾", "矛盾"),
    (r"却(不|并非)", "却不"), (r"与之(相反|不同)", "与之相反"),
]
CLAIM_SIGNALS = [
    (r"\bfor all\b", "for all"), (r"\balways\b", "always"), (r"\bimplies?\b", "implies"),
    (r"\bmonoton\w*", "monotone"), (r"\b(upper|lower) bound\b", "bound"),
    (r"\bconverge\w*", "converge"), (r"\bconserv\w*", "conserved"),
    (r"\bequivalen\w*", "equivalent"), (r"所有", "所有"), (r"任意", "任意"),
    (r"必然", "必然"), (r"单调", "单调"), (r"(上|下)界", "界"), (r"收敛", "收敛"),
    (r"守恒", "守恒"), (r"等价", "等价"), (r"恒(等|成立)", "恒成立"),
]

FOLLOWUPS = [
    ("范围追问", "该结论的成立范围能否扩展（或收紧）到更一般的对象类？边界在哪里？",
     "枚举/反例搜索 + 界证明"),
    ("反例追问", "该结论的例外集有多大、由什么结构刻画？例外是否贴边界（=未收敛）？",
     "枚举 + 例外集结构拟合"),
    ("机制追问", "该结论背后的机制是什么？在什么条件下（参数、噪声、尺度）会失效？",
     "建模仿真 + 参数扫描"),
    ("定量追问", "该结论给出的界是否紧？最坏情形是什么，何时达到？",
     "数值实验 + 紧性证明"),
]

SENT_SPLIT = re.compile(r"(?<=[.。！？!?;；])\s+")


# ── 文本抽取 ──────────────────────────────────────────────────────────
def _docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", "ignore")
    xml = re.sub(r"</w:p>", "\n", xml)
    return re.sub(r"<[^>]+>", "", xml)


def _epub_text(path: Path) -> str:
    out = []
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            if re.search(r"\.(x?html?|htm)$", n, re.I):
                raw = z.read(n).decode("utf-8", "ignore")
                raw = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
                raw = re.sub(r"</(p|div|h\d|li)>", "\n", raw)
                out.append(re.sub(r"<[^>]+>", "", raw))
    return "\n".join(out)


def _pdf_text(path: Path) -> tuple[str, str]:
    """返回 (文本, 用的什么方法)。优先第三方库，其次 pdftotext，最后内置尽力提取。"""
    try:
        from pypdf import PdfReader                          # type: ignore
        return "\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages), "pypdf"
    except Exception:                                        # noqa: BLE001
        pass
    try:
        from PyPDF2 import PdfReader                         # type: ignore
        return "\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages), "PyPDF2"
    except Exception:                                        # noqa: BLE001
        pass
    import shutil
    import subprocess
    if shutil.which("pdftotext"):
        r = subprocess.run(["pdftotext", "-q", str(path), "-"], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout, "pdftotext"
    return _pdf_text_builtin(path), "builtin(尽力提取, 建议装 pypdf 更稳)"


def _pdf_text_builtin(path: Path) -> str:
    """内置尽力提取：解码内容流，取 Tj/TJ 里的字面量字符串。对扫描件无效。

    注意：内容流可能**未压缩**（合法），所以解压失败时要退回原始字节，不能直接跳过。
    """
    import zlib
    raw = path.read_bytes()
    chunks = []
    for m in re.finditer(rb"stream\r?\n(.*?)endstream", raw, re.S):
        data = m.group(1)
        for attempt in ("zlib", "raw"):
            if attempt == "zlib":
                try:
                    data2 = zlib.decompress(data)
                except Exception:                            # noqa: BLE001
                    try:
                        data2 = zlib.decompressobj().decompress(data)   # 截断流
                    except Exception:                        # noqa: BLE001
                        continue
            else:
                data2 = data                                  # 未压缩内容流
            for tm in re.finditer(rb"\((?:\\.|[^\\()])*\)", data2):
                s = tm.group(0)[1:-1]
                s = re.sub(rb"\\([()\\])", rb"\1", s)
                txt = s.decode("latin-1", "ignore")
                if txt.strip():
                    chunks.append(txt)
            if any(c.strip() for c in chunks):
                break
    return " ".join(chunks)


def extract_text(path: Path) -> tuple[str, str]:
    ext = path.suffix.lower()
    if ext in (".md", ".txt", ".text", ".markdown"):
        return path.read_text(encoding="utf-8", errors="ignore"), "plain"
    if ext == ".docx":
        return _docx_text(path), "docx"
    if ext == ".epub":
        return _epub_text(path), "epub"
    if ext == ".pdf":
        return _pdf_text(path)
    raise ValueError(f"不支持的格式: {path.suffix}（支持 .md/.txt/.pdf/.docx/.epub）")


_SKIP_NAMES = {"readme.md", "readme.txt", "license", "license.md"}


def collect_inputs(paths) -> list[Path]:
    """收集输入文件；跳过 README/LICENSE 与下划线开头的文件（目录里的说明不该被当论文）。"""
    files: list[Path] = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            for ext in ("*.md", "*.txt", "*.pdf", "*.docx", "*.epub"):
                for f in sorted(p.rglob(ext)):
                    if f.name.lower() in _SKIP_NAMES or f.name.startswith("_"):
                        continue
                    files.append(f)
        elif p.exists():
            files.append(p)
    return files


# ── 挖掘 ──────────────────────────────────────────────────────────────
def _sentences(text: str):
    for s in SENT_SPLIT.split(re.sub(r"\s+", " ", text)):
        s = s.strip()
        if 40 <= len(s) <= 400:
            yield s


def mine(text: str, source: str, max_per_type: int = 8) -> list[dict]:
    out: list[dict] = []
    seen = set()
    counters = {"①作者自陈未解": 0, "②文本张力": 0, "③结构追问": 0}

    for sent in _sentences(text):
        low = sent.lower()

        # ① 作者自陈未解（作者已提出）
        for pat, tag in OPEN_SIGNALS:
            if re.search(pat, low) and counters["①作者自陈未解"] < max_per_type:
                key = ("①", sent[:80])
                if key in seen:
                    continue
                seen.add(key)
                counters["①作者自陈未解"] += 1
                out.append({
                    "id": f"PA{counters['①作者自陈未解']:02d}",
                    "source": source, "type": "①作者自陈未解", "is_author_stated": True,
                    "signal": tag, "evidence": sent,
                    "statement": f"作者自陈的未解点（信号：「{tag}」）：{sent}",
                    "route": "文献/作者自述（机器不判新）",
                    "status": "开放(作者已提出)",
                })
                break

        # ② 文本张力（作者未提出）
        for pat, tag in TENSION_SIGNALS:
            if re.search(pat, low) and counters["②文本张力"] < max_per_type:
                key = ("②", sent[:80])
                if key in seen:
                    continue
                seen.add(key)
                counters["②文本张力"] += 1
                out.append({
                    "id": f"PB{counters['②文本张力']:02d}",
                    "source": source, "type": "②文本张力", "is_author_stated": False,
                    "signal": tag, "evidence": sent,
                    "statement": f"文中出现「{tag}」处的分歧：{sent[:120]}\n"
                                 f"→ 追问：这两侧能否在某个前提下统一？冲突落在哪一层"
                                 f"（定义 / 前提 / 判定标准 / 尺度）？",
                    "route": "概念分析 + 形式化缺口",
                    "status": "悬置(开放)",
                })
                break

        # ③ 结构追问（作者未提出）：对"结论句"套四类追问
        claim_tag = None
        for pat, tag in CLAIM_SIGNALS:
            if re.search(pat, low):
                claim_tag = tag
                break
        if claim_tag and counters["③结构追问"] < max_per_type * len(FOLLOWUPS):
            base = sent[:110]
            for name, tmpl, route in FOLLOWUPS:
                key = ("③", name, base[:60])
                if key in seen:
                    continue
                seen.add(key)
                counters["③结构追问"] += 1
                out.append({
                    "id": f"PC{counters['③结构追问']:02d}",
                    "source": source, "type": f"③结构追问·{name}", "is_author_stated": False,
                    "signal": claim_tag, "evidence": sent,
                    "statement": f"针对文中结论「{base}…」的{name}：{tmpl}",
                    "route": route,
                    "status": "悬置(开放)",
                })
    return out


# ── 主流程 ────────────────────────────────────────────────────────────
def run(paths, out_dir="out/papers", max_per_type: int = 8, quiet=False) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    files = collect_inputs([Path(p) for p in paths])
    if not files:
        print("没找到可读入的论文文件（支持 .md/.txt/.pdf/.docx/.epub，或传目录）")
        return {"problems": [], "files": []}

    problems, per_file = [], []
    for f in files:
        try:
            text, how = extract_text(f)
        except Exception as e:                                # noqa: BLE001
            print(f"[skip] {f.name}: {e}")
            per_file.append({"file": str(f), "chars": 0, "method": "error", "problems": 0,
                             "error": str(e)})
            continue
        got = mine(text, f.name, max_per_type=max_per_type)
        problems += got
        per_file.append({"file": str(f), "chars": len(text), "method": how, "problems": len(got)})
        if not quiet:
            print(f"[{f.name}] {len(text):,} 字符 | 抽取方式={how} | 产出问题 {len(got)} 条")

    n_author = sum(1 for p in problems if p["is_author_stated"])
    payload = {
        "domain": "paper",
        "generator": "ask-dao-machine/paper.py",
        "files": [p["file"] for p in per_file],
        "per_file": per_file,
        "counts": {"total": len(problems), "author_stated": n_author,
                   "machine_raised": len(problems) - n_author},
        "roots": [{"id": "PAPER_ROOT", "label": f"论文输入：{len(files)} 个文件"}],
        "problems": problems,
    }
    dst = out / "problems_paper.json"
    dst.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    if not quiet:
        print(f"\n合计 {len(problems)} 条：作者已提出 {n_author} 条 · 机器新提出 {len(problems)-n_author} 条")
        print(f"→ {dst}")
    return payload


def pr_comment(payload: dict, limit: int = 8) -> str:
    """给 GitHub Action 用的 PR 评论正文（Markdown）。"""
    c = payload.get("counts", {})
    L = ["## 论文 → 问题（自动生成）", "",
         f"从 {len(payload.get('files') or [])} 个文件里产出 **{c.get('total', 0)}** 条问题："
         f"其中**作者已提出 {c.get('author_stated', 0)}** 条（不算新）、"
         f"**机器新提出 {c.get('machine_raised', 0)}** 条。", ""]
    new = [p for p in payload.get("problems", []) if not p.get("is_author_stated")]
    for p in new[:limit]:
        L.append(f"- **[{p['type']} {p['id']}]** {p['statement'].splitlines()[0]}")
        L.append(f"  - 出处：`{p['source']}`　判定路由：{p['route']}")
    if len(new) > limit:
        L.append(f"- …还有 {len(new) - limit} 条，见构建产物 `problems_paper.json` / `REPORT.md`")
    L += ["", "> 「作者已提出」与「机器新提出」分开统计：前者是作者自己写的未解点，不算新问题；"
              "世界新问题（N3）至今为 0。"]
    return "\n".join(L)


def main(argv=None, out_dir="out/papers") -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(__doc__)
        return 2
    payload = run(argv, out_dir=out_dir)
    per = payload.get("per_file") or []
    if payload.get("problems"):
        from . import report as report_mod
        report_mod.main(out_dir)                    # 复用一页人话报告
        return 0
    # 一条都没产出：区分"路径不对/格式不支持"（失败）与"文件为空"（空结果）
    failed = [p for p in per if p.get("method") == "error"]
    if failed or not per:
        print("没有产出任何问题：请检查路径是否存在、格式是否支持（.md/.txt/.pdf/.docx/.epub）。",
              file=sys.stderr)
        return 2
    print("输入文件里没有命中任何机制（信号词太稀薄？试试更长的论文正文）。", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
