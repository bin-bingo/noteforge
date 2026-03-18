"""OCR pipeline: image(s) → structured Markdown.

Supports single image or directory of images.
Uses RapidOCR (ONNX) as primary backend, PaddleOCR as optional alternative.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from kb_tool.pipelines.base import Pipeline

# Supported image extensions
IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"})

OCREngine = Literal["rapidocr", "paddleocr", "auto"]


@dataclass
class OCRResult:
    """Result from OCR processing a single image."""

    image_path: str
    text_blocks: list[tuple[str, float]] = field(default_factory=list)  # (text, confidence)
    elapsed_ms: float = 0.0
    error: str | None = None

    @property
    def full_text(self) -> str:
        """Combine all text blocks into a single string."""
        return "\n".join(text for text, _ in self.text_blocks)

    @property
    def avg_confidence(self) -> float:
        """Average confidence across all text blocks."""
        if not self.text_blocks:
            return 0.0
        return sum(score for _, score in self.text_blocks) / len(self.text_blocks)


class _RapidOCREngine:
    """RapidOCR ONNX backend — fast, CPU-friendly, no GPU required."""

    def __init__(self, lang: str = "ch"):
        self.lang = lang
        self._engine = None

    def _ensure_loaded(self):
        if self._engine is None:
            from rapidocr_onnxruntime import RapidOCR

            self._engine = RapidOCR()

    def recognize(self, image_path: str) -> OCRResult:
        """Run OCR on a single image."""
        self._ensure_loaded()
        result = OCRResult(image_path=image_path)
        start = time.monotonic()

        try:
            raw_results, elapse = self._engine(image_path)
            result.elapsed_ms = (elapse[0] if isinstance(elapse, list) else elapse) * 1000

            if raw_results:
                for item in raw_results:
                    # RapidOCR returns: [bbox, text, confidence]
                    _bbox, text, score = item[0], item[1], item[2]
                    if text.strip():
                        result.text_blocks.append((text.strip(), float(score)))
        except Exception as e:
            result.error = str(e)
            result.elapsed_ms = (time.monotonic() - start) * 1000

        return result


class _PaddleOCREngine:
    """PaddleOCR 3.x backend — higher accuracy, may need GPU for best performance."""

    def __init__(self, lang: str = "ch"):
        self.lang = lang
        self._engine = None

    def _ensure_loaded(self):
        if self._engine is None:
            from paddleocr import PaddleOCR

            self._engine = PaddleOCR(
                lang=self.lang,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )

    def recognize(self, image_path: str) -> OCRResult:
        """Run OCR on a single image."""
        self._ensure_loaded()
        result = OCRResult(image_path=image_path)
        start = time.monotonic()

        try:
            results = self._engine.predict(image_path)
            result.elapsed_ms = (time.monotonic() - start) * 1000

            for r in results:
                texts = getattr(r, "rec_texts", [])
                scores = getattr(r, "rec_scores", [])
                for text, score in zip(texts, scores):
                    if text.strip():
                        result.text_blocks.append((text.strip(), float(score)))
        except NotImplementedError as e:
            # PaddlePaddle PIR bug on CPU-only environments
            result.error = f"PaddleOCR not supported on this platform: {e}"
            result.elapsed_ms = (time.monotonic() - start) * 1000
        except Exception as e:
            result.error = str(e)
            result.elapsed_ms = (time.monotonic() - start) * 1000

        return result


def _create_engine(engine_name: OCREngine, lang: str = "ch"):
    """Create an OCR engine instance.

    Args:
        engine_name: Engine type ('rapidocr', 'paddleocr', or 'auto')
        lang: Language code

    Returns:
        OCR engine instance
    """
    if engine_name == "rapidocr":
        return _RapidOCREngine(lang=lang)
    elif engine_name == "paddleocr":
        return _PaddleOCREngine(lang=lang)
    elif engine_name == "auto":
        # Try RapidOCR first (more reliable on CPU)
        try:
            engine = _RapidOCREngine(lang=lang)
            engine._ensure_loaded()
            return engine
        except ImportError:
            pass

        # Fallback to PaddleOCR
        try:
            engine = _PaddleOCREngine(lang=lang)
            engine._ensure_loaded()
            return engine
        except ImportError:
            pass

        raise ImportError(
            "No OCR engine available. Install one of:\n"
            "  pip install 'kb-tool[ocr]'           # RapidOCR (recommended)\n"
            "  pip install paddleocr paddlepaddle   # PaddleOCR"
        )

    raise ValueError(f"Unknown engine: {engine_name}")


def _collect_images(input_path: str) -> list[str]:
    """Collect image file paths from a single file or directory.

    Args:
        input_path: Path to an image file or directory containing images

    Returns:
        Sorted list of image file paths
    """
    path = Path(input_path)

    if path.is_file():
        if path.suffix.lower() in IMAGE_EXTENSIONS:
            return [str(path)]
        raise ValueError(f"Not a supported image file: {path.suffix}")

    if path.is_dir():
        images = sorted(
            str(p)
            for p in path.rglob("*")
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
        )
        if not images:
            raise ValueError(f"No image files found in directory: {input_path}")
        return images

    raise FileNotFoundError(f"Path does not exist: {input_path}")


def _format_ocr_markdown(
    results: list[OCRResult],
    source: str,
    llm_corrected: str | None = None,
) -> str:
    """Format OCR results as a Markdown document.

    Args:
        results: List of OCR results from each image
        source: Source path or description
        llm_corrected: Optional LLM-corrected/structured text

    Returns:
        Markdown document string
    """
    from datetime import date

    today = date.today().isoformat()
    has_multiple = len(results) > 1

    lines = [
        "---",
        f'title: "OCR: {os.path.basename(source)}"',
        f"source: \"{source}\"",
        "type: ocr",
        f"created: {today}",
        f"images: {len(results)}",
        "tags: [\"ocr\"]",
        "---",
        "",
    ]

    if llm_corrected:
        # LLM post-processed output takes priority
        lines.append(llm_corrected)
        lines.append("")
    else:
        # Raw OCR output
        for i, result in enumerate(results, 1):
            if has_multiple:
                img_name = os.path.basename(result.image_path)
                lines.append(f"## 图片 {i}: {img_name}")
                lines.append("")

            if result.error:
                lines.append(f"> ⚠️ OCR 错误: {result.error}")
                lines.append("")
                continue

            if not result.text_blocks:
                lines.append("*未识别到文字*")
                lines.append("")
                continue

            # Write recognized text
            for text, score in result.text_blocks:
                lines.append(text)

            lines.append("")

            # Metadata footer for each image
            lines.append(
                f"> 📊 识别 {len(result.text_blocks)} 段文字 | "
                f"平均置信度 {result.avg_confidence:.1%} | "
                f"耗时 {result.elapsed_ms:.0f}ms"
            )
            lines.append("")

    # Overall summary
    total_blocks = sum(len(r.text_blocks) for r in results)
    total_errors = sum(1 for r in results if r.error)
    avg_conf = (
        sum(r.avg_confidence for r in results if not r.error) / max(len(results) - total_errors, 1)
    )

    lines.extend([
        "---",
        "",
        f"> 📝 **OCR 总结**: {len(results)} 张图片, {total_blocks} 段文字, "
        f"平均置信度 {avg_conf:.1%}",
    ])
    if total_errors:
        lines.append(f"> ⚠️ {total_errors} 张图片处理失败")

    return "\n".join(lines)


class OCRPipeline(Pipeline):
    """Process images into structured Markdown via OCR.

    Supports:
        - Single image file (png, jpg, jpeg, webp, bmp, tiff)
        - Directory of images (recursive)
        - Multiple OCR backends (RapidOCR, PaddleOCR)
        - Optional LLM post-processing for error correction

    Example:
        >>> pipeline = OCRPipeline(engine="rapidocr", lang="ch")
        >>> md = pipeline.process("/path/to/image.png")
        >>> md = pipeline.process("/path/to/images/", config={"use_llm": True})
    """

    def __init__(
        self,
        engine: OCREngine = "auto",
        lang: str = "ch",
        generate_annotations: bool = False,
        model: str = "anthropic/claude-sonnet-4",
        verbose: bool = False,
    ):
        """Initialize OCR pipeline.

        Args:
            engine: OCR backend ('rapidocr', 'paddleocr', or 'auto')
            lang: Language code ('ch' for Chinese, 'en' for English)
            generate_annotations: Whether to use LLM for post-processing
            model: LLM model for post-processing
            verbose: Enable verbose output
        """
        self.engine_name = engine
        self.lang = lang
        self.generate_ann = generate_annotations
        self.model = model
        self.verbose = verbose
        self._engine = None

    def _get_engine(self):
        """Lazy-load OCR engine."""
        if self._engine is None:
            self._engine = _create_engine(self.engine_name, self.lang)
        return self._engine

    def process(self, input_data: str, config: dict | None = None) -> str:
        """Process image(s) into Markdown.

        Args:
            input_data: Path to image file or directory
            config: Optional config dict with keys:
                - use_llm (bool): Enable LLM post-processing
                - engine (str): Override OCR engine
                - lang (str): Override language

        Returns:
            Markdown document with OCR results
        """
        config = config or {}

        # Allow config overrides
        use_llm = config.get("use_llm", config.get("generate_annotations", self.generate_ann))
        engine_name = config.get("engine", self.engine_name)

        # Step 1: Collect images
        try:
            image_paths = _collect_images(input_data)
        except (ValueError, FileNotFoundError) as e:
            return f"# OCR 处理失败\n\n{e}\n"

        if self.verbose:
            print(f"Found {len(image_paths)} image(s) to process")

        # Step 2: Run OCR on each image
        engine = _create_engine(engine_name, self.lang)
        results: list[OCRResult] = []

        for img_path in image_paths:
            if self.verbose:
                print(f"Processing: {os.path.basename(img_path)}")
            result = engine.recognize(img_path)
            results.append(result)

        # Step 3: Optional LLM post-processing
        llm_corrected = None
        if use_llm and any(r.text_blocks for r in results):
            llm_corrected = self._llm_postprocess(results)

        # Step 4: Format output
        return _format_ocr_markdown(results, input_data, llm_corrected)

    def _llm_postprocess(self, results: list[OCRResult]) -> str | None:
        """Use LLM to correct and structure OCR output.

        Args:
            results: OCR results to post-process

        Returns:
            Corrected Markdown text, or None on failure
        """
        try:
            from kb_tool.llm import _get_client, get_config

            client = _get_client()
            config = get_config()
            model_id = self.model or config.llm.api_model

            # Combine raw OCR text
            raw_text = "\n\n---\n\n".join(
                f"[图片: {os.path.basename(r.image_path)}]\n{r.full_text}"
                for r in results
                if r.text_blocks
            )

            prompt = f"""你是 OCR 文本校对助手。以下是从图片中 OCR 识别的原始文本，可能存在识别错误。

请完成以下任务：
1. 修正明显的 OCR 识别错误（如错字、断行、乱码）
2. 恢复原始文档结构（标题、段落、列表等）
3. 输出干净的 Markdown 格式

不要添加原文中没有的内容。只做修正和结构化。

原始 OCR 文本：
{raw_text[:6000]}

请输出修正后的 Markdown："""

            response = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=2048,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            if self.verbose:
                print(f"LLM post-processing failed: {e}")
            return None
