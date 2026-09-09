# -*- coding: utf-8 -*-
"""冒烟测试: 小规模跑通两域引擎 + 出处链完整 + JSON 序列化。"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ask_dao_machine import ProblemMaker  # noqa: E402


def test_math_smoke():
    maker = ProblemMaker()
    ps = maker.run("math", {"N": 60000, "M": 120000})
    assert len(ps.problems) == 25, len(ps.problems)
    ids = [p.id for p in ps.problems]
    assert "A1" in ids and "H4" in ids
    # 出处链完整性: 每条记录都有 motifs/template/judgement/tree
    for p in ps.problems:
        assert p.motifs and p.template and p.judgement
        assert p.tree.get("parent"), p.id
    d = ps.to_dict()
    assert d["domain"] == "math"
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "math.json"
        f.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        assert json.loads(f.read_text(encoding="utf-8"))["problems"]


def test_aesthetics_smoke():
    maker = ProblemMaker()
    ps = maker.run("aesthetics")
    assert len(ps.problems) == 8
    assert all(p.status == "待实验/待评审" for p in ps.problems)
    assert ps.roots[0].id == "A_ROOT"


if __name__ == "__main__":
    test_math_smoke()
    test_aesthetics_smoke()
    print("smoke tests OK")
