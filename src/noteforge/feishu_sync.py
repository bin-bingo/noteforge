#!/usr/bin/env python3
"""飞书文档同步模块 - 将 Markdown 笔记同步到飞书云文档"""

import os
from pathlib import Path
from typing import Optional

def sync_to_feishu(
    content: str,
    title: str,
    folder_token: Optional[str] = None,
    parent_doc_token: Optional[str] = None
) -> dict:
    """
    同步 Markdown 内容到飞书文档
    
    Args:
        content: Markdown 内容
        title: 文档标题
        folder_token: 目标文件夹 token（可选，默认到根目录）
        parent_doc_token: 父文档 token（可选，用于创建子文档）
    
    Returns:
        {
            "doc_token": "xxx",
            "doc_url": "https://feishu.cn/docx/xxx",
            "status": "success" | "error",
            "message": "错误信息（如果有）"
        }
    """
    try:
        # 使用 feishu_doc tool 创建文档
        # 这里调用 feishu_doc 的 create 或 write action
        from feishu_doc import feishu_doc
        
        # 创建文档
        result = feishu_doc(
            action="create",
            title=title,
            content=content,
            folder_token=folder_token
        )
        
        return {
            "doc_token": result.get("doc_token"),
            "doc_url": f"https://feishu.cn/docx/{result.get('doc_token')}",
            "status": "success",
            "message": "同步成功"
        }
        
    except Exception as e:
        return {
            "doc_token": None,
            "doc_url": None,
            "status": "error",
            "message": str(e)
        }

def upload_to_feishu_drive(
    file_path: str,
    folder_token: Optional[str] = None
) -> dict:
    """
    上传文件到飞书云盘
    
    Args:
        file_path: 本地文件路径
        folder_token: 目标文件夹 token（可选）
    
    Returns:
        {
            "file_token": "xxx",
            "file_url": "https://feishu.cn/drive/xxx",
            "status": "success" | "error"
        }
    """
    try:
        from feishu_drive import feishu_drive
        
        # 上传文件
        result = feishu_drive(
            action="upload",
            file_path=file_path,
            folder_token=folder_token
        )
        
        return {
            "file_token": result.get("file_token"),
            "file_url": result.get("file_url"),
            "status": "success"
        }
        
    except Exception as e:
        return {
            "file_token": None,
            "file_url": None,
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    # 测试
    result = sync_to_feishu("# 测试文档\n内容", "测试标题")
    print(result)
