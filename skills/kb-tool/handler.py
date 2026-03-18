#!/usr/bin/env python3
"""kb-tool OpenClaw Skill 执行器 - 在飞书中调用 kb CLI"""

import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

def process_input(input_text: str, images: list = None, mode: str = "fidelity") -> str:
    """
    处理用户输入（链接/文本/图片）
    
    Args:
        input_text: 用户输入的文本（URL 或文本）
        images: 图片列表（如果有）
        mode: 处理模式 (fidelity/concise/raw)
    
    Returns:
        Markdown 格式的笔记
    """
    # 检测输入类型
    input_type = detect_input_type(input_text)
    
    if input_type == "url":
        # 文章/视频链接处理
        cmd = ["kb", input_text, "--mode", mode]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout
    
    elif input_type == "image" or images:
        # 图片 OCR 处理
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            # 保存临时图片
            img_paths = []
            for i, img_data in enumerate(images or []):
                img_path = tmpdir / f"image_{i}.png"
                # TODO: 解析图片数据
                img_paths.append(str(img_path))
            
            # 调用 kb CLI 处理图片
            cmd = ["kb", "--mode", mode] + img_paths
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.stdout
    
    elif input_type == "text":
        # 纯文本 - 可能是多个 URL 或混合输入
        parts = input_text.split()
        if len(parts) > 1:
            # 多个 URL，批量处理
            cmd = ["kb", "--batch"] + parts
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.stdout
        else:
            # 单个 URL
            cmd = ["kb", input_text, "--mode", mode]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.stdout
    
    return "无法识别输入类型"

def detect_input_type(text: str) -> str:
    """检测输入类型：url, image, text"""
    if not text.strip():
        return "image"
    
    # 检测 URL
    if text.strip().startswith(("http://", "https://")):
        return "url"
    
    # 检测是否包含 URL
    if "://" in text:
        return "text"  # 可能是多个 URL
    
    # 默认作文本
    return "text"

if __name__ == "__main__":
    # 测试
    print(process_input("https://example.com"))
