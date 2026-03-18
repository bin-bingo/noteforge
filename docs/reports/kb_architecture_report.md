# 系统架构设计 项目报告

## 需求
- **背景**：Boss 需要一个个人知识库构建工具，将图片、URL、PDF、文本等多种来源自动提炼为结构化 Markdown 笔记
- **目标**：完成系统架构设计，为后续开发提供技术蓝图
- **验收标准**：包含架构图、组件说明、技术选型对比表、数据流图的完整设计文档

## 方案
### 技术选型及理由

| 组件 | 选型 | 核心理由 |
|------|------|----------|
| **OCR 引擎** | PaddleOCR | 中文识别准确率 ~97%，远超 Tesseract (~85-90%)；PP-Structure 支持表格识别；离线可用 |
| **网页提取** | trafilatura | benchmark 最优，中文站点支持好（微信/CSDN），维护活跃 |
| **视频字幕** | yt-dlp 字幕优先 | 速度秒级，免费；whisper 作为无字幕时的本地备选 |
| **LLM 接口** | OpenRouter API | 当前唯一可用方案（无 GPU）；DeepSeek 系列性价比高；抽象接口便于后续切换本地模型 |
| **CLI 框架** | Python Typer | 所有核心库都是 Python 生态，Typer 现代化且自带类型校验 |
| **存储** | 本地 Markdown + SQLite | 简单可靠，Obsidian 兼容，全文搜索可用 |

### 实现步骤（MVP 分阶段）
1. **Phase 1**：CLI 框架 + 文章提取管线 + LLM 提炼 + Markdown 输出
2. **Phase 2**：图片 OCR + 视频字幕 + SQLite 索引
3. **Phase 3**：PDF 处理 + 批量异步 + MCP 服务

## 落地效果
- ✅ **已完成**：输出完整架构文档 `work_rpt/drafts/kb_architecture_draft.md`，包含：
  - ASCII 系统架构图 + Mermaid 类图 + Mermaid 数据流图
  - 4 种 Processor 接口设计（Image/Web/PDF/Text）
  - 6 项技术选型对比表（每项含 2-4 个方案对比）
  - Pipeline Orchestrator 编排逻辑伪代码
  - 存储方案（目录结构 + SQLite Schema）
  - 配置管理方案（config.yaml 设计）
  - 错误处理与重试策略
  - OpenClaw 集成方式（CLI → ACP → MCP 三层）
  - 依赖清单
  - 风险与缓解措施表
- ✅ **已完成**：更新项目上下文 `CONTEXT.md`（加入技术选型摘要）
- ✅ **已完成**：更新任务分解 `TASKS.md`（标记 1.3 和 2.1 完成）
- ✅ **已完成**：写入操作日志 `log.jsonl`
- ⚠️ **未完成项**：web_search API 不可用，无法做实时 benchmark 调研，技术选型基于已有知识
- 📋 **下一步**：前端工程师设计 CLI 交互接口，后端工程师实现 WebProcessor（文章提取）原型
