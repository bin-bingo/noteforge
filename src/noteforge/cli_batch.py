"""批量处理命令 - kb batch"""

import typer
from pathlib import Path
from typing import Optional
from datetime import datetime
from rich.console import Console

console = Console()

def batch_process(
    inputs: list[str],
    mode: str = "fidelity",
    output_dir: Optional[Path] = None,
    model: str = "anthropic/claude-sonnet-4",
    no_annotations: bool = False,
    verbose: bool = False,
):
    """批量处理多个输入（URL/文件）"""
    from kb_tool.router import detect_input_type, route_input
    
    output_dir = output_dir or Path.cwd()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    console.print(f"[bold blue]📦 批量处理中[/bold blue] - 共 {len(inputs)} 个输入\n")
    
    success_count = 0
    for i, input_item in enumerate(inputs, 1):
        try:
            console.print(f"[cyan][{i}/{len(inputs)}][/cyan] 处理：{input_item}")
            
            input_type = detect_input_type(input_item)
            result = route_input(
                input_path=input_item,
                input_type=input_type,
                mode=mode,
                model=model,
                generate_annotations=not no_annotations,
                verbose=verbose,
            )
            
            if result:
                # 生成输出文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_name = "".join(c for c in str(result.get("title", "note")[:50]) if c.isalnum() or c in " -_")
                output_file = output_dir / f"{timestamp}_{safe_name}.md"
                
                # 写入文件
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(result)
                
                console.print(f"  ✅ 已保存：{output_file}")
                success_count += 1
            else:
                console.print("  ❌ 处理失败")
                
        except Exception as e:
            console.print(f"  ❌ 错误：{e}")
            if verbose:
                import traceback
                traceback.print_exc()
    
    console.print(f"\n[bold green]✅ 完成：{success_count}/{len(inputs)} 个成功[/bold green]")

if __name__ == "__main__":
    # 测试
    batch_process(["https://example.com"])
