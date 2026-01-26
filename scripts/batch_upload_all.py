#!/usr/bin/env python3
"""
批量上传所有文章到 Notion
从 results.json 读取文件列表并逐个上传
"""

import json
import sys
import os
from pathlib import Path

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractor import ArticleExtractor
from src.notion_client import NotionDatabase, Article
from src.file_tracker import FileTracker


def batch_upload_from_results(results_file: str = "results.json", force: bool = False, skip_existing: bool = True):
    """
    从 results.json 批量上传所有文章
    
    Args:
        results_file: results.json 文件路径
        force: 强制重新处理（忽略去重）
        skip_existing: 跳过已处理的文件
    """
    print("="*80)
    print("批量上传所有文章到 Notion")
    print("="*80)
    
    # 读取 results.json
    if not os.path.exists(results_file):
        print(f"\n✗ 文件不存在: {results_file}")
        sys.exit(1)
    
    with open(results_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    print(f"\n总文章数: {len(results)}")
    print(f"模式: {'强制重新上传' if force else '跳过已上传文件' if skip_existing else '检查每个文件'}")
    print("-"*80)
    
    # 初始化
    tracker = FileTracker()
    notion = NotionDatabase()
    extractor = ArticleExtractor()
    
    # 统计
    total = len(results)
    uploaded = 0
    skipped = 0
    failed = 0
    
    # 逐个处理
    for idx, result in enumerate(results, 1):
        file_path = result.get("file", "")
        title = result.get("title", "未知文章")
        
        print(f"\n[{idx}/{total}] {title}")
        print("-"*80)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"  ✗ 文件不存在: {file_path}")
            failed += 1
            continue
        
        pdf_file = Path(file_path)
        
        # 检查是否已处理
        if skip_existing and not force and tracker.is_processed(pdf_file):
            record = tracker.get_record(pdf_file)
            print(f"  ⊘ 已上传，跳过")
            print(f"  处理时间: {record.get('processed_at', 'N/A')}")
            print(f"  Notion ID: {record.get('notion_article_id', 'N/A')[:16]}...")
            skipped += 1
            continue
        
        # 上传文章
        try:
            # 计算 MD5
            md5 = tracker.calculate_md5(pdf_file)
            
            # 提取文本
            print(f"  [1/4] 提取文本...")
            full_text = extractor.extract_text_from_pdf(pdf_file)
            print(f"    ✓ {len(full_text)} 字符")
            
            # 提取观点和证据
            print(f"  [2/4] 提取观点和证据...")
            claims, evidences = extractor.process_pdf_with_evidence(pdf_file)
            print(f"    ✓ 观点: {len(claims)} 个")
            print(f"    ✓ 证据: {len(evidences)} 个")
            
            # 上传文章
            print(f"  [3/4] 上传文章...")
            article = Article(
                title=title,
                content="",  # PDF 格式，不上传文本
                file_path=str(pdf_file),
                file_md5=md5,
                file_size=pdf_file.stat().st_size
            )
            article_page = notion.add_article(article)
            article_id = article_page["id"]
            print(f"    ✓ Notion ID: {article_id[:16]}...")
            
            # 上传观点和证据
            print(f"  [4/4] 上传观点和证据...")
            for claim in claims:
                claim.source_title = title
                notion.add_claim(claim)
            
            for evidence in evidences:
                evidence.source_title = title
                notion.add_evidence(evidence)
            
            print(f"    ✓ 观点: {len(claims)} 个")
            print(f"    ✓ 证据: {len(evidences)} 个")
            
            # 记录处理结果
            tracker.mark_processed(
                file_path=pdf_file,
                notion_article_id=article_id,
                claims_count=len(claims),
                evidence_count=len(evidences)
            )
            
            uploaded += 1
            print(f"  ✅ 上传成功")
            
        except Exception as e:
            print(f"  ✗ 上传失败: {str(e)}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    # 打印统计
    print("\n" + "="*80)
    print("批量上传完成！")
    print("="*80)
    print(f"  总文章数: {total}")
    print(f"  成功上传: {uploaded}")
    print(f"  已跳过: {skipped}")
    print(f"  失败: {failed}")
    print("="*80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="批量上传所有文章到 Notion")
    parser.add_argument("--results", default="results.json", help="results.json 文件路径")
    parser.add_argument("--force", action="store_true", help="强制重新上传（忽略去重）")
    parser.add_argument("--no-skip", action="store_true", help="不跳过已上传的文件")
    
    args = parser.parse_args()
    
    batch_upload_from_results(
        results_file=args.results,
        force=args.force,
        skip_existing=not args.no_skip
    )
