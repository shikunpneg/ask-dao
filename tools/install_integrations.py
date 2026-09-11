# -*- coding: utf-8 -*-
"""install_integrations.py — 把问道挂到各宿主上（一份源码，多处安装）。

做三件事：
  1. 安装 SKILL.md 到各宿主的技能目录（内容完全相同，只换路径）：
       Claude Code : <repo>/.claude/skills/ask-dao-machine/SKILL.md
       DSH         : <repo>/.dsh/skills/ask-dao-machine/SKILL.md
       用户级(可选): ~/.claude/skills/... · ~/.dsh/skills/... · ~/.agents/skills/...
  2. 写 <repo>/.mcp.json（Claude Code / Cursor 等按项目读的 MCP 配置）。
  3. 打印 DSH 用的 cordis.yml 片段（MCP client 插件行）。

用法:
  python tools/install_integrations.py            # 装到本仓库（项目级）
  python tools/install_integrations.py --user     # 同时装到用户级目录
  python tools/install_integrations.py --check    # 只检查现状，不写文件
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SRC = HERE / "integrations" / "skill" / "SKILL.md"
NAME = "ask-dao-machine"
DSH_HOME = Path(os.environ.get("DSH_HOME") or (Path.home() / ".dsh"))

SKILL_TARGETS = [
    # .agents/skills 是跨工具约定的位置，DSH 也读它；这份随仓库走，clone 后零配置可用
    ("agents 通用（项目级，入库）", ".agents/skills"),
    ("Claude Code（项目级，本地）", ".claude/skills"),
    ("DSH（项目级，本地）", ".dsh/skills"),
]
USER_TARGETS = [
    ("Claude Code（用户级）", Path.home() / ".claude" / "skills"),
    ("DSH（用户级）", DSH_HOME / "skills"),
    ("agents 通用（用户级）", Path.home() / ".agents" / "skills"),
]

MCP_JSON = {
    "mcpServers": {
        "ask-dao": {
            "command": "python",
            "args": ["-m", "ask_dao_machine", "mcp"],
            "env": {"PYTHONPATH": "src", "PYTHONIOENCODING": "utf-8"},
        }
    }
}

CORDIS_SNIPPET = """# DSH 主机复合（cordis.yml）里加一行，即可把问道注册成模型工具
# 工具会以 mcp__askdao__<tool> 的名字出现在模型侧（与 Claude Code 同款约定）
- id: mcp-ask-dao
  name: '@deepseek-ai/dsh-mcp-client'
  config:
    serverName: askdao
    transport: stdio
    command: python
    args: ['-m', 'ask_dao_machine', 'mcp']
    cwd: <repo 路径>
    env:
      PYTHONPATH: src
      PYTHONIOENCODING: utf-8
    failOnStartupError: true
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="把问道安装进各宿主的技能/MCP 配置")
    ap.add_argument("--user", action="store_true", help="同时装到用户级目录")
    ap.add_argument("--check", action="store_true", help="只检查，不写文件")
    a = ap.parse_args(argv)

    if not SRC.exists():
        print(f"找不到源文件 {SRC}", file=sys.stderr)
        return 2
    body = SRC.read_text(encoding="utf-8")

    targets = [(n, HERE / p) for n, p in SKILL_TARGETS]
    if a.user:
        targets += [(n, p) for n, p in USER_TARGETS]

    print(f"源: {SRC.relative_to(HERE)}（{len(body)} 字符）")
    for label, root in targets:
        dst = Path(root) / NAME / "SKILL.md"
        state = "已安装" if dst.exists() else "未安装"
        if a.check:
            same = dst.exists() and dst.read_text(encoding="utf-8") == body
            print(f"  [{state}{'·一致' if same else ''}] {label}: {dst}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(body, encoding="utf-8")
        print(f"  [已写入] {label}: {dst}")

    mcp_path = HERE / ".mcp.json"
    if a.check:
        print(f"  [{'已存在' if mcp_path.exists() else '未生成'}] MCP 配置: {mcp_path}")
    else:
        if mcp_path.exists():
            try:
                old = json.loads(mcp_path.read_text(encoding="utf-8"))
            except Exception:                                   # noqa: BLE001
                old = {}
            old.setdefault("mcpServers", {}).update(MCP_JSON["mcpServers"])
            mcp_path.write_text(json.dumps(old, ensure_ascii=False, indent=1) + "\n",
                                encoding="utf-8")
        else:
            mcp_path.write_text(json.dumps(MCP_JSON, ensure_ascii=False, indent=1) + "\n",
                                encoding="utf-8")
        print(f"  [已写入] MCP 配置: {mcp_path}")

    print("\nDSH 主机复合片段（复制到 cordis.yml）：\n" + CORDIS_SNIPPET)
    print("验证：python tools/install_integrations.py --check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
