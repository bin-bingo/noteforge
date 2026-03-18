# kb-tool OpenClaw Skill

## 功能说明
在飞书聊天中直接调用 kb-tool，输入链接/图片自动生成 Markdown 笔记。

## 使用方式

### 1. 文章链接提炼
```
kb https://mp.weixin.qq.com/s/xxx
```

### 2. 多图 OCR 识别
```
kb [上传图片]
```

### 3. 视频链接提炼
```
kb https://www.bilibili.com/video/BV1xx411c7mD
```

### 4. 批量处理
```
kb https://url1.com https://url2.com [图片]
```

## 输出格式
- 默认：Markdown 格式（frontmatter + 原文 + AI 旁注）
- 可选模式：
  - `--mode=fidelity` 原文 +AI 旁注（默认）
  - `--mode=concise` 去水提炼
  - `--mode=raw` 纯原文

## 配置项
- `KB_LLM_MODEL`: LLM 模型（默认复用 OpenClaw 配置）
- `KB_OUTPUT_DIR`: 输出目录（默认 `~/kb/`）
- `KB_MODE`: 默认模式（默认 `fidelity`）

## 技术实现
- 调用本地 `kb` CLI 命令
- 支持飞书图片上传 → 临时文件 → OCR 处理
- 输出自动同步到飞书文档（可选）

## 依赖
- kb-tool 已安装（`pip install kb-tool[all]`）
- OpenClaw 配置正常
- 飞书权限：文档读写、云盘上传
