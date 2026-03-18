"""LLM wrapper for generating article annotations via OpenRouter API."""

import json
from typing import Optional

from openai import OpenAI

from kb_tool.config import get_config

MAX_CONTENT_LENGTH = 8000

ANNOTATION_PROMPT = """你是一个知识管理助手。请分析以下文章，生成结构化旁注。

文章标题：{title}
来源：{url}

文章正文：
{content}

请严格输出以下 JSON 格式（不要输出其他内容）：
{{
  "summary": "3句话摘要，概括文章核心内容",
  "key_points": ["要点1", "要点2", "要点3"],
  "key_data": ["关键数据/数字/引用"],
  "tags": ["标签1", "标签2"],
  "reread": ["值得回头精读的段落或主题描述"]
}}"""


class LLMError(Exception):
    """LLM API error."""

    pass


def _get_client() -> OpenAI:
    """Create OpenRouter API client."""
    config = get_config()
    api_key = config.llm.api_key
    if not api_key:
        raise LLMError("OPENROUTER_API_KEY environment variable not set")
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        timeout=config.llm.timeout,
    )


def generate_annotations(
    title: str,
    content: str,
    url: str = "",
    model: Optional[str] = None,
) -> dict:
    """Generate AI annotations for article content.

    Args:
        title: Article title
        content: Article body text
        url: Source URL
        model: LLM model ID (default: anthropic/claude-sonnet-4)

    Returns:
        dict with keys: summary, key_points, key_data, tags, reread
        Returns empty annotations on failure (never raises).
    """
    empty = {"summary": "", "key_points": [], "key_data": [], "tags": [], "reread": []}

    try:
        client = _get_client()
        config = get_config()
        model_id = model or config.llm.api_model

        # Truncate content if too long
        truncated = content[:MAX_CONTENT_LENGTH]
        if len(content) > MAX_CONTENT_LENGTH:
            truncated += "\n\n[内容已截断...]"

        prompt = ANNOTATION_PROMPT.format(
            title=title or "无标题",
            url=url or "未知来源",
            content=truncated,
        )

        response = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1024,
        )

        text = response.choices[0].message.content.strip()

        # Parse JSON (handle markdown code blocks)
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        result = json.loads(text)

        # Validate structure
        for key in empty:
            if key not in result:
                result[key] = empty[key]

        return result

    except json.JSONDecodeError:
        return empty
    except Exception:
        return empty
