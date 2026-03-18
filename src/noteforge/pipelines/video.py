"""Video pipeline: URL → subtitle extraction → LLM summary → Markdown.

Supports:
  - YouTube (via yt-dlp subtitles) ✅ ready
  - Bilibili / Douyin 🚧 placeholder (same yt-dlp, needs testing)
"""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from kb_tool.pipelines.base import Pipeline
from kb_tool.llm import LLMError

# ── LLM summary prompt ────────────────────────────────────────────

VIDEO_SUMMARY_PROMPT = """你是一个学习笔记助手。请根据以下视频字幕，生成结构化学习笔记。

视频标题：{title}
视频来源：{url}
视频时长：{duration}

字幕内容：
{transcript}

请严格输出以下 JSON 格式（不要输出其他内容）：
{{
  "summary": "3-5 句话概括视频核心内容",
  "key_points": ["要点1", "要点2", "要点3"],
  "key_data": ["关键数据/数字/引用"],
  "tags": ["标签1", "标签2"],
  "learning_notes": ["学习要点1", "学习要点2"],
  "timestamps": [{{"time": "00:01:30", "note": "关键片段描述"}}]
}}"""


# ── yt-dlp helpers ────────────────────────────────────────────────


def _check_ytdlp() -> bool:
    """Check if yt-dlp is available."""
    return shutil.which("yt-dlp") is not None


def _fetch_video_info(url: str) -> dict | None:
    """Fetch video metadata via yt-dlp --dump-json."""
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-download", url],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return None
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None


def _fetch_subtitles(url: str) -> tuple[str, str, str]:
    """Fetch subtitles via yt-dlp.

    Returns:
        (subtitle_text, title, duration_str)

    Raises:
        RuntimeError: if no subtitles available.
    """
    info = _fetch_video_info(url)
    if info is None:
        raise RuntimeError(f"无法获取视频信息：{url}")

    title = info.get("title", "无标题")
    duration_sec = info.get("duration", 0)
    duration_str = _format_duration(duration_sec)

    # Check if subtitles are available
    subs = info.get("subtitles", {}) or {}
    auto_subs = info.get("automatic_captions", {}) or {}

    # Prefer manual subtitles; fall back to auto-generated
    available = subs if subs else auto_subs

    if not available:
        raise RuntimeError(
            f"视频「{title}」没有可用字幕。\n"
            f"  可能原因：\n"
            f"  • 视频未提供字幕\n"
            f"  • 需要登录才能访问\n"
            f"  • 地区限制\n"
            f"  建议：手动复制字幕或使用其他工具提取。"
        )

    # Download best subtitle (prefer zh > en > first available)
    lang_priority = ["zh-Hans", "zh", "zh-CN", "en"]
    chosen_lang = None
    for lang in lang_priority:
        if lang in available:
            chosen_lang = lang
            break
    if chosen_lang is None:
        chosen_lang = list(available.keys())[0]

    # Download subtitle to temp file
    with tempfile.TemporaryDirectory() as tmpdir:
        sub_path = Path(tmpdir) / "subtitle"
        result = subprocess.run(
            [
                "yt-dlp",
                "--skip-download",
                "--write-sub",
                "--write-auto-sub",
                "--sub-lang", chosen_lang,
                "--sub-format", "vtt",
                "-o", str(sub_path),
                url,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        # Find the downloaded subtitle file
        vtt_files = list(Path(tmpdir).glob("*.vtt"))
        if not vtt_files:
            raise RuntimeError(f"字幕下载失败（语言: {chosen_lang}）")

        raw_text = vtt_files[0].read_text(encoding="utf-8")

    # Clean VTT to plain text
    clean_text = _vtt_to_text(raw_text)

    if not clean_text.strip():
        raise RuntimeError("字幕内容为空")

    return clean_text, title, duration_str


def _transcribe_with_whisper(audio_path: str) -> str:
    """Transcribe audio using faster-whisper (or openai-whisper as fallback)."""
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(audio_path)
        return "\n".join(seg.text for seg in segments)
    except ImportError:
        try:
            import whisper
        except ImportError:
            raise RuntimeError(
                "需要安装 whisper 依赖：\n"
                "  pip install kb-tool[whisper]  # faster-whisper\n"
                "  或\n"
                "  pip install openai-whisper     # openai-whisper"
            )
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        return result["text"]


def _download_audio(url: str) -> str:
    """Download audio from video URL using yt-dlp. Returns path to mp3 file."""
    tmpdir = tempfile.mkdtemp()
    audio_path = Path(tmpdir) / "audio.mp3"
    result = subprocess.run(
        [
            "yt-dlp",
            "-x",
            "--audio-format", "mp3",
            "-o", str(audio_path),
            url,
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode != 0:
        raise RuntimeError(f"音频下载失败：{result.stderr}")

    # yt-dlp may add extension automatically
    if not audio_path.exists():
        candidates = list(Path(tmpdir).glob("audio*"))
        if candidates:
            audio_path = candidates[0]
        else:
            raise RuntimeError("音频文件未找到")

    return str(audio_path)


def _vtt_to_text(vtt_content: str) -> str:
    """Convert VTT subtitle to clean plain text."""
    import re

    lines = []
    for line in vtt_content.split("\n"):
        line = line.strip()
        # Skip VTT headers, timestamps, empty lines
        if not line:
            continue
        if line.startswith("WEBVTT"):
            continue
        if line.startswith("NOTE"):
            continue
        if re.match(r"^\d+$", line):
            continue
        if re.match(r"\d{2}:\d{2}:\d{2}", line):
            continue
        if "-->" in line:
            continue
        # Remove VTT tags like <c>, </c>, etc.
        clean = re.sub(r"<[^>]+>", "", line)
        if clean:
            lines.append(clean)

    return "\n".join(lines)


def _format_duration(seconds: int | float) -> str:
    """Format seconds to HH:MM:SS."""
    seconds = int(seconds)
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


# ── LLM summary ───────────────────────────────────────────────────


def _generate_video_summary(
    title: str,
    url: str,
    duration: str,
    transcript: str,
    model: str = "anthropic/claude-sonnet-4",
) -> dict:
    """Generate structured summary from video transcript."""
    from openai import OpenAI
    from kb_tool.config import get_config

    config = get_config()
    api_key = config.llm.api_key
    if not api_key:
        raise LLMError("OPENROUTER_API_KEY not set")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        timeout=config.llm.timeout,
    )

    # Truncate transcript if too long
    max_len = 12000
    truncated = transcript[:max_len]
    if len(transcript) > max_len:
        truncated += "\n\n[字幕已截断...]"

    prompt = VIDEO_SUMMARY_PROMPT.format(
        title=title or "无标题",
        url=url,
        duration=duration,
        transcript=truncated,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2048,
    )

    text = response.choices[0].message.content.strip()

    # Parse JSON
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    return json.loads(text)


# ── Output formatter ──────────────────────────────────────────────


def _format_video_note(
    title: str,
    url: str,
    duration: str,
    summary_data: dict,
) -> str:
    """Format video summary into Markdown."""
    from datetime import date

    today = date.today().isoformat()
    tags = summary_data.get("tags", [])
    tags_str = ", ".join(f'"{t}"' for t in tags) if tags else ""

    lines = [
        "---",
        f'title: "{title}"',
        f'source: "{url}"',
        "type: video",
        f"created: {today}",
        f"duration: \"{duration}\"",
        f"tags: [{tags_str}]" if tags else "tags: []",
        "---",
        "",
        f"# 🎬 {title}",
        "",
    ]

    # Summary
    summary = summary_data.get("summary", "")
    if summary:
        lines.extend(["> 📝 **视频摘要**", f"> {summary}", ""])

    # Key points
    key_points = summary_data.get("key_points", [])
    if key_points:
        lines.extend(["> 💡 **要点**", ""])
        for p in key_points:
            lines.append(f"> - {p}")
        lines.append("")

    # Key data
    key_data = summary_data.get("key_data", [])
    if key_data:
        lines.extend(["> 📊 **关键数据**", ""])
        for d in key_data:
            lines.append(f"> - {d}")
        lines.append("")

    # Learning notes
    learning = summary_data.get("learning_notes", [])
    if learning:
        lines.extend(["---", "", "## 📖 学习笔记", ""])
        for note in learning:
            lines.append(f"- {note}")
        lines.append("")

    # Timestamps
    timestamps = summary_data.get("timestamps", [])
    if timestamps:
        lines.extend(["---", "", "## ⏱️ 关键时间点", ""])
        for ts in timestamps:
            t = ts.get("time", "")
            n = ts.get("note", "")
            lines.append(f"- **[{t}]** {n}")
        lines.append("")

    return "\n".join(lines)


# ── Pipeline ───────────────────────────────────────────────────────


class VideoPipeline(Pipeline):
    """Extract video subtitles and generate annotated learning notes."""

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
        """Process video URL into annotated Markdown.

        Args:
            input_data: Video URL
            config: Optional config dict

        Returns:
            Markdown document with summary and learning notes.
        """
        url = input_data

        # Check yt-dlp availability
        if not _check_ytdlp():
            return (
                "# ✗ 依赖缺失\n\n"
                "需要安装 yt-dlp 才能处理视频。\n\n"
                "```bash\n"
                "pip install yt-dlp\n"
                "# 或\n"
                "brew install yt-dlp\n"
                "```\n"
            )

        # Determine platform
        platform = self._detect_platform(url)
        if self.verbose:
            print(f"Platform: {platform}")

        # Fetch subtitles
        try:
            transcript, title, duration = _fetch_subtitles(url)
        except RuntimeError as e:
            # Fallback: download audio + whisper transcription
            if self.verbose:
                print(f"字幕不可用，尝试 Whisper 转写: {e}")
            try:
                info = _fetch_video_info(url)
                title = info.get("title", "无标题") if info else "无标题"
                duration_sec = info.get("duration", 0) if info else 0
                duration = _format_duration(duration_sec)

                audio_path = _download_audio(url)
                if self.verbose:
                    print(f"音频已下载: {audio_path}")
                transcript = _transcribe_with_whisper(audio_path)

                # Clean up temp audio
                try:
                    Path(audio_path).unlink()
                    Path(audio_path).parent.rmdir()
                except OSError:
                    pass

                if not transcript.strip():
                    return f"# 转写失败\n\nWhisper 未能识别到任何文字。\n"
            except RuntimeError as whisper_err:
                return f"# 字幕提取失败\n\n{e}\n\nWhisper fallback 也失败了：\n{whisper_err}\n"

        if self.verbose:
            print(f"Title: {title}")
            print(f"Duration: {duration}")
            print(f"Transcript length: {len(transcript)} chars")

        # Generate summary
        if self.generate_ann and self.mode != "raw":
            try:
                summary_data = _generate_video_summary(
                    title=title,
                    url=url,
                    duration=duration,
                    transcript=transcript,
                    model=self.model,
                )
            except Exception as e:
                summary_data = {
                    "summary": f"LLM 总结失败: {e}",
                    "key_points": [],
                    "key_data": [],
                    "tags": [],
                    "learning_notes": [transcript[:500] + "..."],
                    "timestamps": [],
                }
        else:
            summary_data = {
                "summary": "",
                "key_points": [],
                "key_data": [],
                "tags": [],
                "learning_notes": [],
                "timestamps": [],
            }

        return _format_video_note(
            title=title,
            url=url,
            duration=duration,
            summary_data=summary_data,
        )

    @staticmethod
    def _detect_platform(url: str) -> str:
        """Detect video platform from URL."""
        url_lower = url.lower()
        if "youtube.com" in url_lower or "youtu.be" in url_lower:
            return "youtube"
        if "bilibili.com" in url_lower or "b23.tv" in url_lower:
            return "bilibili"
        if "douyin.com" in url_lower or "tiktok.com" in url_lower:
            return "douyin"
        if "vimeo.com" in url_lower:
            return "vimeo"
        return "unknown"
