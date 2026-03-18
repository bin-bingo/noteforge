# kb-tool 任务分解

## Phase 1: 调研与产品规划 ✅ 完成

| # | 任务 | 状态 | 产出 |
|---|---|---|---|
| 1.1 | 竞品调研 | ✅ | 17KB 竞品报告 |
| 1.2 | OCR 技术方案 | ✅ | PaddleOCR → rapidocr |
| 1.3 | 系统架构设计 | ✅ | 15KB 架构文档 |
| 1.4 | 产品定义 v4.0 | ✅ | 飞书文档 |
| 1.5 | 管线技术方案评估 | ✅ | 四管线深度评估 |

## Phase 2: PoC 原型 ✅ 完成

| # | 任务 | 状态 | 产出 |
|---|---|---|---|
| 2.1 | 项目骨架搭建 | ✅ | 14个 .py 文件, ~1800行 |
| 2.2 | 文章管线 | ✅ | trafilatura + Playwright fallback |
| 2.3 | OCR 管线 | ✅ | RapidOCR 集成 |
| 2.4 | 视频管线 | ✅ | yt-dlp + ffmpeg |
| 2.5 | 智能路由 | ✅ | 微信检测、视频文件、混合输入 |
| 2.6 | 全流程测试 | ✅ | 6/7 通过 |

## Phase 3: 核心开发（进行中）

| # | 任务 | 状态 | 产出 |
|---|---|---|---|
| 3.1 | 安装包配置（pip install -e .） | ✅ | pyproject.toml 完善，`kb` 命令可用 |
| 3.2 | CLI 入口完善 | ✅ | --version, config show/set, 友好错误提示 |
| 3.3 | 管线参数统一 | ✅ | generate_annotations 统一命名 |
| 3.4 | 真实 URL 测试 | ✅ | 3 个 URL 测试通过 |
| 3.5 | Whisper fallback 验证 | ✅ | 函数可用，ImportError 处理正确 |
| [ ] | OpenClaw Skill 集成 | | |
| [ ] | 飞书文档同步 | | |
| [ ] | 批量处理 | | |
| [ ] | 用户文档 | | |

## Phase 4: 测试与发布（待规划）

- [ ] 端到端测试（10+ 真实场景）
- [ ] README + 用户指南
- [ ] v1.0 发布（GitHub Release）
