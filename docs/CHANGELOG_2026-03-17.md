# kb-tool 技术方案修改记录

> 日期：2026-03-17 | 版本：v0.1 → v0.2

---

## 修改概览

基于今日技术调研和 Boss 讨论，对原有技术方案进行以下修改。

---

## 修改 1：OCR 引擎更换

**原方案：** PaddleOCR 3.0
**新方案：** RapidOCR (rapidocr-onnxruntime)
**日期：** 2026-03-17

### 修改理由
- PaddleOCR 3.4 修改了 API，`show_log`、`cls` 参数不兼容
- PaddleOCR 需要 PaddlePaddle 框架（体积大、依赖重）
- RapidOCR 基于 ONNX Runtime，无需 PaddlePaddle
- RapidOCR 精度 92%（PaddleOCR 94.5%），差距可通过 LLM 校错弥补

### 影响范围
- `src/kb_tool/pipelines/ocr.py` — 更换引擎
- `pyproject.toml` — 依赖从 `paddleocr` 改为 `rapidocr-onnxruntime`
- 安装体积：500MB → 225MB（减少 55%）

### 回退方案
如需更高精度，可切换到 PaddleOCR（解决 API 兼容问题后）

---

## 修改 2：LLM 方案调整

**原方案：** 本地模型（Ollama）+ API 双通道
**新方案：** 纯 API（OpenRouter / OpenClaw），砍掉本地模型
**日期：** 2026-03-17

### 修改理由
- AI 旁注需要判断力，7B 小模型质量不达标
- 本地大模型（14B+）硬件要求高
- OpenClaw 用户直接复用已有 LLM 配置
- 独立用户走 OpenRouter API（~¥0.03/篇）

### 影响范围
- `src/kb_tool/llm.py` — 移除本地模型选项
- `pyproject.toml` — 移除 ollama/vllm 依赖
- 安装体积减少 ~4GB

---

## 修改 3：提炼策略调整

**原方案：** "去水留干"——LLM 提炼精华，去除废话
**新方案：** "原文+AI 旁注"——保留完整原文，AI 添加摘要/要点/数据标注
**日期：** 2026-03-17

### 修改理由
- "去水留干"会丢失论证过程、细节数据、上下文衔接
- 技术文档删细节致命，深度分析删论证等于没读
- "水"vs"干"是主观判断，容易做错
- 默认不丢信息密度，用户主动选择要省略什么

### 影响范围
- `src/kb_tool/output.py` — 新增"原文+旁注"输出模板
- `src/kb_tool/llm.py` — 旁注 prompt 设计（摘要/要点/数据/待读）
- 三种模式：`--mode=fidelity`（默认原文+旁注）/ `--mode=concise`（去水）/ `--mode=raw`（纯原文）

---

## 修改 4：浏览器策略

**原方案：** Playwright 自带浏览器（~400MB）
**新方案：** 优先使用系统 Chrome，Playwright 自带浏览器作为 fallback
**日期：** 2026-03-17

### 修改理由
- 系统已安装 Google Chrome 146.0
- 省 400MB 下载体积
- Core 安装包体积大幅减小

### 影响范围
- 新增 `src/kb_tool/browser.py` — 浏览器检测模块
- `src/kb_tool/pipelines/article.py` — Playwright fallback 使用系统 Chrome
- 安装体积减少 ~400MB

---

## 修改 5：视频管线增强

**原方案：** yt-dlp 字幕下载 → LLM 总结
**新方案：** 字幕优先 → 无字幕时 Whisper fallback + 关键帧截图
**日期：** 2026-03-17

### 修改理由
- 很多 B站/抖音视频没有字幕（实测验证）
- 需要音频转录作为 fallback
- 参考 BiliNote 架构：字幕优先 + whisper fallback + 截图

### 影响范围
- `src/kb_tool/pipelines/video.py` — 添加 Whisper fallback 逻辑
- `pyproject.toml` — 添加 `whisper` 和 `faster-whisper` 可选依赖
- 安装体积增加 ~74MB（base 模型）

---

## 修改 6：安装分层

**原方案：** 统一安装包
**新方案：** 四层安装（Core / Standard / Full / Pro）
**日期：** 2026-03-17

### 分层方案

| 层级 | 体积 | 包含组件 |
|------|------|---------|
| Core | ~25MB | httpx + trafilatura + pyyaml（API-only） |
| Standard | ~80MB | + rapidocr + click |
| Full | ~320MB | + Whisper base + Playwright |
| Pro | ~3GB | + PaddleOCR（最高精度） |

### 影响范围
- `pyproject.toml` — optional-dependencies 分组
- README.md — 安装说明

---

## 总结

| 修改 | 原方案 | 新方案 | 影响 |
|------|--------|--------|------|
| OCR 引擎 | PaddleOCR | RapidOCR | 体积-55% |
| LLM 方案 | 本地+API | 纯 API | 体积-4GB |
| 提炼策略 | 去水留干 | 原文+旁注 | 信息不丢失 |
| 浏览器 | Playwright 自带 | 系统 Chrome | 体积-400MB |
| 视频管线 | 仅字幕 | 字幕+Whisper fallback | 功能增强 |
| 安装方式 | 统一安装 | 四层分层 | 灵活部署 |

**总体效果：**
- 安装体积从 ~4.5GB 降至 ~320MB（标准安装）
- 零配置可用性保持不变
- 功能覆盖更完整
