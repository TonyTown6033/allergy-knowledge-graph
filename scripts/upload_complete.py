#!/usr/bin/env python3
"""
完整上传脚本（带去重）：
1. 检查文件是否已处理（MD5）
2. 上传文章全文到 Notion
3. 提取并上传 Claims 和 Evidence
4. 建立关联关系
"""

import sys
from pathlib import Path
from src.extractor import ArticleExtractor
from src.notion_client import NotionDatabase, Article
from src.file_tracker import FileTracker


def process_pdf_with_dedup(pdf_path: str, force: bool = False):
    """
    处理 PDF 文件（带去重）
    
    Args:
        pdf_path: PDF 文件路径
        force: 强制重新处理（忽略去重）
    """
    print("="*70)
    print("完整知识图谱提取与上传（带去重）")
    print("="*70)
    
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"\n✗ 文件不存在: {pdf_path}")
        sys.exit(1)
    
    print(f"\n📄 文件: {pdf_file.name}")
    print("-"*70)
    
    # 初始化追踪器
    tracker = FileTracker()
    
    # [步骤 1] 检查是否已处理
    print("\n[1/5] 检查文件是否已处理...")
    md5 = tracker.calculate_md5(pdf_file)
    print(f"  文件 MD5: {md5}")
    
    if not force and tracker.is_processed(pdf_file):
        record = tracker.get_record(pdf_file)
        print(f"  ⚠ 文件已处理过")
        print(f"  处理时间: {record.get('processed_at', 'N/A')}")
        print(f"  观点数: {record.get('claims_count', 0)}")
        print(f"  证据数: {record.get('evidence_count', 0)}")
        print(f"  Notion 文章 ID: {record.get('notion_article_id', 'N/A')[:16]}...")
        
        response = input("\n是否重新处理？(y/n): ").strip().lower()
        if response != 'y':
            print("\n跳过处理")
            return
        print("\n强制重新处理...")
    else:
        print("  ✓ 文件未处理，开始提取")
    
    # [步骤 2] 提取文本和观点
    print("\n[2/5] 提取文本和观点...")
    extractor = ArticleExtractor()
    
    try:
        # 提取文本
        full_text = extractor.extract_text_from_pdf(pdf_file)
        print(f"  ✓ 提取文本: {len(full_text)} 字符")
        
        # 提取观点和证据
        claims, evidences = extractor.process_pdf_with_evidence(pdf_file)
        print(f"  ✓ 提取观点: {len(claims)} 个")
        print(f"  ✓ 提取证据: {len(evidences)} 个")
        
    except Exception as e:
        print(f"  ✗ 提取失败: {str(e)}")
        sys.exit(1)
    
    # [步骤 3] 上传文章全文到 Notion
    print("\n[3/5] 上传文章全文到 Notion...")
    notion = NotionDatabase()
    
    try:
        # 创建 Article 对象
        article = Article(
            title=pdf_file.stem,
            content="",  # 不上传文本，上传 PDF 文件
            file_path=str(pdf_file),
            file_md5=md5,
            file_size=pdf_file.stat().st_size
        )
        
        article_page = notion.add_article(article)
        article_id = article_page["id"]
        print(f"  ✓ 文章页面已创建")
        print(f"  Notion 页面 ID: {article_id[:16]}...")
        
        # 上传 PDF 文件
        print(f"\n  上传 PDF 文件...")
        file_size_mb = pdf_file.stat().st_size / 1024 / 1024
        
        if file_size_mb > 5:
            print(f"  ⚠ 文件过大 ({file_size_mb:.2f} MB)，免费版限制 5 MB")
            print(f"  💡 请手动上传或升级 Notion 账户")
        else:
            try:
                upload_result = notion.upload_pdf_to_page(article_id, pdf_file)
                print(f"  ✓ PDF 文件已上传 ({file_size_mb:.2f} MB)")
                print(f"  文件 ID: {upload_result['file_id'][:16]}...")
            except Exception as e:
                print(f"  ✗ PDF 自动上传失败: {str(e)[:80]}")
                print(f"  💡 请手动在页面中上传 PDF")
        
    except Exception as e:
        print(f"  ✗ 创建页面失败: {str(e)}")
        article_id = None
    
    # [步骤 4] 上传证据
    print("\n[4/5] 上传证据到 Notion...")
    evidence_pages = []
    
    for i, evidence in enumerate(evidences, 1):
        try:
            page = notion.add_evidence(evidence)
            evidence_pages.append(page)
            print(f"  ✓ ({i}/{len(evidences)}) {evidence.title[:40]}...")
        except Exception as e:
            print(f"  ✗ ({i}/{len(evidences)}) 失败: {str(e)[:60]}")
            evidence_pages.append(None)
    
    # [步骤 5] 上传观点并关联
    print("\n[5/5] 上传观点并建立关联...")
    
    success_count = 0
    failed_count = 0
    
    for i, (claim, evidence_page) in enumerate(zip(claims, evidence_pages), 1):
        try:
            # 关联证据
            if evidence_page:
                claim.evidence_ids = [evidence_page["id"]]
            
            # 关联文章
            if article_id:
                claim.source_url = f"https://notion.so/{article_id.replace('-', '')}"
            
            notion.add_claim(claim)
            print(f"  ✓ ({i}/{len(claims)}) {claim.title[:40]}...")
            success_count += 1
            
        except Exception as e:
            print(f"  ✗ ({i}/{len(claims)}) 失败: {str(e)[:60]}")
            failed_count += 1
    
    # [步骤 6] 标记为已处理
    print("\n标记文件为已处理...")
    tracker.mark_processed(
        file_path=pdf_file,
        notion_article_id=article_id,
        claims_count=len(claims),
        evidence_count=len(evidences)
    )
    print("  ✓ 已记录到处理历史")
    
    # 总结
    print("\n" + "="*70)
    print("✓ 处理完成")
    print("="*70)
    print(f"\n统计:")
    print(f"  文章: 1 篇（{len(full_text)} 字符）")
    print(f"  观点: {success_count} 成功, {failed_count} 失败")
    print(f"  证据: {len([p for p in evidence_pages if p])} 个")
    print(f"  MD5: {md5}")
    
    if article_id:
        print(f"\n📖 在 Notion 中查看文章:")
        print(f"  https://notion.so/{article_id.replace('-', '')}")


def show_statistics():
    """显示处理统计"""
    tracker = FileTracker()
    stats = tracker.get_statistics()
    records = tracker.get_all_records()
    
    print("\n" + "="*70)
    print("处理历史统计")
    print("="*70)
    print(f"\n总计:")
    print(f"  已处理文件: {stats['total_files']} 个")
    print(f"  提取观点: {stats['total_claims']} 个")
    print(f"  提取证据: {stats['total_evidence']} 个")
    
    if records:
        print(f"\n最近处理的文件:")
        for record in sorted(records, key=lambda x: x.get('processed_at', ''), reverse=True)[:5]:
            print(f"\n  📄 {record.get('file_name')}")
            print(f"     时间: {record.get('processed_at', 'N/A')[:19]}")
            print(f"     观点: {record.get('claims_count', 0)} 个")
            print(f"     MD5: {record.get('md5', 'N/A')[:16]}...")


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python upload_complete.py <PDF文件路径> [--force]")
        print("  python upload_complete.py --stats  # 查看统计")
        print("\n示例:")
        print('  python upload_complete.py "file.pdf"')
        print('  python upload_complete.py "file.pdf" --force  # 强制重新处理')
        sys.exit(1)
    
    if sys.argv[1] == "--stats":
        show_statistics()
    else:
        pdf_path = sys.argv[1]
        force = "--force" in sys.argv
        process_pdf_with_dedup(pdf_path, force)


if __name__ == "__main__":
    main()
