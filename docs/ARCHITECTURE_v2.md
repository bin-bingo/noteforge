# kb-tool 技术架构文档 v2.0

**架构师**: kb-architect (AI Agent)  
**创建日期**: 2026-03-18  
**状态**: ✅ 已完成  
**版本**: v2.0 (Phase 3 完成版)

---

## 一、架构概述

### 1.1 设计目标
| 目标 | 说明 | 实现方式 |
|-----|------|---------|
| 零配置 | 用户不需要知道 OCR/Readability/yt-dlp 是什么 | 智能路由 + 默认配置 |
| 智能路由 | 自动识别输入类型 | URL/文件/目录/视频检测 |
| 原文优先 | 保留完整信息，AI 旁注帮助定位 | fidelity 模式默认 |
| 模块化 | 核心 50MB，按需安装 | 分层依赖设计 |
| 本地/API 双通道 | 每个组件可选本地或云端 | 组件可插拔 |

### 1.2 系统边界
```\n┌──────────────────────────────────────────┐\n│           用户交互层                      │\n│  CLI (kb)  │  OpenClaw Skill  │  API    │\n└──────────────────────────────────────────┘\n                    ↓\n┌──────────────────────────────────────────┐\n│           智能路由层                      │\n│  输入类型识别  │  任务分发  │  错误处理  │\n└──────────────────────────────────────────┘\n                    ↓\n┌──────────────────────────────────────────┐\n│           管线处理层                      │\n│  文章管线  │  OCR 管线  │  视频管线  │\n└──────────────────────────────────────────┘\n                    ↓\n┌──────────────────────────────────────────┐\n│           AI 增强层                       │\n│  LLM 旁注生成  │  推理校错  │  摘要提炼  │\n└──────────────────────────────────────────┘\n                    ↓\n┌──────────────────────────────────────────┐\n│           输出层                          │\n│  Markdown 格式化  │  飞书同步  │  文件存储  │\n└──────────────────────────────────────────┘\n```

---

## 二、核心模块设计

### 2.1 CLI 模块 (`cli.py`)
**职责**: 用户交互入口，参数解析，结果展示

**关键函数**:
```python
@app.command()
def main(
    input: str,           # 输入：URL/文件/目录
    mode: str,           # 处理模式
    output: Optional[Path], # 输出路径
    model: str,          # LLM 模型
    no_annotations: bool,  # 跳过 AI 旁注
    verbose: bool        # 详细模式
)

@app.command("batch")
def batch_process(
    inputs: list[str],   # 多个输入
    output_dir: Optional[Path], # 输出目录
    ...
)
```

**设计要点**:
- 使用 Typer 框架，自动生成帮助文档
- 支持子命令（`config`, `batch`, `help`）
- Rich 库美化输出（进度条、彩色文本）

### 2.2 智能路由模块 (`router.py`)
**职责**: 输入类型识别，任务分发

**关键函数**:
```python
def detect_input_type(input: str) -> str:
    """识别输入类型：url | file | directory | video_url"""
    
def route_input(
    input_path: str,
    input_type: str,
    mode: str,
    model: str,
    generate_annotations: bool,
    verbose: bool
) -> str:
    """路由到对应管线处理"""
```

**路由逻辑**:
```
输入 → 是否 URL? 
      → 是 → 视频域名？
            → 是 → 视频管线
            → 否 → 微信域名？
                  → 是 → 文章管线 (Playwright 兜底)
                  → 否 → 文章管线 (trafilatura)
      → 否 → 是否文件？
            → 是 → 图片？
                  → 是 → OCR 管线
                  → 否 → 文件处理
            → 否 → 目录？
                  → 是 → 批量处理
                  → 否 → 错误
```

### 2.3 文章管线 (`pipelines/article.py`)
**职责**: 网页内容提取，AI 旁注生成

**处理流程**:
```
URL → trafilatura.fetch_url() → HTML
    → trafilatura.extract() → (正文，元数据)
    → llm.generate_annotations() → {summary, key_points, key_data, tags, reread}
    → output.format_article() → Markdown
```

**技术选型**:
- **主提取器**: trafilatura (快且准)
- **兜底方案**: Playwright (微信等 JS 渲染页面)
- **备用方案**: Jina Reader API (云端渲染)

**关键代码**:
```python
class ArticlePipeline:
    def __init__(self, generate_annotations=True, model="default"):
        self.generate_ann = generate_annotations
        self.model = model
    
    def process(self, url: str) -> str:
        # 1. 提取正文
        html = fetch_url(url)
        content, metadata = extract(html)
        
        # 2. 生成旁注
        if self.generate_ann:
            annotations = generate_annotations(content, model=self.model)
        else:
            annotations = None
        
        # 3. 格式化输出
        return format_article(
            title=metadata.get("title"),
            content=content,
            url=url,
            annotations=annotations
        )
```

### 2.4 OCR 管线 (`pipelines/ocr.py`)
**职责**: 图片文字识别，LLM 校错

**技术选型**:
- **OCR 引擎**: RapidOCR (API 稳定，中文优化)
- **校错方案**: LLM 推理校错
- **备用方案**: tesseract (轻量级)

**处理流程**:
```
图片 → 预处理 (灰度化/二值化/去噪)
    → RapidOCR 识别 → 原始文本
    → LLM 校错 → 校正后文本
    → 格式化 → Markdown
```

### 2.5 视频管线 (`pipelines/video.py`)
**职责**: 视频字幕提取，AI 总结

**技术选型**:
- **下载器**: yt-dlp (支持 B 站/YouTube/抖音)
- **转录**: Whisper (音频转文字)
- **关键帧**: ffmpeg 场景检测
- **总结**: LLM 生成结构化笔记

**处理流程**:
```
视频 URL → yt-dlp 下载字幕 (优先)
        → 无字幕？→ 下载音频 → Whisper 转录
        → ffmpeg 提取关键帧
        → LLM 生成时间戳笔记
        → 组装 Markdown (截图 + 时间戳 + 总结)
```

**Whisper Fallback**:
```python
def _transcribe_with_whisper(audio_path: str) -> str:
    try:
        # 优先使用 faster-whisper (更快)
        from faster_whisper import WhisperModel
        model = WhisperModel("base")
        segments, _ = model.transcribe(audio_path)
        return "".join([s.text for s in segments])
    except ImportError:
        # 回退到 openai-whisper
        import whisper
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        return result["text"]
```

### 2.6 LLM 模块 (`llm.py`)
**职责**: AI 旁注生成

**支持模式**:
- **OpenRouter API**: 多模型切换，按量付费
- **OpenClaw 复用**: 使用 Boss 已配置的模型

**Prompt 设计**:
```python
def generate_annotations(text: str, model: str = "default") -> dict:
    prompt = f"""
    请分析以下文章，生成结构化旁注：
    
    要求：
    1. 摘要：3 句话概括核心内容
    2. 要点：列出 3-5 个关键论点
    3. 数据：提取关键数字和统计
    4. 待读：标记值得精读的段落
    
    文章：
    {text[:8000]}  # 限制长度
    """
    
    response = call_llm_api(prompt, model=model)
    return parse_json_response(response)
```

### 2.7 输出模块 (`output.py`)
**职责**: Markdown 格式化

**输出格式**:
```markdown
---
title: "文章标题"
source: "https://example.com"
type: article
created: 2026-03-18
tags: ["标签 1", "标签 2"]
---

# 文章标题

> 📝 **摘要**: AI 生成的 3 句话摘要

---

## 原文

[文章完整内容]

---

> 💡 **要点**
> - 要点 1
> - 要点 2

> 📊 **关键数据**
> - 数据 1

> 📖 **待读**
> - 这段值得精读
```

### 2.8 飞书同步模块 (`feishu_sync.py`)
**职责**: 同步到飞书文档/云盘

**关键函数**:
```python
def sync_to_feishu(
    content: str,
    title: str,
    folder_token: Optional[str] = None
) -> dict:
    """同步 Markdown 到飞书文档"""
    result = feishu_doc(
        action="create",
        title=title,
        content=content,
        folder_token=folder_token
    )
    return {"doc_token": result.get("doc_token"), "status": "success"}

def upload_to_feishu_drive(
    file_path: str,
    folder_token: Optional[str] = None
) -> dict:
    """上传文件到飞书云盘"""
    result = feishu_drive(
        action="upload",
        file_path=file_path,
        folder_token=folder_token
    )
    return {"file_token": result.get("file_token")}
```

---

## 三、数据流

### 3.1 文章处理数据流
```
用户输入 URL
    ↓
CLI 解析参数
    ↓
智能路由识别为文章 URL
    ↓
ArticlePipeline.process()
    ├─ trafilatura 提取正文
    ├─ LLM 生成旁注
    └─ output 格式化
    ↓
输出 Markdown
    ├─ 终端显示
    ├─ 写入文件
    └─ (可选) 同步飞书
```

### 3.2 批量处理数据流
```
用户输入多个 URL
    ↓
CLI batch 命令
    ↓
遍历每个输入
    ├─ 检测类型
    ├─ 路由到对应管线
    ├─ 生成 Markdown
    └─ 保存到输出目录
    ↓
显示进度和统计
```

---

## 四、配置管理

### 4.1 配置文件 (~/.kb/config.yaml)
```yaml
llm:
  provider: api
  api_provider: openrouter
  api_model: anthropic/claude-sonnet-4
  # api_key: sk-or-... (或使用环境变量)
  timeout: 30.0

output:
  dir: ~/.kb/vault/
  mode: fidelity  # fidelity | concise | raw
```

### 4.2 环境变量
```bash
# LLM API Key
export OPENROUTER_API_KEY="sk-or-..."

# 自定义配置路径
export KB_CONFIG_PATH="/path/to/config.yaml"

# 输出目录
export KB_OUTPUT_DIR="~/kb/"
```

---

## 五、错误处理

### 5.1 错误类型
| 错误类型 | 原因 | 处理方式 |
|---------|------|---------|
| `LLMError` | API Key 无效/限流 | 提示检查配置，建议切换模型 |
| `ExtractionError` | 网页无法访问/反爬 | 尝试兜底方案 (Playwright/Jina) |
| `OCRError` | 图片质量差/格式不支持 | 提示重新截图，尝试备用引擎 |
| `VideoError` | 链接失效/地区限制 | 提示检查链接，需要代理 |

### 5.2 容错机制
- **LLM 失败**: 返回空旁注，不中断流程
- **提取失败**: 尝试多种方案 (trafilatura → Playwright → Jina)
- **网络超时**: 自动重试 3 次，指数退避
- **配置缺失**: 使用默认值，提示用户配置

---

## 六、性能优化

### 6.1 缓存策略
- **LLM 响应缓存**: 相同内容不重复调用
- **网页内容缓存**: 避免重复抓取
- **OCR 结果缓存**: 相同图片不重复识别

### 6.2 并行处理 (未来优化)
```python
# TODO: 批量处理使用 asyncio 并行
async def batch_process_async(inputs: list[str]):
    tasks = [process_single(inp) for inp in inputs]
    results = await asyncio.gather(*tasks)
    return results
```

### 6.3 内存优化
- 流式处理大文件
- 及时释放不再需要的内存
- 限制 LLM 输入长度 (8000 字符)

---

## 七、安全考虑

### 7.1 敏感信息保护
- **API Key**: 存储在环境变量或配置文件，不提交到代码库
- **Cookies**: B 站/抖音 cookies 存储在本地，不上传
- **用户数据**: 处理的内容默认保存在本地，不上传云端

### 7.2 输入验证
- URL 格式验证
- 文件类型白名单
- 防止路径遍历攻击

---

## 八、扩展性设计

### 8.1 插件系统 (未来)
```python
# 自定义管线示例
class CustomPipeline(BasePipeline):
    def process(self, input_data) -> str:
        # 自定义处理逻辑
        pass

# 注册插件
register_pipeline("custom", CustomPipeline)
```

### 8.2 支持更多格式
- [ ] PDF 文档提取
- [ ] Email 处理
- [ ] 播客音频转录
- [ ] 微信聊天记录导出

---

## 九、技术债务

| 问题 | 影响 | 优先级 | 计划解决时间 |
|-----|------|-------|------------|
| 批量处理未并行 | 速度较慢 | P2 | v1.1 |
| 缺少进度回调 | 无法实时反馈 | P2 | v1.1 |
| 配置热重载 | 需要重启 | P3 | v1.2 |
| 无插件系统 | 扩展困难 | P3 | v2.0 |

---

*文档版本：v2.0*  
*下次更新：Phase 4 完成后或重大架构调整时*
