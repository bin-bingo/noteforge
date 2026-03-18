# NoteForge 🦐

> **扔进材料，输出笔记。** 零配置的个人知识库构建工具。

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)]

## 🎯 功能一览

| 功能 | 状态 | 说明 |
|------|------|------|
| 🔗 文章 URL → 笔记 | ✅ 可用 | trafilatura 提取正文 + AI 旁注 |
| 🎬 YouTube 视频 → 笔记 | ✅ 可用 | yt-dlp 字幕提取 + LLM 总结 |
| 🎬 B 站/抖音 视频 → 笔记 | ✅ 可用 | 支持字幕 + Whisper fallback |
| 📸 OCR 图片识别 | ✅ 可用 | RapidOCR + LLM 校错 |
| 📁 批量处理 | ✅ 可用 | 支持多个 URL/文件批量处理 |
| 🐚 Shell 补全 | ✅ 可用 | Bash / Zsh / Fish |

## 🚀 快速开始

### 安装

```bash
# 核心功能（<50MB）
pip install noteforge

# 完整功能（OCR + 视频）
pip install 'noteforge[all]'
```

### 使用示例

```bash
# 文章链接提炼
nf https://example.com/article

# 输出到文件
nf https://example.com/article -o note.md

# 图片 OCR
nf /path/to/image.png

# 视频链接
nf https://www.bilibili.com/video/BV1xx411c7mD

# 批量处理
nf batch url1.com url2.com url3.com
```

## 📦 安装选项

```bash
# 核心功能
pip install noteforge

# +OCR 功能（~500MB）
pip install 'noteforge[ocr]'

# +视频功能（~60MB）
pip install 'noteforge[video]'

# 全部功能
pip install 'noteforge[all]'
```

## 🔧 配置

```bash
# 查看配置
nf config show

# 设置默认模型
nf config set llm.api_model anthropic/claude-sonnet-4

# 设置 API Key（可选）
export OPENROUTER_API_KEY="sk-or-..."
```

## 📚 文档

- [用户指南](USER_GUIDE.md) - 详细使用说明
- [产品规划](docs/PRODUCT_PLAN_v1.md) - 产品定义与愿景
- [技术架构](docs/ARCHITECTURE_v2.md) - 技术实现细节
- [开发报告](reports/phase3_dev_report.md) - 开发进度与成果

## 🎯 核心特性

- **智能路由**: 自动识别输入类型（URL/文件/目录/视频）
- **原文优先**: 保留完整信息，AI 旁注帮助定位
- **模块化**: 核心 50MB 起步，按需安装组件
- **零配置**: 开箱即用，默认配置适合大多数场景
- **多模式**: fidelity（原文 + 旁注）/ concise（提炼）/ raw（纯原文）

## 🛠️ 技术栈

- **CLI**: Typer (类型安全，自动生成帮助)
- **文章提取**: trafilatura (最快最准)
- **OCR 引擎**: RapidOCR (中文优化)
- **视频处理**: yt-dlp + Whisper
- **LLM**: OpenRouter / OpenClaw (多模型支持)
- **输出格式**: Markdown + YAML frontmatter

## 📊 项目状态

- ✅ Phase 1: 调研与产品规划 (100%)
- ✅ Phase 2: PoC 原型验证 (100%)
- ✅ Phase 3: 核心开发 (100%)
- 🔄 Phase 4: 测试与发布 (进行中)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📝 License

MIT License - 详见 [LICENSE](LICENSE)

---

*NoteForge v1.0.0 — 2026-03-18*
