# CLI + 文档工程 项目报告

## 需求
- **背景**：kb-tool 核心管线（文章提取）已可用，但 CLI 体验粗糙、缺少视频管线、文档不完整
- **目标**：完善 CLI 体验，添加视频管线 PoC，补充项目文档，定义 OpenClaw skill
- **验收标准**：CLI 彩色输出+进度提示+config 子命令可用；视频管线骨架可跑通；文档准确反映功能；SKILL.md 就绪

## 方案
- **CLI**：基于已有 Rich 集成，增加彩色状态输出（绿✓/红✗/蓝ℹ）、进度提示消息、`kb config show/init` 子命令、Shell 补全说明、改进 help 文本
- **视频管线**：复用 yt-dlp 字幕提取 → OpenRouter LLM 总结 → Markdown 输出架构，先实现 YouTube，B站/抖音路由已就绪
- **文档**：重写 README.md（功能状态表+架构图+CLI 参考+开发指南），新建 USER_GUIDE.md（安装+配置+场景+排错）
- **SKILL.md**：定义触发条件、使用方式、输出格式、示例交互

## 落地效果

### 已完成文件

| 文件 | 变更 | 说明 |
|------|------|------|
| `src/kb_tool/cli.py` | 重写 | 彩色输出、进度提示、`config show/init`、Shell 补全说明、更好 help |
| `src/kb_tool/pipelines/video.py` | 新建 | 视频管线：yt-dlp 字幕提取 → LLM 总结 → Markdown（YouTube ✅，B站/抖音路由就绪） |
| `src/kb_tool/router.py` | 更新 | 添加 `video_url → VideoPipeline` 路由，新增 `b23.tv` 域名 |
| `src/kb_tool/pipelines/__init__.py` | 更新 | 导出 VideoPipeline |
| `README.md` | 重写 | 功能状态表、使用示例、架构图、CLI 参考、开发指南、项目结构 |
| `docs/USER_GUIDE.md` | 新建 | 安装指南、配置说明、6 个使用场景（含完整命令示例）、故障排除 FAQ |
| `SKILL.md` | 新建 | OpenClaw skill 定义：触发条件、使用方式、错误处理、示例交互 |
| `log.jsonl` | 新建 | 6 条结构化操作记录 |

### 验证结果

```
✅ 4/4 测试通过（原有测试无破坏）
✅ CLI imports 正常
✅ 路由测试全部通过：
   - YouTube/YouTube短链 → video_url
   - Bilibili/b23.tv → video_url  
   - 普通 URL → url
```

### 未完成项 & 风险

1. **视频管线未端到端测试** — 需要 OpenRouter API Key + yt-dlp 才能实际跑通，骨架逻辑已验证
2. **B站/抖音** — yt-dlp 理论上支持，但字幕获取可能需要登录 cookie，待实际测试
3. **文件/目录管线** — 路由已支持但实际处理管线未实现，属于下一阶段
4. **Shell 补全** — 提供了安装说明但未内嵌生成脚本（Typer 内置支持，用户自行 eval 即可）
