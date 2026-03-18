"""CLI entry point for kb-tool."""

import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.markdown import Markdown

from kb_tool import __version__
from kb_tool.router import detect_input_type, route_input, route_inputs
from kb_tool.llm import generate_annotations, LLMError

console = Console()

# Known subcommands that should NOT be treated as input
_SUBCOMMANDS = {"config", "help", "main", "batch"}


def _patch_argv() -> None:
    """Patch sys.argv so `kb <url>` becomes `kb main <url>`.

    When the first CLI arg after `kb` is not a known subcommand,
    insert 'main' so typer routes to the default processing command.
    Handles: kb --version, kb -V, kb config show, kb <url> etc.
    """
    if len(sys.argv) < 2:
        return
    first = sys.argv[1]
    # Don't patch if it's already a subcommand
    if first in _SUBCOMMANDS:
        return
    # Always inject 'main' - whether first arg is an option or input
    sys.argv.insert(1, "main")


_patch_argv()


# ── Helpers ────────────────────────────────────────────────────────


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold blue]kb-tool[/bold blue] v{__version__}")
        raise typer.Exit()


def completion_callback(value: bool) -> None:
    """Print shell completion instructions."""
    if value:
        console.print(
            Panel(
                """[bold]Shell Completion[/bold]

To enable tab-completion for [cyan]kb[/cyan], run:

  [green]# Bash[/green]
  eval "$(_KB_COMPLETE=bash_source kb)"

  [green]# Zsh[/green]
  eval "$(_KB_COMPLETE=zsh_source kb)"

  [green]# Fish[/green]
  eval "$(_KB_COMPLETE=fish_source kb)"

Add to your shell config ([dim].bashrc / .zshrc / config.fish[/dim]) for persistence.
""",
                title="🐚 Shell Completion",
                border_style="blue",
            )
        )
        raise typer.Exit()


# ── App ────────────────────────────────────────────────────────────

app = typer.Typer(
    name="kb",
    help=(
        "[bold blue]kb-tool[/bold blue] — 扔进材料，输出笔记\n\n"
        "零配置的个人知识库构建工具。自动识别输入类型，"
        "提取正文并生成 AI 旁注，输出结构化 Markdown。\n\n"
        "[bold]示例：[/bold]\n"
        "  kb https://example.com/article\n"
        "  kb https://example.com/article -o note.md\n"
        "  kb /path/to/image.png\n"
        "  kb https://youtube.com/watch?v=xxx -m concise\n"
        "  kb config show\n"
        "  kb config set llm.api_model anthropic/claude-sonnet-4"
    ),
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)


# ── Main command ───────────────────────────────────────────────────


@app.command()
def main(
    input: str = typer.Argument(
        ...,
        help="输入：URL、文件路径、目录路径或视频链接",
        metavar="<input>",
    ),
    mode: str = typer.Option(
        "fidelity",
        "--mode",
        "-m",
        help="处理模式：[cyan]fidelity[/cyan]（原文+旁注）、[cyan]concise[/cyan]（提炼）、[cyan]raw[/cyan]（纯原文）",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径（默认输出到终端）",
    ),
    model: str = typer.Option(
        "anthropic/claude-sonnet-4",
        "--model",
        help="LLM 模型 ID（通过 OpenRouter）",
    ),
    no_annotations: bool = typer.Option(
        False,
        "--no-annotations",
        help="跳过 AI 旁注生成",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="显示详细处理信息",
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="显示版本号",
    ),
    show_completion: Optional[bool] = typer.Option(
        None,
        "--show-completion",
        callback=completion_callback,
        is_eager=True,
        help="显示 Shell 补全安装方法",
    ),
) -> None:
    """将输入材料转换为知识库笔记。

    支持的输入类型：
      • 文章 URL — 提取正文 + AI 旁注
      • 视频 URL — 提取字幕 + 总结（YouTube 已支持，B站/抖音开发中）
      • 本地文件 — PDF / Markdown / 文本文件
      • 目录 — 批量处理目录内所有文件
    """
    # ── Detect input ──
    console.print(f"\n[dim]🔍 识别输入类型...[/dim]", end="")
    input_type = detect_input_type(input)

    if input_type == "url":
        console.print(" [green]文章链接[/green]")
    elif input_type == "video_url":
        console.print(" [green]视频链接[/green]")
    elif input_type == "file":
        console.print(" [green]文件[/green]")
    elif input_type == "directory":
        console.print(" [green]目录[/green]")
    else:
        console.print(" [red]无法识别[/red]")
        console.print(
            f"\n[red]✗[/red] 无法识别输入类型：[bold]{input}[/bold]\n"
            f"  [dim]支持：URL、文件路径、目录路径[/dim]\n"
        )
        raise typer.Exit(code=1)

    if verbose:
        console.print(f"  [dim]输入: {input}[/dim]")
        console.print(f"  [dim]模式: {mode}[/dim]")

    # ── Process ──
    progress_messages = {
        "url": "正在提取文章正文...",
        "video_url": "正在提取视频字幕...",
        "file": "正在处理文件...",
        "directory": "正在批量处理...",
    }

    try:
        with Progress(
            SpinnerColumn(style="blue"),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                progress_messages.get(input_type, "正在处理..."),
                total=None,
            )

            result = route_input(
                input_path=input,
                input_type=input_type,
                mode=mode,
                model=model,
                generate_annotations=not no_annotations,
                verbose=verbose,
            )

            # Show annotation progress if applicable
            if not no_annotations and mode != "raw":
                progress.update(task, description="正在生成 AI 旁注...")
                import time
                time.sleep(0.3)  # Brief visual feedback

            progress.update(task, description="[green]✓ 处理完成", completed=True)

        # ── Output ──
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(result, encoding="utf-8")
            console.print(
                f"\n[green]✓[/green] 已保存到 [bold]{output}[/bold]"
                f"  [dim]({len(result)} 字符)[/dim]\n"
            )
        else:
            console.print()
            md = Markdown(result)
            console.print(md)
            console.print()

    except LLMError as e:
        console.print(f"\n[red]✗ LLM 错误：{e}[/red]\n")
        console.print(
            f"  [dim]提示：请检查 [cyan]OPENROUTER_API_KEY[/cyan] 环境变量[/dim]\n"
        )
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        console.print(f"\n[yellow]⚠ 已取消[/yellow]\n")
        raise typer.Exit(code=130)
    except Exception as e:
        console.print(f"\n[red]✗ 错误：{e}[/red]\n")
        if verbose:
            import traceback
            console.print_exception()
        raise typer.Exit(code=1)


# ── Config subcommand ──────────────────────────────────────────────

config_app = typer.Typer(
    name="config",
    help="显示或修改 kb-tool 配置",
    rich_markup_mode="rich",
)
app.add_typer(config_app, name="config")


@config_app.command("show")
def config_show() -> None:
    """显示当前配置"""
    from kb_tool.config import get_config

    cfg = get_config()
    config_path = Path.home() / ".kb" / "config.yaml"

    console.print()
    console.print(Panel("[bold]kb-tool 配置[/bold]", border_style="blue"))

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="cyan")
    table.add_column("Value")

    table.add_row(
        "配置文件",
        str(config_path) if config_path.exists() else f"[dim]{config_path} (未创建)[/dim]",
    )
    table.add_row("─" * 30, "─" * 40)

    table.add_row("[bold]LLM[/bold]", "")
    table.add_row("  Provider", cfg.llm.api_provider)
    table.add_row("  Model", cfg.llm.api_model)
    table.add_row("  API Key", "✓ 已设置" if cfg.llm.api_key else "[red]✗ 未设置[/red]")
    table.add_row("  Timeout", f"{cfg.llm.timeout}s")
    table.add_row("", "")

    table.add_row("[bold]输出[/bold]", "")
    table.add_row("  目录", str(cfg.output.dir))
    table.add_row("  模式", cfg.output.mode)

    console.print(table)
    console.print()

    if not cfg.llm.api_key:
        console.print(
            "[yellow]⚠[/yellow] 未设置 API Key。运行：\n"
            '  [cyan]export OPENROUTER_API_KEY="sk-or-..."[/cyan]\n'
        )


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="配置键（如 llm.api_model、output.mode）"),
    value: str = typer.Argument(..., help="配置值"),
) -> None:
    """设置配置项（写入 ~/.kb/config.yaml）"""
    import yaml

    config_path = Path.home() / ".kb" / "config.yaml"

    if config_path.exists():
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    else:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {}

    keys = key.split(".")
    target = data
    for k in keys[:-1]:
        if k not in target:
            target[k] = {}
        target = target[k]

    try:
        parsed_value = yaml.safe_load(value)
    except Exception:
        parsed_value = value
    target[keys[-1]] = parsed_value

    config_path.write_text(
        yaml.dump(data, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )
    console.print(f"[green]✓[/green] 已设置 [cyan]{key}[/cyan] = [bold]{value}[/bold]")
    console.print(f"  [dim]配置文件: {config_path}[/dim]\n")

    from kb_tool.config import reset_config
    reset_config()


@config_app.command("init")
def config_init(
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的配置文件"),
) -> None:
    """创建默认配置文件 (~/.kb/config.yaml)"""
    config_path = Path.home() / ".kb" / "config.yaml"

    if config_path.exists() and not force:
        console.print(
            f"[yellow]⚠[/yellow] 配置文件已存在：{config_path}\n"
            f"  使用 [cyan]--force[/cyan] 覆盖\n"
        )
        raise typer.Exit(code=1)

    config_path.parent.mkdir(parents=True, exist_ok=True)

    default_config = """# kb-tool 配置文件
# 文档：https://github.com/kb-tool/kb-tool

llm:
  provider: api
  api_provider: openrouter
  api_model: anthropic/claude-sonnet-4
  # api_key: sk-or-...  # 或使用环境变量 OPENROUTER_API_KEY
  timeout: 30.0

output:
  dir: ~/.kb/vault/
  mode: fidelity  # fidelity | concise | raw
"""

    config_path.write_text(default_config, encoding="utf-8")
    console.print(
        f"[green]✓[/green] 配置文件已创建：[bold]{config_path}[/bold]\n"
    )


if __name__ == "__main__":
    app()
