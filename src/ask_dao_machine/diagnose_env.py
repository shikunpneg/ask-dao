# -*- coding: utf-8 -*-
"""doctor.py — 环境自查 + 参照系（OEIS）获取。

解决两件"劝退"的事：
  1. 跑完 / 跑不动时，一眼看出缺什么（Python 版本、包、数据、输出目录、测试）
  2. OEIS 索引（data/stripped.gz，约 32MB）从哪来 —— 直接给命令，并且**一条命令就能取**
"""
from __future__ import annotations

import gzip
import os
import shutil
import sys
import time
import urllib.request
from pathlib import Path

OEIS_URL = "https://oeis.org/stripped.gz"
MIN_BYTES = 5 * 1024 * 1024          # 比这小说明没下全


def data_dir() -> Path:
    """默认 <repo>/data；不在仓库里时退回 ./data。"""
    here = Path(__file__).resolve()
    for up in here.parents:
        if (up / "pyproject.toml").exists():
            return up / "data"
    return Path.cwd() / "data"


def check() -> int:
    from . import ui_console as _console
    _console.setup()
    ok = True
    print("=" * 76)
    print("ask-dao-machine · 环境自查")
    print("=" * 76)

    v = sys.version_info
    good = v >= (3, 9)
    ok &= good
    print(f"[{'OK ' if good else 'FAIL'}] Python {v.major}.{v.minor}.{v.micro}（需要 ≥3.9）")

    try:
        from .stage_pipeline import ProblemMaker
        maker = ProblemMaker()
        doms = list(maker.list_domains())
        print(f"[OK ] 包已安装，引擎可用；域 {len(doms)} 个：{', '.join(doms)}")
    except Exception as e:                                  # noqa: BLE001
        ok = False
        print(f"[FAIL] 包导入/引擎初始化失败：{e}")
        print("       修复：pip install -e .（或设 PYTHONPATH=src）")

    dd = data_dir()
    idx = dd / "stripped.gz"
    if idx.exists() and idx.stat().st_size >= MIN_BYTES:
        try:
            n = _count_sequences(idx)
            print(f"[OK ] OEIS 参照系：{idx}（{idx.stat().st_size/1024/1024:.1f}MB，序列 {n} 条）")
        except Exception as e:                              # noqa: BLE001
            ok = False
            print(f"[WARN] OEIS 文件存在但读不动：{e}")
            print("       修复：python -m ask_dao_machine data fetch --force")
    else:
        print(f"[-- ] OEIS 参照系缺失：{idx}")
        print("       影响：新颖性门跑不了（N0–N3 分级不会写入），其余引擎照常")
        print("       获取：python -m ask_dao_machine data fetch   （约 32MB，来自 oeis.org）")

    out = Path.cwd() / "out"
    try:
        out.mkdir(parents=True, exist_ok=True)
        probe = out / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        print(f"[OK ] 输出目录可写：{out}")
    except Exception as e:                                  # noqa: BLE001
        ok = False
        print(f"[FAIL] 输出目录不可写：{out}（{e}）")

    try:
        import pytest                                          # noqa: F401
        print("[OK ] pytest 已安装（可跑测试：pytest -q）")
    except Exception:                                       # noqa: BLE001
        print("[-- ] pytest 未安装（跑测试需要：pip install -e \".[dev]\"）")

    print("-" * 76)
    print("建议的下一步：" if ok else "先修上面标 FAIL 的项，然后：")
    print("  1) python -m ask_dao_machine all --out out/demo    # 跑一批（约 30s）")
    print("  2) python -m ask_dao_machine report --out out/demo # 看一页人话汇总")
    return 0 if ok else 1


def _count_sequences(path: Path, limit: int | None = None) -> int:
    n = 0
    with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if line.startswith("A"):
                n += 1
                if limit and n >= limit:
                    break
    return n


def fetch(dest: str | None = None, force: bool = False) -> int:
    from . import ui_console as _console
    _console.setup()
    dd = Path(dest) if dest else data_dir()
    dd.mkdir(parents=True, exist_ok=True)
    dst = dd / "stripped.gz"
    if dst.exists() and dst.stat().st_size >= MIN_BYTES and not force:
        print(f"已存在：{dst}（{dst.stat().st_size/1024/1024:.1f}MB）。加 --force 可重新下载。")
        return 0
    print(f"下载 OEIS 索引：{OEIS_URL} → {dst}（约 32MB，来源 oeis.org）")
    t0 = time.time()
    tmp = dst.with_suffix(".part")
    try:
        with urllib.request.urlopen(OEIS_URL, timeout=60) as r, open(tmp, "wb") as f:
            total = int(r.headers.get("Content-Length") or 0)
            got, last = 0, 0
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
                got += len(chunk)
                if total and got - last > 4 * 1024 * 1024:
                    print(f"  {got/1024/1024:.1f}/{total/1024/1024:.1f}MB "
                          f"({100.0*got/total:.0f}%)", flush=True)
                    last = got
    except Exception as e:                                  # noqa: BLE001
        print(f"下载失败：{e}")
        print("可手动下载后放到：", dst)
        tmp.unlink(missing_ok=True)
        return 1
    if tmp.stat().st_size < MIN_BYTES:
        print(f"下载不完整（{tmp.stat().st_size} 字节），已删除")
        tmp.unlink(missing_ok=True)
        return 1
    shutil.move(str(tmp), str(dst))
    n = _count_sequences(dst)
    print(f"完成：{dst}（{dst.stat().st_size/1024/1024:.1f}MB，序列 {n} 条，用时 {time.time()-t0:.0f}s）")
    print("现在可以跑带新颖性门的全量：python -m ask_dao_machine all --out out/demo")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "fetch":
        raise SystemExit(fetch())
    raise SystemExit(check())
