# kb-tool 开发日志

> 日期：2026-03-18 | 版本：v0.1.0

---

## 修改 1：管线参数统一

**问题：** ArticlePipeline 和 VideoPipeline 使用 `generate_annotations`，但 OCRPipeline 使用 `use_llm`，导致 router.py 传参时可能 TypeError。

**修改：**
- `OCRPipeline.__init__` 参数从 `use_llm: bool` 改为 `generate_annotations: bool`
- 内部属性统一为 `self.generate_ann`
- `router.py` 中 OCRPipeline 实例化时传递 `generate_annotations` 和 `model` 参数

**文件：** `pipelines/ocr.py`, `router.py`

---

## 修改 2：CLI 入口完善

**新增功能：**
- `kb --version` / `kb -V` 显示版本号
- `kb config show` 显示当前配置（LLM、输出等）
- `kb config set <key> <value>` 设置配置项并写入 `~/.kb/config.yaml`
- `kb` 无参数时显示帮助（不再是报错）
- 输入无法识别时给出友好提示，不显示 Python traceback
- 帮助信息包含使用示例

**技术方案：**
- 使用 sys.argv 预处理：`kb <url>` 自动转为 `kb main <url>`，避免 typer 子命令冲突
- `_SUBCOMMANDS` 集合识别已知子命令，避免误注入

**文件：** `cli.py`

---

## 修改 3：安装包验证

**测试：** `pip install -e .` 成功，`kb` 命令可用。
- pyproject.toml 已包含 `[project.scripts] kb = "kb_tool.cli:app"`
- 使用 hatchling 构建后端，src layout 正确

**文件：** `pyproject.toml`（无需修改）

---

## 修改 4：真实 URL 测试

| URL | 结果 | 提取字数 | 备注 |
|-----|------|----------|------|
| https://httpbin.org/html | ✅ 成功 | 3734 chars | Moby-Dick 段落，正文完整提取 |
| https://sspai.com/post/80063 | ⚠️ 需要 JS | 225 chars | SPA 页面，trafilatura 无法提取 |
| https://blog.rust-lang.org | ✅ 成功 | 366 chars | 博客首页，简短描述提取 |

**结论：** 静态页面正常，SPA 页面需要 Playwright fallback（已有代码，未在此测试中触发）。

---

## 修改 5：Whisper fallback 验证

**测试内容：**
- `_transcribe_with_whisper` 函数可导入 ✅
- `_download_audio(url: str) -> str` 签名正确 ✅
- ImportError 处理：无 whisper 时给出友好提示（含安装命令）✅
- `VideoPipeline(generate_annotations=False)` 参数统一 ✅

---

## 修改 6：Phase 3 文档更新

- TASKS.md：Phase 3 从"待启动"更新为"进行中"，标记已完成任务
- CHANGELOG：新增今日变更记录
