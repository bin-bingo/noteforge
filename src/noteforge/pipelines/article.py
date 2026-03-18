"""Article extraction pipeline: URL → structured Markdown with AI annotations."""

import trafilatura

from kb_tool.pipelines.base import Pipeline
from kb_tool.llm import generate_annotations
from kb_tool.output import format_article
from kb_tool.browser import launch_browser


class ArticlePipeline(Pipeline):
    """Extract article from URL and generate annotated Markdown."""

    def __init__(
        self,
        mode: str = "fidelity",
        model: str = "anthropic/claude-sonnet-4",
        generate_annotations: bool = True,
        verbose: bool = False,
    ):
        self.mode = mode
        self.model = model
        self.generate_ann = generate_annotations
        self.verbose = verbose

    def process(self, input_data: str, config: dict | None = None) -> str:
        """Process article URL into annotated Markdown.

        Args:
            input_data: Article URL
            config: Optional config (currently unused)

        Returns:
            Markdown document with frontmatter and annotations
        """
        url = input_data

        # Step 1: Extract content with trafilatura
        downloaded = trafilatura.fetch_url(url)
        html_source = None

        if downloaded is not None:
            html_source = downloaded
        else:
            # Try Playwright fallback
            html_source = self._fetch_with_playwright(url)
            if html_source is None:
                return f"# 提取失败\n\n无法访问 URL: {url}\n"

        # Extract content from HTML
        result = trafilatura.extract(
            html_source,
            include_comments=False,
            include_tables=True,
            include_links=True,
            include_images=False,
            output_format="markdown",
            with_metadata=True,
        )

        if result is None:
            return f"# 提取失败\n\n无法提取正文: {url}\n"

        # trafilatura returns (content, metadata) tuple when with_metadata=True
        # but with output_format='markdown', it returns a string with frontmatter
        if isinstance(result, tuple):
            content, metadata = result
            title = metadata.get("title", "") if metadata else ""
            author = metadata.get("author", "") if metadata else ""
            date = metadata.get("date", "") if metadata else ""
        else:
            # Parse YAML frontmatter from markdown output
            content = result
            title = ""
            author = ""
            date = ""
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    import re

                    frontmatter = parts[1]
                    content = parts[2].strip()
                    m = re.search(r"title:\s*(.+)", frontmatter)
                    if m:
                        title = m.group(1).strip().strip('"').strip("'")
                    m = re.search(r"author:\s*(.+)", frontmatter)
                    if m:
                        author = m.group(1).strip().strip('"').strip("'")
                    m = re.search(r"date:\s*(.+)", frontmatter)
                    if m:
                        date = m.group(1).strip().strip('"').strip("'")

        # Fallback title extraction
        if not title:
            title = self._extract_title(html_source) or "无标题"

        # Build content with metadata header
        md_parts = []
        if author:
            md_parts.append(f"**作者：** {author}")
        if date:
            md_parts.append(f"**日期：** {date}")
        if md_parts:
            md_parts.append("")

        md_parts.append(content)
        full_content = "\n".join(md_parts)

        # Step 2: Generate annotations (unless raw mode)
        annotations = {}
        if self.generate_ann and self.mode != "raw":
            if self.verbose:
                print("Generating AI annotations...")
            annotations = generate_annotations(
                title=title,
                content=content,
                url=url,
                model=self.model,
            )

        # Step 3: Format output
        return format_article(
            title=title,
            content=full_content,
            url=url,
            annotations=annotations,
        )

    @staticmethod
    def _extract_title(html: str) -> str:
        """Extract title from HTML as fallback."""
        import re

        match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    @staticmethod
    def _fetch_with_playwright(url: str) -> str | None:
        """Fetch page content using Playwright browser as fallback.

        Args:
            url: URL to fetch

        Returns:
            HTML content string, or None if failed
        """
        from playwright.sync_api import sync_playwright

        try:
            with sync_playwright() as p:
                browser = launch_browser(p, headless=True)
                try:
                    page = browser.new_page()
                    page.goto(url, wait_until="networkidle")
                    html = page.content()
                    return html
                finally:
                    browser.close()
        except Exception:
            return None
