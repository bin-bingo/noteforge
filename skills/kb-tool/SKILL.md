# kb-tool OpenClaw Skill

name: kb-tool
version: 1.0.0
description: 个人知识库构建工具 - URL/图片 → Markdown 笔记
author: 灵虾
license: MIT

triggers:
  - pattern: "^kb\\s+(.+)$"
    action: process
  - pattern: "^/kb\\s+(.+)$"
    action: process

config:
  llm_model: "default"  # 复用 OpenClaw 配置
  output_dir: "~/kb/"
  mode: "fidelity"  # fidelity | concise | raw
  sync_to_feishu: true

permissions:
  - exec: "kb"
  - filesystem: "read:~/kb/, write:~/kb/"
  - feishu: "doc.write, drive.upload"
