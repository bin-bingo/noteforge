# kb-tool 用户指南 🦐

## 目录

1. [安装指南](#安装指南)
2. [配置说明](#配置说明)
3. [使用场景](#使用场景)
4. [故障排除](#故障排除)

---

## 安装指南

### 系统要求

- Python 3.12+
- pip
- （可选）yt-dlp（视频处理需要）

### 方式一：开发安装

```bash
# 1. 克隆仓库
git clone https://github.com/kb-tool/kb-tool.git
cd kb-tool

# 2. 创建虚拟环境
python3.12 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 3. 安装（含开发工具）
pip install -e ".[dev]"
```

### 方式二：从 PyPI 安装（即将支持）

```bash
pip install kb-tool
```

### 安装可选组件

```bash
# 视频处理支持
pip install yt-dlp

# 验证安装
kb --version
# 输出: kb-tool v0.1.0
```

### 安装后设置

```bash
# 设置 OpenRouter API Key（必需）
export OPENROUTER_API_KEY="sk-or-..."

# 创建默认配置
kb config init
```

---

## 配置说明

### API Key 配置

kb-tool 使用 [OpenRouter](https://openrouter.ai) 作为 LLM 提供商。你需要：

1. 注册 OpenRouter 账号
2. 获取 API Key
3. 设置环境变量：

```bash
# 临时设置（当前会话）
export OPENROUTER_API_KEY="sk-or-..."

# 永久设置（写入 shell 配置）
echo 'export OPENROUTER_API_KEY="sk-or-..."' >> ~/.bashrc
source ~/.bashrc
```

### 配置文件

配置文件位于 `~/.kb/config.yaml`。使用 `kb config init` 创建默认配置：

```yaml
# kb-tool 配置文件

llm:
  provider: api
  api_provider: openrouter
  api_model: anthropic/claude-sonnet-4  # 默认模型
  # api_key: sk-or-...                 # 可在配置文件中设置（不推荐）
  timeout: 30.0                        # API 超时（秒）

output:
  dir: ~/.kb/vault/                    # 默认输出目录
  mode: fidelity                       # 处理模式
```

### 可用 LLM 模型

通过 OpenRouter 支持的模型：

| 模型 ID | 说明 |
|---------|------|
| `anthropic/claude-sonnet-4` | 默认，质量好 |
| `anthropic/claude-haiku` | 更快更便宜 |
| `google/gemini-2.5-flash` | Google 最新 |
| `openai/gpt-4o` | OpenAI |
| `deepseek/deepseek-chat` | 性价比高 |

使用方式：
```bash
kb "https://example.com" --model google/gemini-2.5-flash
```

### 处理模式

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| `fidelity` | 原文 + AI 旁注（默认） | 完整保存信息密度 |
| `concise` | 提炼总结 | 快速浏览 |
| `raw` | 仅原文提取 | 不需要 AI 处理 |

```bash
kb "https://example.com" --mode concise
```

---

## 使用场景

### 场景一：保存网页文章

**场景**：看到一篇好文章，想保存到知识库。

```bash
# 基础用法
kb "https://paulgraham.com/greatwork.html"

# 保存到指定文件
kb "https://paulgraham.com/greatwork.html" \
  -o ~/notes/paul-graham-great-work.md

# 输出示例
# ✓ 已保存到 /home/user/notes/paul-graham-great-work.md (15234 字符)
```

输出包含：
- YAML frontmatter（标题、来源、日期、标签）
- 文章摘要（3 句话概括）
- 完整原文
- AI 旁注（要点、关键数据、待读标记）

### 场景二：YouTube 视频学习笔记

**场景**：看技术视频，想快速获取要点。

```bash
# YouTube 视频 → 学习笔记
kb "https://www.youtube.com/watch?v=VIDEO_ID"

# 使用快速模型
kb "https://www.youtube.com/watch?v=VIDEO_ID" \
  --model anthropic/claude-haiku

# 纯字幕（不加 AI 总结）
kb "https://www.youtube.com/watch?v=VIDEO_ID" --mode raw
```

**注意**：需要先安装 yt-dlp：
```bash
pip install yt-dlp
```

### 场景三：批量处理文章

**场景**：收集了一批文章链接，想批量转换。

```bash
# 创建链接列表文件
cat > urls.txt << EOF
https://example.com/article1
https://example.com/article2
https://example.com/article3
EOF

# 批量处理
mkdir -p ~/notes/batch
while IFS= read -r url; do
  filename=$(echo "$url" | md5sum | cut -d' ' -f1)
  kb "$url" -o "~/notes/batch/${filename}.md"
done < urls.txt
```

### 场景四：纯原文提取

**场景**：只需要原文，不需要 AI 加工。

```bash
kb "https://example.com/article" --mode raw

# 或者跳过旁注但保留提取
kb "https://example.com/article" --no-annotations
```

### 场景五：作为 OpenClaw 技能使用

**场景**：在 OpenClaw 对话中，用户发送链接时自动处理。

配置方法参见项目中的 `SKILL.md`。

### 场景六：查看和管理配置

```bash
# 查看当前配置
kb config show

# 创建默认配置文件
kb config init

# 覆盖已存在的配置
kb config init --force
```

---

## 故障排除

### Q: 提示 "OPENROUTER_API_KEY not set"

**原因**：未设置 API Key。

**解决**：
```bash
export OPENROUTER_API_KEY="sk-or-..."
kb config show  # 确认 Key 状态
```

### Q: 文章提取失败 / 正文为空

**可能原因**：
- 网站有反爬机制
- 需要登录才能访问
- JavaScript 渲染的内容

**解决**：
- 尝试使用 `--mode raw`
- 检查 URL 是否可正常访问
- 对于 JS 渲染的页面，暂时不支持

### Q: 视频字幕提取失败

**可能原因**：
- 未安装 yt-dlp
- 视频没有字幕（手动或自动生成）
- 地区限制

**解决**：
```bash
# 检查 yt-dlp 是否安装
which yt-dlp

# 安装 yt-dlp
pip install yt-dlp

# 手动检查视频是否有字幕
yt-dlp --list-subs "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Q: LLM 返回错误或空结果

**可能原因**：
- API Key 额度不足
- 模型暂时不可用
- 内容太长被截断

**解决**：
- 检查 OpenRouter 账户余额
- 尝试其他模型：`--model anthropic/claude-haiku`
- 使用 `--verbose` 查看详细错误

### Q: 输出中文乱码

**解决**：确保终端支持 UTF-8：
```bash
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

### Q: 如何使用本地模型？

**当前**：kb-tool 使用 OpenRouter API。

**未来**：将支持本地模型（Ollama 等）。关注项目更新。

### 获取帮助

- 查看帮助：`kb --help`
- 查看配置：`kb config show`
- 详细模式：`kb <input> --verbose`
- 提交 Issue：GitHub Issues

---

*最后更新：2026-03-17*
