# kb-tool 用户指南

## 快速开始

### 安装
```bash
# 核心功能（<50MB）
pip install kb-tool

# 完整功能（OCR + 视频）
pip install 'kb-tool[all]'
```

### 配置
```bash
# 设置 API Key（可选，使用 OpenClaw 默认模型则不需要）
export OPENROUTER_API_KEY="sk-or-..."

# 查看配置
kb config show

# 设置默认模型
kb config set llm.api_model anthropic/claude-sonnet-4
```

## 使用示例

### 1. 文章链接提炼
```bash
# 基础用法
kb https://mp.weixin.qq.com/s/xxx

# 输出到文件
kb https://example.com/article -o note.md

# 使用简洁模式
kb https://example.com/article --mode=concise

# 纯原文（无 AI 旁注）
kb https://example.com/article --mode=raw
```

### 2. 多图 OCR 识别
```bash
# 单张图片
kb /path/to/image.png

# 多张图片
kb image1.png image2.png image3.png

# 输出到指定目录
kb /path/to/images/ -d ~/kb/ocr-output/
```

### 3. 视频链接提炼
```bash
# B 站视频
kb https://www.bilibili.com/video/BV1xx411c7mD

# YouTube 视频（需要代理）
kb https://www.youtube.com/watch?v=xxx

# 带字幕提取
kb https://www.bilibili.com/video/BV1xx411c7mD --mode=fidelity
```

### 4. 批量处理
```bash
# 批量处理多个 URL
kb batch url1.com url2.com url3.com

# 批量处理目录
kb batch /path/to/articles/

# 指定输出目录
kb batch url1.com url2.com -d ~/kb/output/
```

## 输出格式

### 默认输出（Fidelity 模式）
```markdown
---
title: "文章标题"
source: "https://example.com"
type: article
created: 2026-03-18
tags: ["标签 1", "标签 2"]
---

# 文章标题

> 📝 **摘要**：AI 生成的 3 句话摘要

---

## 原文

[文章完整内容]

---

> 💡 **要点**
> - 要点 1
> - 要点 2

> 📊 **关键数据**
> - 数据 1
> - 数据 2

> 📖 **待读**
> - 这段值得精读
```

### 简洁模式（Concise）
只保留 AI 提炼的要点，适合快速浏览。

### 纯原文模式（Raw）
只保留原文，不进行任何处理。

## 高级用法

### 自定义 LLM 模型
```bash
kb https://example.com --model anthropic/claude-sonnet-4
```

### 关闭 AI 旁注
```bash
kb https://example.com --no-annotations
```

### 详细模式
```bash
kb https://example.com --verbose
```

## 故障排除

### API Key 错误
```
错误：LLM 错误：Invalid API key
解决：检查 OPENROUTER_API_KEY 环境变量
```

### 微信文章无法提取
```
解决：微信文章需要 JavaScript 渲染，自动使用 Playwright 兜底
确保已安装：pip install playwright
playwright install chromium
```

### B 站视频需要 Cookies
```
解决：复制浏览器的 cookies.txt 到 ~/.kb/cookies.txt
或使用浏览器插件导出 cookies
```

## 更多信息

- GitHub: https://github.com/kb-tool/kb-tool
- 问题反馈：https://github.com/kb-tool/kb-tool/issues
- 文档：https://kb-tool.readthedocs.io/
