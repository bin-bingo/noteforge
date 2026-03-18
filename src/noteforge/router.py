"""Smart routing module for kb-tool.

Determines input type and routes to appropriate pipeline.
"""

from pathlib import Path
from typing import Literal

InputType = Literal["url", "file", "directory", "image", "video_url", "unknown"]

# Video URL domains
VIDEO_DOMAINS = (
    "bilibili.com",
    "b23.tv",
    "youtube.com",
    "youtu.be",
    "douyin.com",
    "tiktok.com",
    "vimeo.com",
    "ixigua.com",
    "youku.com",
    "qq.com/video",
)

# Article URL domains (special handling, not generic)
ARTICLE_DOMAINS = (
    "mp.weixin.qq.com",  # 微信公众号
)

# Video file extensions
VIDEO_EXTENSIONS = frozenset({".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv"})

# Image file extensions
IMAGE_EXTENSIONS = frozenset(
    {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}
)


def is_wechat_article(url: str) -> bool:
    """Check if URL is a WeChat MP article."""
    return "mp.weixin.qq.com" in url.lower()


def detect_input_type(input_str: str) -> InputType:
    """Detect the type of input string.

    Args:
        input_str: The input string to analyze (URL, file path, or directory path)

    Returns:
        One of: "url", "file", "directory", "image", "video_url", "unknown"

    Examples:
        >>> detect_input_type("https://example.com/article")
        'url'
        >>> detect_input_type("https://www.bilibili.com/video/...")
        'video_url'
        >>> detect_input_type("/path/to/photo.png")
        'image'
        >>> detect_input_type("/path/to/file.pdf")
        'file'
        >>> detect_input_type("/path/to/directory")
        'directory'
    """
    # Check for URL
    if input_str.startswith("http://") or input_str.startswith("https://"):
        # Check if it's a video URL
        url_lower = input_str.lower()
        if any(domain in url_lower for domain in VIDEO_DOMAINS):
            return "video_url"
        return "url"

    # Check for file or directory (local paths)
    path = Path(input_str)
    if path.exists():
        if path.is_dir():
            # Check if directory contains images
            has_images = any(
                p.suffix.lower() in IMAGE_EXTENSIONS
                for p in path.iterdir()
                if p.is_file()
            )
            if has_images:
                return "image"
            return "directory"
        elif path.is_file():
            # Check if it's an image file
            if path.suffix.lower() in IMAGE_EXTENSIONS:
                return "image"
            # Check if it's a video file
            if path.suffix.lower() in VIDEO_EXTENSIONS:
                return "video_url"
            return "file"

    return "unknown"


def route_input(
    input_path: str,
    input_type: InputType,
    mode: str = "fidelity",
    model: str = "anthropic/claude-sonnet-4",
    generate_annotations: bool = True,
    verbose: bool = False,
) -> str:
    """Route input to appropriate pipeline and process.

    Args:
        input_path: The input path (URL, file, or directory)
        input_type: The detected input type
        mode: Processing mode (fidelity, concise, raw)
        model: LLM model to use
        generate_annotations: Whether to generate AI annotations
        verbose: Enable verbose output

    Returns:
        Processed content as Markdown string
    """
    pipeline_kwargs = dict(
        mode=mode,
        model=model,
        generate_annotations=generate_annotations,
        verbose=verbose,
    )

    if input_type == "video_url":
        from kb_tool.pipelines.video import VideoPipeline

        pipeline = VideoPipeline(**pipeline_kwargs)
    elif input_type == "image":
        from kb_tool.pipelines.ocr import OCRPipeline

        pipeline = OCRPipeline(
            generate_annotations=generate_annotations,
            model=model,
            verbose=verbose,
        )
    elif input_type == "file":
        # Non-image files — could be PDF, doc, etc.
        # For now, try OCR pipeline (works for scanned docs)
        from kb_tool.pipelines.ocr import OCRPipeline

        pipeline = OCRPipeline(
            generate_annotations=generate_annotations,
            model=model,
            verbose=verbose,
        )
    else:
        # Default: article pipeline (handles url, directory)
        from kb_tool.pipelines.article import ArticlePipeline

        pipeline = ArticlePipeline(**pipeline_kwargs)

    return pipeline.process(input_path, {"mode": mode})


def route_inputs(
    inputs: list[str],
    mode: str = "fidelity",
    model: str = "anthropic/claude-sonnet-4",
    generate_annotations: bool = True,
    verbose: bool = False,
) -> dict[str, str]:
    """Route multiple mixed inputs to appropriate pipelines and process.

    Args:
        inputs: List of input strings (URLs, file paths, directory paths, etc.)
        mode: Processing mode (fidelity, concise, raw)
        model: LLM model to use
        generate_annotations: Whether to generate AI annotations
        verbose: Enable verbose output

    Returns:
        Dictionary mapping input string to processed markdown result
    """
    results: dict[str, str] = {}

    for input_str in inputs:
        input_type = detect_input_type(input_str)
        result = route_input(
            input_path=input_str,
            input_type=input_type,
            mode=mode,
            model=model,
            generate_annotations=generate_annotations,
            verbose=verbose,
        )
        results[input_str] = result

    return results
