# -*- coding: utf-8 -*-
"""tools/run_resident.py — 常驻长跑总控: 三链路轮转, 用满核, 无超时

  链路A(扫描):   all_domains_engine + parallel_factory   —— Pool 满核
  链路B(融合):   field_fusion + deep_fusion + fusion_territories
  链路C(想象):   browser_mass_search --quick + word_fusion + word_understand + imagination_sentence
                —— POOL_WORKERS=6, 每轮先刷经验语料(词条通道本地秒级)
  引导步骤(首次): browser_mass_search (无 --quick) 全量搜索通道, 约 5-6h, 可跳过

设计: 三条链路**串行轮转**(不是线程+Pool, 避免 Windows spawn 下 Pool 互相阻塞)。
每轮想象链路设 POOL_WORKERS=6(不抢扫描算力), 扫描链路满 20 核。
每 5 分钟过 OEIS 门。主进程永不退出。

首次启动可选跑全量浏览器搜索(搜索通道, 开 Edge 搜 6642 组合, 约 5-6h),
之后每轮只跑 --quick 词条通道(本地缓存, 秒级)。
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
TOOLS = HERE / "tools"


def run(cmd, tag, env_extra=None, timeout_round=3600, extra_args=None):
    """跑一个链路工具。

    注意(踩过的坑): 这里**不能**用 subprocess.run(capture_output=True)。
    子进程链会拉起 Edge(selenium), Edge 会继承 stdout 管道句柄; 子进程退出后
    管道仍不 EOF, 父进程的 communicate() 就永久阻塞 —— 整个常驻总控会卡死在
    某一轮且 CPU≈0。改为直接把子进程输出重定向到日志文件, 不建管道。
    """
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    cmd_parts = [sys.executable, str(TOOLS / cmd)]
    if extra_args:
        cmd_parts.extend(extra_args)
    print(f"[{tag}] 启动 {' '.join(cmd_parts[-3:])}", flush=True)
    t0 = time.time()
    log_path = HERE / "out" / "resident_children.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(log_path, "ab") as lf:
            lf.write(f"\n===== [{tag}] {' '.join(cmd_parts[-3:])} @ {time.strftime('%F %T')} =====\n"
                     .encode("utf-8"))
            lf.flush()
            r = subprocess.run(cmd_parts, timeout=timeout_round,
                               stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                               env=env)
        dt = time.time() - t0
        print(f"[{tag}] 完成 {dt:.0f}s rc={r.returncode}", flush=True)
        with open(log_path, "ab") as lf:
            lf.write(f"----- [{tag}] rc={r.returncode} {dt:.0f}s -----\n".encode("utf-8"))
        return r.returncode
    except subprocess.TimeoutExpired:
        print(f"[{tag}] 工具超时({timeout_round}s)被杀, 总控继续", flush=True)
        return -1


GUIDE_FLAG_FILE = HERE / "data" / ".browser_search_done"


def main():
    print("=" * 90, flush=True)
    print("常驻长跑总控 · 三链路轮转 · 用满核 · 无超时", flush=True)
    print("=" * 90, flush=True)

    # 引导步骤(首次): 全量浏览器搜索(搜索通道, 约 5-6h)
    if not GUIDE_FLAG_FILE.exists():
        print("\n[引导] 首次启动: 全量浏览器搜索通道可用(开 Edge 搜 6642 组合词, 约 5-6h)", flush=True)
        print("        完成后后续轮次只跑 --quick 词条通道(本地秒级)。", flush=True)
        print("        跳过: 在后面 10 秒内按 Ctrl+C 即可, 之后每轮只跑本地词条通道。", flush=True)
        print("        启动: 不操作, 10 秒后自动开始全量浏览器搜索。", flush=True)
        print("        开始倒计时...", end="", flush=True)
        for _ in range(10):
            print(".", end="", flush=True)
            time.sleep(1)
        print("\n[引导] 开始全量浏览器搜索...", flush=True)
        run("browser_mass_search.py", "引导·全量浏览器搜",
            timeout_round=21600)  # 6h 超时(6642 组合约 5-6h)
        GUIDE_FLAG_FILE.write_text("done", encoding="utf-8")
        print("[引导] 全量浏览器搜索完成, 后续轮次只跑词条通道。", flush=True)

    round_no = 0
    while True:
        round_no += 1
        print(f"\n########## ROUND {round_no} ##########", flush=True)

        # 链路A: 扫描(满核)
        run("all_domains_engine.py", f"R{round_no}·A扫描", timeout_round=2400)
        run("parallel_factory.py", f"R{round_no}·A工厂", timeout_round=2400)

        # 链路B: 融合
        for f in ("field_fusion.py", "deep_fusion.py", "fusion_territories.py"):
            run(f, f"R{round_no}·B融合·{f.split('_')[0]}", timeout_round=1800)

        # 链路C: 想象(限核6, 不抢扫描)
        # 每轮先刷新经验语料(--quick 词条通道: 本地缓存, 秒级)
        run("browser_mass_search.py", f"R{round_no}·C经验语料",
            env_extra=None, timeout_round=600, extra_args=["--quick"])
        for f in ("word_fusion.py", "word_understand.py", "imagination_sentence.py"):
            run(f, f"R{round_no}·C想象·{f.split('_')[0]}",
                env_extra={"POOL_WORKERS": "6"}, timeout_round=1800)

        # 每轮结束过 OEIS 门
        run("oeis_batch_gate.py", f"R{round_no}·OEIS门", timeout_round=1800)

        print(f"\n[ROUND {round_no}] 全部链路完成, 下一轮", flush=True)
        time.sleep(2)


if __name__ == "__main__":
    main()
