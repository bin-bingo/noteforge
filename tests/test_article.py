"""Tests for kb-tool article pipeline."""

import os
from unittest.mock import patch, MagicMock


def test_detect_input_type():
    """Test URL and file detection."""
    from kb_tool.router import detect_input_type

    # URLs
    assert detect_input_type("https://example.com/article") == "url"
    assert detect_input_type("http://blog.example.com/post") == "url"

    # Video URLs
    assert detect_input_type("https://www.bilibili.com/video/BVxxx") == "video_url"
    assert detect_input_type("https://youtube.com/watch?v=xxx") == "video_url"
    assert detect_input_type("https://youtu.be/xxx") == "video_url"
    assert detect_input_type("https://www.douyin.com/video/xxx") == "video_url"

    # Non-existent path
    assert detect_input_type("/nonexistent/path") == "unknown"


def test_format_article():
    """Test Markdown output formatting."""
    from kb_tool.output import format_article

    # Basic article
    result = format_article(
        title="Test Article",
        content="This is the body.",
        url="https://example.com",
        annotations={},
    )

    assert "title: \"Test Article\"" in result
    assert "source: \"https://example.com\"" in result
    assert "type: article" in result
    assert "## 原文" in result
    assert "This is the body." in result


def test_format_article_with_annotations():
    """Test output with AI annotations."""
    from kb_tool.output import format_article

    ann = {
        "summary": "This is a summary.",
        "key_points": ["Point 1", "Point 2"],
        "key_data": ["42% improvement"],
        "tags": ["AI", "Tech"],
        "reread": ["Section 3"],
    }

    result = format_article(
        title="Annotated Article",
        content="Body text here.",
        url="https://example.com",
        annotations=ann,
    )

    assert "摘要" in result
    assert "This is a summary." in result
    assert "Point 1" in result
    assert "42% improvement" in result
    assert "Section 3" in result
    assert '"AI"' in result


def test_llm_returns_empty_on_no_key():
    """Test LLM gracefully handles missing API key."""
    from kb_tool.llm import generate_annotations

    # Without API key, should return empty annotations
    with patch.dict(os.environ, {}, clear=True):
        result = generate_annotations("Test", "Content", "https://example.com")

    assert result["summary"] == ""
    assert result["key_points"] == []


if __name__ == "__main__":
    test_detect_input_type()
    print("✅ test_detect_input_type passed")

    test_format_article()
    print("✅ test_format_article passed")

    test_format_article_with_annotations()
    print("✅ test_format_article_with_annotations passed")

    test_llm_returns_empty_on_no_key()
    print("✅ test_llm_returns_empty_on_no_key passed")

    print("\n✅ All tests passed!")
