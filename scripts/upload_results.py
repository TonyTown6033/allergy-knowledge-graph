#!/usr/bin/env python3
"""
将 results.json 中的观点批量上传到 Notion
"""

import json
import sys
from pathlib import Path

from src.notion_client import NotionDatabase, Claim, Polarity


def upload_results_to_notion(json_file: str):
    """
    从 JSON 文件读取提取结果并上传到 Notion
    
    Args:
        json_file: results.json 文件路径
    """
    # 读取 JSON 文件
    with open(json_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # 初始化 Notion 客户端
    notion = NotionDatabase()
    
    # 统计信息
    total_files = len(results)
    total_claims = 0
    success_count = 0
    error_count = 0
    
    print(f"开始上传 {total_files} 个文件的提取结果到 Notion...\n")
    
    # 遍历每个文件的结果
    for file_result in results:
        file_name = file_result.get("title", file_result.get("file", "未知文件"))
        claims = file_result.get("claims", [])
        
        if not claims:
            print(f"⊘ {file_name}: 无观点数据")
            continue
        
        print(f"📄 {file_name}: {len(claims)} 个观点")
        total_claims += len(claims)
        
        # 遍历该文件的所有观点
        for i, claim_data in enumerate(claims, 1):
            try:
                # 创建 Claim 对象
                claim = Claim(
                    title=claim_data["title"],
                    content=claim_data["content"],
                    polarity=Polarity(claim_data["polarity"]),
                    mapped_nodes=claim_data.get("mapped_nodes", []),
                    evidence_ids=claim_data.get("evidence_ids", []),
                    source_title=file_name,
                    source_url=claim_data.get("source_url")
                )
                
                # 上传到 Notion
                notion.add_claim(claim)
                success_count += 1
                print(f"  ✓ 观点 {i}: {claim.title[:50]}...")
                
            except Exception as e:
                error_count += 1
                print(f"  ✗ 观点 {i} 上传失败: {str(e)}")
        
        print()  # 空行分隔
    
    # 打印统计结果
    print("=" * 60)
    print(f"上传完成！")
    print(f"  总文件数: {total_files}")
    print(f"  总观点数: {total_claims}")
    print(f"  成功上传: {success_count}")
    print(f"  失败数量: {error_count}")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python upload_results.py <results.json>")
        print("示例: python upload_results.py results.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    if not Path(json_file).exists():
        print(f"错误: 文件不存在 - {json_file}")
        sys.exit(1)
    
    upload_results_to_notion(json_file)
