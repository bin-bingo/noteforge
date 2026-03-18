# kb-tool Phase 2 PoC 项目报告

## 需求
- **背景**：个人知识库构建工具需要验证核心管线可行性——用户扔一个 URL 进来，自动提取正文 + AI 旁注，输出结构化 Markdown
- **目标**：Phase 2 PoC，验证"URL → 文章笔记"完整流程可跑通
- **验收标准**：
  1. `kb <url>` 命令可用
  2. 正文提取完整（trafilatura）
  3. LLM 生成旁注（摘要/要点/数据/待读）
  4. 输出 Markdown 带 frontmatter
  5. 测试全部通过

## 方案
- **技术选型**：Python 3.12 + Typer CLI + trafilatura + OpenRouter API + YAML frontmatter
- **架构**：CLI → 智能路由 → 管线(文章/OCR/视频) → LLM → Markdown 输出
- **实现步骤**：
  1. 项目骨架（pyproject.toml + 目录结构）
  2. 核心模块（router/llm/output/config/cli）
  3. 文章管线（trafilatura + LLM 旁注）
  4. 测试 + 文档

## 落地效果

### 已创建文件

| 文件 | 功能 |
|------|------|
| `pyproject.toml` | 项目配置，依赖声明，`kb` 命令入口 |
| `src/kb_tool/__init__.py` | 包初始化 |
| `src/kb_tool/router.py` | 智能路由——识别 URL/文件/目录/视频 URL |
| `src/kb_tool/llm.py` | LLM 调用——OpenRouter API，生成旁注 JSON |
| `src/kb_tool/output.py` | Markdown 输出——frontmatter + 原文 + 旁注块 |
| `src/kb_tool/config.py` | 配置管理——~/.kb/config.yaml + 环境变量 |
| `src/kb_tool/cli.py` | Typer CLI 入口，支持 --mode/--output/--no-annotations |
| `src/kb_tool/pipelines/base.py` | 管线抽象基类 |
| `src/kb_tool/pipelines/article.py` | 文章管线——trafilatura 提取 + LLM 旁注 |
| `tests/test_article.py` | 4 个测试用例（路由/格式化/旁注/容错） |
| `README.md` | 项目说明、安装、使用示例 |
| `docs/ARCHITECTURE.md` | 架构图、数据流、技术选型 |

### 测试结果
```
tests/test_article.py::test_detect_input_type PASSED
tests/test_article.py::test_format_article PASSED
tests/test_article.py::test_format_article_with_annotations PASSED
tests/test_article.py::test_llm_returns_empty_on_no_key PASSED
4 passed in 0.57s
```

### 端到端验证
- 用 `https://paulgraham.com/greatwork.html` 测试
- 正文提取：成功，1147+ 行完整正文
- 输出格式：YAML frontmatter + 标题 + 原文 正确
- LLM 旁注：因无 API key 优雅降级返回空注释（不崩溃）

### Bug 修复
- 修复 `ArticlePipeline.__init__()` 参数名不匹配（`generate_ann` vs `generate_annotations`）
- 修正默认模型 ID（`claude-sonnet-4` 替代过长的版本号）

### 待 Boss 确认
1. **LLM 模型选择**：当前默认 `anthropic/claude-sonnet-4`，是否需要调整？
2. **默认输出目录**：当前输出到 stdout 或指定文件，是否需要默认保存到 `~/kb/`？
3. **下一步**：继续做 OCR 管线 (2.3) 还是先把文章管线打磨完善？
