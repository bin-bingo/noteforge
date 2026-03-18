"""Markdown output formatter for kb-tool."""

from datetime import date


def format_article(
    title: str,
    content: str,
    url: str = "",
    annotations: dict | None = None,
) -> str:
    """Format article content with annotations into Markdown.

    Args:
        title: Article title
        content: Extracted article body (Markdown)
        url: Source URL
        annotations: AI annotations dict from llm.generate_annotations

    Returns:
        Complete Markdown document with frontmatter
    """
    ann = annotations or {}
    today = date.today().isoformat()

    # Build frontmatter
    tags = ann.get("tags", [])
    tags_str = ", ".join(f'"{t}"' for t in tags) if tags else ""

    lines = [
        "---",
        f'title: "{_escape_yaml(title)}"',
        f'source: "{url}"' if url else 'source: ""',
        "type: article",
        f"created: {today}",
        f"tags: [{tags_str}]" if tags else "tags: []",
        "---",
        "",
        f"# {title or '无标题'}",
        "",
    ]

    # Summary annotation
    summary = ann.get("summary", "")
    if summary:
        lines.extend([
            "> 📝 **摘要**",
            f"> {summary}",
            "",
        ])

    lines.extend(["---", "", "## 原文", "", content or "*无法提取正文*", ""])

    # Annotations footer
    key_points = ann.get("key_points", [])
    key_data = ann.get("key_data", [])
    reread = ann.get("reread", [])

    if key_points or key_data or reread:
        lines.extend(["---", ""])

        if key_points:
            lines.append("> 💡 **要点**")
            for p in key_points:
                lines.append(f"> - {p}")
            lines.append("")

        if key_data:
            lines.append("> 📊 **关键数据**")
            for d in key_data:
                lines.append(f"> - {d}")
            lines.append("")

        if reread:
            lines.append("> 📖 **待读**")
            for r in reread:
                lines.append(f"> - {r}")
            lines.append("")

    return "\n".join(lines)


def _escape_yaml(text: str) -> str:
    """Escape double quotes in YAML strings."""
    return (text or "").replace('"', '\\"')
