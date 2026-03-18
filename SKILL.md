# kb-tool Skill

## 触发条件

用户发送以下内容时激活此 skill：

- **文章 URL**：任何网页链接（非视频网站）
- **视频 URL**：YouTube / Bilibili / 抖音 / Vimeo 链接
- **文件路径**：本地 PDF、Markdown、文本文件
- **关键词**：用户说"提取文章"、"总结这个链接"、"生成笔记"等

## 使用方式

### 方式一：直接命令

用户发送链接时，直接执行：

```bash
kb "<url>" -o ~/notes/output.md
```

### 方式二：智能处理

```bash
# 自动识别输入类型并处理
kb "<url>"

# 视频链接（自动走视频管线）
kb "https://www.youtube.com/watch?v=..."

# 文章链接（自动走文章管线）
kb "https://example.com/article"
```

### 方式三：带选项处理

```bash
# 快速模式（跳过 AI 旁注）
kb "<url>" --no-annotations

# 纯原文
kb "<url>" --mode raw

# 指定输出位置
kb "<url>" -o /path/to/output.md
```

## 输出

kb-tool 输出结构化 Markdown，包含：
- YAML frontmatter（元数据）
- 内容摘要（AI 生成）
- 完整原文或字幕
- 结构化旁注（要点、数据、待读）

## 配置要求

- 环境变量 `OPENROUTER_API_KEY` 必须设置
- 视频处理需要 `yt-dlp` 已安装

## 错误处理

- URL 访问失败 → 返回友好错误提示
- 无字幕的视频 → 告知用户原因并建议替代方案
- API Key 缺失 → 提示设置方法
- 所有错误不中断对话流

## 与 OpenClaw 集成

在 OpenClaw 中注册为 skill 后：
1. 用户发送链接 → 自动检测 → 调用 kb-tool
2. 结果以 Markdown 消息回复
3. 可选保存到飞书文档或本地笔记

## 示例交互

```
用户: https://paulgraham.com/greatwork.html

助手: 正在提取文章...
     ✓ 完成！已生成笔记（含 AI 旁注）
     
     [输出完整的 Markdown 笔记内容]
```

```
用户: https://www.youtube.com/watch?v=xxx

助手: 正在提取视频字幕...
     正在生成学习笔记...
     ✓ 完成！
     
     [输出视频学习笔记]
```
