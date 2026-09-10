# -*- coding: utf-8 -*-
"""tools/run_resident.py — 常驻长跑总控: 三条链路并行, 无超时, 用满核

  链路A(扫描):   all_domains_engine + parallel_factory   —— 用满 Pool(20)
  链路B(融合):   field_fusion + deep_fusion + fusion_territories
  链路C(想象):   word_fusion + word_understand + imagination_sentence  —— 用满 Pool(20)

三条链路各由一个后台线程驱动, 每轮内部再调用工具(工具内部 Pool 用满核)。
每轮结束自动过 OEIS 门。
主进程永不退出(无限 while)。工具单轮有超时保护(防止个别工具卡死), 但总控不设整体超时。
"""
import json
import multiprocessing as mp
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
TOOLS = HERE / "tools"


def run(cmd, tag, timeout_round=3600):
    print(f"[{tag}] 启动 {cmd}", flush=True)
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, str(TOOLS / cmd)], timeout=timeout_round,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        dt = time.time() - t0
        print(f"[{tag}] 完成 {dt:.0f}s rc={r.returncode}", flush=True)
        if r.returncode != 0:
            print(f"[{tag}] stderr: {(r.stderr or '')[-400:]}", flush=True)
        return r.returncode
    except subprocess.TimeoutExpired:
        print(f"[{tag}] 工具超时({timeout_round}s)被杀, 链路继续", flush=True)
        return -1


def chain(name, cmds, interval=2):
    """一条链路: 循环执行其命令, 永不退出。"""
    round_no = 0
    while True:
        round_no += 1
        for cmd in cmds:
            run(cmd, f"{name}·R{round_no}", timeout_round=2400)
        time.sleep(interval)


def main():
    mp.set_start_method("spawn", force=True)
    print("=" * 90, flush=True)
    print("常驻长跑总控 · 三条链路并行 · 用满 20 核 · 无超时", flush=True)
    print(f"核数 {mp.cpu_count()}", flush=True)
    print("=" * 90, flush=True)

    chains = [
        ("扫描", ["all_domains_engine.py", "parallel_factory.py"]),
        ("融合", ["field_fusion.py", "deep_fusion.py", "fusion_territories.py"]),
        ("想象", ["word_fusion.py", "word_understand.py", "imagination_sentence.py"]),
    ]
    # 每轮结束后统一过 OEIS 门(独立线程)
    threads = []
    for name, cmds in chains:
        t = threading.Thread(target=chain, args=(name, cmds), daemon=True)
        t.start()
        threads.append(t)
        print(f"[总控] {name} 链路已启动", flush=True)

    # OEIS 门: 周期性地把新产出过门(每 5 分钟一次)
    def oeis_loop():
        while True:
            time.sleep(300)
            run("oeis_batch_gate.py", "OEIS门", timeout_round=1800)
    threading.Thread(target=oeis_loop, daemon=True).start()

    print("[总控] 所有链路已启动, 主进程常驻。Ctrl-C 停止。", flush=True)
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("[总控] 收到中断, 退出", flush=True)


if __name__ == "__main__":
    main()
