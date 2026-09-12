# -*- coding: utf-8 -*-
"""tools/research/p_B_deep.py — P-B 深扫 S2 广义Collatz停时(扩展 Q 到更多, 看是否单调爬升)
用于支撑/反对 P-A.A3 的子命题2(模型/有界性)
"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from ask_dao_machine import sparse_engine as se


def main():
    out = []
    for p in (3, 5, 7):
        for Q in (11, 21, 31, 41, 51, 71):
            mx = max(se.max_stop(p, q) for q in range(1, Q + 1, 2))
            out.append((p, Q, mx))
            print(f"p={p} Q<={Q} 最大停时={mx}")
    print("趋势(单调爬升吗?)")
    for p in (3, 5, 7):
        seq = [v for pp, _, v in out if pp == p]
        mono = all(seq[i + 1] >= seq[i] for i in range(len(seq) - 1))
        print(f"  p={p} 序列={seq} 单调↑={mono}")
    Path("out/demo/s2_deep.json").write_text(
        __import__("json").dumps([{"p": pp, "Q": qq, "max_stop": vv} for pp, qq, vv in out],
                                 ensure_ascii=False, indent=1),
        encoding="utf-8")


if __name__ == "__main__":
    main()
