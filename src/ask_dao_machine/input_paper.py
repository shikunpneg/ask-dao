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
    """返回 (文本, 用的什么方法)。

    优先级：**pdftotext 优先**，其次 pypdf / PyPDF2，最后内置尽力提取。
    为什么 pdftotext 优先（实测教训）：双栏学术 PDF 上 pypdf 会弄错页序与分栏，
    把标题挤到第 55 行、前 19 行是从第 2 页正文倒着来的；同一篇文件 pdftotext
    把标题放在第 5 行（页眉/DOI 之后）。装上 pypdf 反而变差，所以顺序不能反。
    """
    import shutil
    import subprocess
    if shutil.which("pdftotext"):
        try:
            # 注意(踩过的坑): 必须显式指定 encoding/errors。
            # 中文 Windows 上 locale 默认是 cp936(GBK), 而 pdftotext 输出 UTF-8;
            # 用 text=True 不指定编码时, Python 会在**读取线程**里抛
            # UnicodeDecodeError, 异常不冒泡, 只让 r.stdout 变成 None,
            # 下游 r.stdout.strip() 再抛 AttributeError, 文件被整篇跳过。
            r = subprocess.run(
                ["pdftotext", "-q", "-enc", "UTF-8", str(path), "-"],
                capture_output=True, encoding="utf-8", errors="replace", timeout=180,
            )
            txt = r.stdout or ""
            if txt.strip():
                tag = "pdftotext" if r.returncode == 0 else f"pdftotext(rc={r.returncode})"
                return txt, tag
        except subprocess.TimeoutExpired:
            print(f"[warn] pdftotext 超时(180s): {path.name}", file=sys.stderr)
        except Exception as e:                                # noqa: BLE001
            print(f"[warn] pdftotext 失败: {type(e).__name__} {e}", file=sys.stderr)
    for mod, tag in (("pypdf", "pypdf"), ("PyPDF2", "PyPDF2")):
        try:
            m = __import__(mod)
            Reader = getattr(m, "PdfReader")
            txt = "\n".join((p.extract_text() or "") for p in Reader(str(path)).pages)
            if txt.strip():
                return txt, tag
        except Exception:                                     # noqa: BLE001
            continue
    return _pdf_text_builtin(path), "builtin(尽力提取, 装 pypdf 或在 PATH 放 pdftotext 更稳)"


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

# ── 输出版本化：每篇论文一个目录（按标题），不再互相覆盖 ────────────
_SLUG_BAD = re.compile(r"[^\w\u4e00-\u9fff\u3400-\u4dbf\-]+")
# 明显不是标题的行（期刊页眉、页脚、DOI、纯数字…）
_TITLE_NOISE = re.compile(
    r"^(?:doi|https?://|www\.|arxiv|copyright|©|received|accepted|published|"
    r"open\s+access|original\s+(?:article|research)|research\s+article|"
    r"article|research|review|abstract|keywords?|citation|journal|volume|vol\.|"
    r"page|pp\.|issn|pmid|pmcid|downloaded|licensed|all rights reserved)\b",
    re.I)


def _pdf_meta_title(path: Path) -> str:
    """从 PDF /Title 元数据里取标题（尽力，失败返回空）。"""
    try:
        raw = path.read_bytes()[:400_000]
    except Exception:                                          # noqa: BLE001
        return ""
    m = re.search(rb"/Title\s*\(((?:\\.|[^\\()])*)\)", raw)
    if not m:
        m = re.search(rb"/Title\s*<([0-9A-Fa-f\s]{8,})>", raw)
        if m:
            try:
                hx = bytes.fromhex(re.sub(rb"\s", b"", m.group(1)).decode("ascii"))
                for enc in ("utf-16-be", "utf-8", "latin-1"):
                    try:
                        t = hx.decode(enc).strip()
                        if len(t) >= 8:
                            return t
                    except Exception:                              # noqa: BLE001
                        continue
            except Exception:                                      # noqa: BLE001
                pass
        return ""
    s = re.sub(rb"\\([()\\])", rb"\1", m.group(1))
    for enc in ("utf-8", "latin-1", "utf-16-be"):
        try:
            t = s.decode(enc).strip()
            if len(t) >= 8:
                return t
        except Exception:                                          # noqa: BLE001
            continue
    return ""


_ABSTRACT_LINE = re.compile(r"^\s*(abstract|摘要|1\s*[.．、]?\s*introduction|introduction)\s*$", re.I)
_AUTHOR_LINE = re.compile(r"[·•]|\band\b.*,|,\s*\w+\s*\d\s*$")


def _letters_ratio(s: str) -> float:
    if not s:
        return 0.0
    return sum(c.isalpha() or "\u4e00" <= c <= "\u9fff" for c in s) / len(s)


def _title_score(line: str, following: list[str]) -> int:
    """给一行"像不像标题"打分（学术 PDF 的经验规则，不追求普适）。"""
    s = line.strip()
    n = len(s)
    score = 0
    if 25 <= n <= 170:
        score += 1
    elif n < 15 or n > 220:
        return -99
    if _TITLE_NOISE.match(s):
        return -99
    letters = _letters_ratio(s)
    if letters >= 0.75:
        score += 2
    elif letters < 0.55:
        score -= 3
    if not s.endswith((".", "。", ";", "；")):
        score += 1
    else:
        score -= 2                      # 标题几乎不以句号结尾
    if ":" in s or "：" in s:
        score += 2                      # 学术标题常带冒号副标题
    digits = sum(c.isdigit() for c in s)
    if digits / max(n, 1) > 0.15:
        score -= 2
    # 后面几行里出现 Abstract/Introduction 或作者行 → 这行极可能是标题
    for j, nxt in enumerate(following[:5]):
        t = nxt.strip()
        if _ABSTRACT_LINE.match(t) or _AUTHOR_LINE.search(t):
            score += 3 if j <= 2 else 2
            break
    return score


def derive_title(path: Path, text: str = "") -> str:
    """给这篇输入起个标题（用于输出目录名）。优先级：PDF 元数据 > 正文打分 > 文件名。"""
    if path.suffix.lower() == ".pdf":
        t = _pdf_meta_title(path)
        if t and not _TITLE_NOISE.match(t):
            return re.sub(r"\s+", " ", t)[:200]

    lines = [l for l in (text or "").splitlines()[:80]]
    cand = [(i, l.strip()) for i, l in enumerate(lines) if len(l.strip()) >= 12]
    best, best_score = "", -100
    for k, (i, s) in enumerate(cand):
        if k > 40:                      # 只看前 40 个非空行
            break
        following = [lines[j] for j in range(i + 1, min(i + 6, len(lines)))]
        sc = _title_score(s, following)
        if sc <= best_score:
            continue
        # 标题常折行：若下一非空行也像标题，合并
        merged = s
        if k + 1 < len(cand):
            nxt = cand[k + 1][1]
            nsc = _title_score(nxt, [])
            if (nsc >= 2 and not merged.endswith((".", "。"))
                    and 25 <= len(merged) + len(nxt) <= 200):
                merged = f"{merged} {nxt}"
        best, best_score = merged, sc
    if best and best_score > 0:
        return re.sub(r"\s+", " ", best)[:200]
    return path.stem


def slugify(title: str, maxlen: int = 64) -> str:
    """标题 -> 目录名：保留中英数字与连字符，其余压成 -。"""
    s = _SLUG_BAD.sub("-", title.strip())
    s = re.sub(r"-{2,}", "-", s).strip("-").strip()
    if len(s) > maxlen:
        s = s[:maxlen].rstrip("-")
    return s or "untitled"


def plan_out_dir(base: Path, slug: str, mode: str = "version") -> tuple[Path, int]:
    """决定这次写到哪：mode=version 时同标题再跑就递增 -v2/-v3，不覆盖。"""
    base.mkdir(parents=True, exist_ok=True)
    if mode == "overwrite":
        d = base / slug
        d.mkdir(parents=True, exist_ok=True)
        return d, 1
    d = base / slug
    if not (d / "problems_paper.json").exists() and not (d / "REPORT.md").exists():
        d.mkdir(parents=True, exist_ok=True)
        return d, 1
    v = 2
    while (base / f"{slug}-v{v}").exists():
        v += 1
    d = base / f"{slug}-v{v}"
    d.mkdir(parents=True, exist_ok=True)
    return d, v


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


def mine(text: str, source: str, max_per_type: int = 8, domain: str = "auto",
         n_followups: int = 4, max_total: int = 0) -> list[dict]:
    """三种通用机制 + （可选）领域包。domain: auto | biomed | none

    n_followups: ③结构追问套几问（1–4：范围/反例/机制/定量），控制"问题深度"。
    max_total:   总条数上限（0 = 不限），控制"生成多少问题"。
    """
    out: list[dict] = []
    seen = set()
    counters = {"①作者自陈未解": 0, "②文本张力": 0, "③结构追问": 0}
    followups = FOLLOWUPS[:max(1, min(n_followups, len(FOLLOWUPS)))]

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
        if claim_tag and counters["③结构追问"] < max_per_type * len(followups):
            base = sent[:110]
            for name, tmpl, route in followups:
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
    # ④ 领域包：生物医学 —— 把方法学缺口写成可判形式（不主张世界新）
    use_biomed = domain in ("biomed", "biomedical", "生物医学")
    if domain == "auto":
        try:
            from . import domain_pack_biomed as _bm
            use_biomed = _bm.detect_vocab(text) >= 25
        except Exception:                                      # noqa: BLE001
            use_biomed = False
    if use_biomed:
        try:
            from . import domain_pack_biomed as _bm
            out += _bm.mine(text, source, _sentences(text), max_per_rule=3)
        except Exception as e:                                 # noqa: BLE001
            print(f"[warn] 生物医学包未生效: {e}", file=sys.stderr)
    return out


# ── 主流程 ────────────────────────────────────────────────────────────
def run(paths, out_dir="out/papers", max_per_type: int = 8, quiet=False,
        domain: str = "auto", group: str = "auto", n_followups: int = 4,
        max_total: int = 0, overwrite: bool = False) -> dict:
    base = Path(out_dir)
    files = collect_inputs([Path(p) for p in paths])
    if not files:
        print("没找到可读入的论文文件（支持 .md/.txt/.pdf/.docx/.epub，或传目录）")
        return {"problems": [], "files": []}

    # 先抽第一篇的文本，用它来定标题（单文件时按标题建目录，避免不同论文互相覆盖）
    problems, per_file = [], []
    title, slug, out, version = "", "", base, 1
    for i, f in enumerate(files):
        try:
            text, how = extract_text(f)
        except Exception as e:                                # noqa: BLE001
            print(f"[skip] {f.name}: {type(e).__name__}: {e}")
            per_file.append({"file": str(f), "chars": 0, "method": "error", "problems": 0,
                             "error": f"{type(e).__name__}: {e}"})
            continue
        if i == 0:
            title = derive_title(f, text)
            slug = slugify(title)
            use_group = (group == "title") or (group == "auto" and len(files) == 1)
            if use_group:
                out, version = plan_out_dir(base, slug, "overwrite" if overwrite else "version")
            else:
                out = base
                out.mkdir(parents=True, exist_ok=True)
        got = mine(text, f.name, max_per_type=max_per_type, domain=domain,
                   n_followups=n_followups, max_total=max_total)
        problems += got
        per_file.append({"file": str(f), "chars": len(text), "method": how,
                         "problems": len(got), "title": title or f.stem})
        if not quiet:
            print(f"[{f.name}] {len(text):,} 字符 | 抽取方式={how} | 产出问题 {len(got)} 条")

    if max_total and len(problems) > max_total:
        problems = problems[:max_total]

    n_author = sum(1 for p in problems if p["is_author_stated"])
    n_bm = sum(1 for p in problems if p.get("domain") == "生物医学")
    payload = {
        "domain": "paper",
        "generator": "ask-dao-machine/input_paper.py",
        "title": title,
        "slug": slug,
        "version": version,
        "out_dir": str(out),
        "inputs": [p["file"] for p in per_file],
        "files": [p["file"] for p in per_file],
        "per_file": per_file,
        "params": {"per_type": max_per_type, "domain": domain, "depth_followups": n_followups,
                   "max_total": max_total, "group": group},
        "counts": {"total": len(problems), "author_stated": n_author,
                   "machine_raised": len(problems) - n_author, "biomed_pack": n_bm},
        "roots": [{"id": "PAPER_ROOT", "label": f"论文输入：{len(files)} 个文件"}],
        "problems": problems,
    }
    dst = out / "problems_paper.json"
    dst.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    if not quiet:
        if title:
            print(f"标题：{title}")
        print(f"合计 {len(problems)} 条：作者已提出 {n_author} 条 · 机器新提出 {len(problems)-n_author} 条"
              + (f"（其中生物医学方法学追问 {n_bm} 条）" if n_bm else ""))
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


# 深度档：控制"每类机制产出多少"与"③结构追问套几问"
DEPTHS = {
    "shallow": (3, 2),      # 少量、浅：只问范围/反例
    "normal": (8, 4),       # 默认
    "deep": (20, 4),        # 大量、四问全上
}


def main(argv=None, out_dir="out/papers") -> int:
    from . import ui_console as _console
    _console.setup()
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(__doc__)
        return 2
    import argparse
    ap = argparse.ArgumentParser(
        prog="ask-dao-machine paper",
        description="输入论文（.md/.txt/.pdf/.docx/.epub 或目录），输出问题清单 + 一页人话报告",
        epilog=("例子:\n"
                "  ask-dao-machine paper paper.pdf                      # 按论文标题建目录，不覆盖别篇\n"
                "  ask-dao-machine paper paper.pdf --depth deep         # 多问、四问全上\n"
                "  ask-dao-machine paper paper.pdf --max-total 30       # 只要 30 条\n"
                "  ask-dao-machine paper paper.pdf --per-type 5 --depth shallow\n"
                "  ask-dao-machine paper papers/ --flat                 # 目录输入：平铺到 --out（CI 用法）\n"
                "  产出：problems_paper.json（「作者已提出」与「机器新提出」分开标注）+ REPORT.md\n"),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="论文文件或目录")
    ap.add_argument("--out", default=out_dir, help="输出根目录（默认 out/papers）")
    ap.add_argument("--per-type", type=int, default=None,
                    help="每类机制最多产出多少条（默认按 --depth：shallow 3 / normal 8 / deep 20）")
    ap.add_argument("--depth", choices=sorted(DEPTHS), default="normal",
                    help="问题深度档：shallow（少而浅）/ normal（默认）/ deep（多而全）")
    ap.add_argument("--max-total", type=int, default=0,
                    help="总条数上限（0 = 不限）")
    ap.add_argument("--group", choices=["auto", "title", "flat"], default="auto",
                    help="输出目录组织：auto=单文件按标题建目录、目录输入平铺；"
                         "title=总是按标题；flat=总是平铺到 --out")
    ap.add_argument("--flat", action="store_true",
                    help="等价于 --group flat（平铺到 --out，CI 常用）")
    ap.add_argument("--overwrite", action="store_true",
                    help="同标题重跑时覆盖，而不是递增 -v2/-v3")
    ap.add_argument("--domain", choices=["auto", "biomed", "none"], default="auto",
                    help="领域包：auto=按词表自动判断，biomed=强制生物医学方法学追问，none=只用通用三机制")
    a = ap.parse_args(argv)
    if not a.paths:
        print(__doc__)
        return 2

    d_per, d_fol = DEPTHS[a.depth]
    per_type = a.per_type if a.per_type is not None else d_per
    group = "flat" if a.flat else a.group
    payload = run(a.paths, out_dir=a.out, max_per_type=per_type, domain=a.domain,
                  group=group, n_followups=d_fol, max_total=a.max_total,
                  overwrite=a.overwrite)
    out_used = payload.get("out_dir") or a.out
    per = payload.get("per_file") or []
    if payload.get("problems"):
        from . import output_report as report_mod
        report_mod.main(out_used)                 # 复用一页人话报告（写到实际目录）
        if payload.get("version", 1) > 1:
            print(f"（同标题第 {payload['version']} 版，未覆盖前几版）")
        return 0
    # 一条都没产出：区分"路径不对/格式不支持"（失败）与"文本抽取失败"（可诊断）
    failed = [p for p in per if p.get("method") == "error"]
    if failed or not per:
        print("没有产出任何问题。", file=sys.stderr)
        for p in failed[:5]:
            print(f"  ✗ {Path(p['file']).name}: {p.get('error')}", file=sys.stderr)
        print("  提示：PDF 优先用 pdftotext 或 pip install pypdf；"
              "扫描版 PDF 需先 OCR。", file=sys.stderr)
        return 2
    print("输入文件里没有命中任何机制（信号词太稀薄？试试更长的论文正文，或 --depth deep）。",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
