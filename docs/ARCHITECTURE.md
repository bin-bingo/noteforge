# KB-Tool 架构文档

## 设计目标

| 目标 | 说明 |
|------|------|
| 零配置 | 用户不需要知道 OCR/Readability/yt-dlp 是什么 |
| 智能路由 | 自动识别输入类型，用户不需要指定 |
| 原文优先 | 默认保留完整信息，AI 旁注帮用户定位 |
| 模块化 | 核心 50MB，按需安装组件 |
| 本地/API 双通道 | 每个组件可选本地或云端处理 |

## 组件架构

```
┌─────────────────────────────────────────────────────┐
│                    CLI (cli.py)                      │
│                    kb <input>                        │
├─────────────────────────────────────────────────────┤
│                  Router (router.py)                  │
│         URL / 文件 / 目录 / 视频 URL                  │
├──────────┬──────────┬──────────┬────────────────────┤
│ Article  │   OCR    │  Video   │   Future Pipeline   │
│ Pipeline │ Pipeline │ Pipeline │   (PDF/Email/...)   │
├──────────┴──────────┴──────────┴────────────────────┤
│               LLM (llm.py) - OpenRouter              │
├─────────────────────────────────────────────────────┤
│            Output (output.py) - Markdown             │
└─────────────────────────────────────────────────────┘
```

## 数据流

### 文章管线（Article Pipeline）

```
URL
 ↓
trafilatura.fetch_url() → HTML
 ↓
trafilatura.extract() → (正文, 元数据)
 ↓
llm.generate_annotations() → {summary, key_points, key_data, tags, reread}
 ↓
output.format_article() → Markdown (frontmatter + 原文 + 旁注)
 ↓
文件 / stdout
```

## 技术选型

| 组件 | 选择 | 理由 |
|------|------|------|
| CLI | Typer | 类型安全，自动生成帮助 |
| 网页提取 | trafilatura | benchmark 最优，内置去噪 |
| LLM | OpenRouter API | 多模型，按量付费 |
| 输出 | Markdown + YAML frontmatter | 兼容所有笔记工具 |
| 包管理 | pip + pyproject.toml | Python 标准 |

## 模块说明

### cli.py
- Typer CLI 入口
- 参数：input, --mode, --output, --model, --no-annotations, --verbose
- Rich 进度条和彩色输出

### router.py
- `detect_input_type(input)` → "url" | "file" | "directory" | "video_url" | "unknown"
- `route_input(...)` → 路由到对应管线

### pipelines/base.py
- ABC 基类，所有管线继承

### pipelines/article.py
- trafilatura 提取正文
- 调用 LLM 生成旁注
- 格式化输出

### llm.py
- OpenRouter API 封装
- Prompt 设计：文章分析 → JSON 旁注
- 容错：失败返回空注释，不中断流程
- 内容截断：8000 字符上限

### output.py
- YAML frontmatter 生成
- Markdown 格式化（原文 + 旁注块）
