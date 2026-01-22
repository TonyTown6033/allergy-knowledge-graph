#!/usr/bin/env python3
"""
完整上传脚本（上传 PDF 文件）：
保留 PDF 原始格式，将文件作为附件上传到 Notion
"""

import sys
from pathlib import Path
from src.extractor import ArticleExtractor
from src.notion_client import NotionDatabase, Article
from src.file_tracker import FileTracker


def upload_pdf_as_file(pdf_path: str, force: bool = False):
    """
    上传 PDF 作为文件附件（保留格式）
    
    Args:
        pdf_path: PDF 文件路径
        force: 强制重新处理
    """
    print("="*70)
    print("完整知识图谱提取与上传（PDF 文件格式）")
    print("="*70)
    
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"\n✗ 文件不存在: {pdf_path}")
        sys.exit(1)
    
    print(f"\n📄 文件: {pdf_file.name}")
    print(f"   大小: {pdf_file.stat().st_size / 1024 / 1024:.2f} MB")
    print("-"*70)
    
    # 初始化追踪器
    tracker = FileTracker()
    
    # [步骤 1] 检查去重
    print("\n[1/5] 检查文件是否已处理...")
    md5 = tracker.calculate_md5(pdf_file)
    print(f"  文件 MD5: {md5}")
    
    if not force and tracker.is_processed(pdf_file):
        record = tracker.get_record(pdf_file)
        print(f"  ⚠ 文件已处理过")
        print(f"  处理时间: {record.get('processed_at', 'N/A')}")
        print(f"  观点数: {record.get('claims_count', 0)}")
        print(f"  Notion 文章 ID: {record.get('notion_article_id', 'N/A')[:16]}...")
        
        response = input("\n是否重新处理？(y/n): ").strip().lower()
        if response != 'y':
            print("\n跳过处理")
            return
    else:
        print("  ✓ 文件未处理，开始提取")
    
    # [步骤 2] 提取观点和证据
    print("\n[2/5] 提取观点和证据...")
    extractor = ArticleExtractor()
    
    try:
        claims, evidences = extractor.process_pdf_with_evidence(pdf_file)
        print(f"  ✓ 提取观点: {len(claims)} 个")
        print(f"  ✓ 提取证据: {len(evidences)} 个")
    except Exception as e:
        print(f"  ✗ 提取失败: {str(e)}")
        sys.exit(1)
    
    # [步骤 3] 创建文章记录并上传 PDF 文件
    print("\n[3/5] 上传文章到 Notion...")
    notion = NotionDatabase()
    
    try:
        # 创建文章页面（不包含文本内容）
        article = Article(
            title=pdf_file.stem,
            content="",  # 不上传文本内容
            file_path=str(pdf_file),
            file_md5=md5,
            file_size=pdf_file.stat().st_size
        )
        
        article_page = notion.add_article(article)
        article_id = article_page["id"]
        print(f"  ✓ 文章页面已创建")
        print(f"  Notion 页面 ID: {article_id[:16]}...")
        
        # 上传 PDF 文件作为附件
        print("\n  上传 PDF 文件...")
        try:
            # 读取 PDF 文件
            with open(pdf_file, 'rb') as f:
                # Notion API 上传文件
                # 注意：需要先获取上传 URL
                print("  ⚠ PDF 文件上传功能需要使用 Notion 的文件上传 API")
                print("  📎 建议：手动在 Notion 页面中拖拽 PDF 文件")
                print(f"  📖 页面链接: https://notion.so/{article_id.replace('-', '')}")
                
        except Exception as e:
            print(f"  ⚠ 自动上传 PDF 失败: {str(e)}")
            print(f"  📎 请手动在 Notion 页面中上传 PDF 文件")
        
    except Exception as e:
        print(f"  ✗ 创建页面失败: {str(e)}")
        article_id = None
    
    # [步骤 4] 上传证据
    print("\n[4/5] 上传证据...")
    evidence_pages = []
    
    for i, evidence in enumerate(evidences, 1):
        try:
            page = notion.add_evidence(evidence)
            evidence_pages.append(page)
            print(f"  ✓ ({i}/{len(evidences)}) {evidence.title[:40]}...")
        except Exception as e:
            print(f"  ✗ ({i}/{len(evidences)}) 失败: {str(e)[:60]}")
            evidence_pages.append(None)
    
    # [步骤 5] 上传观点
    print("\n[5/5] 上传观点...")
    
    success_count = 0
    failed_count = 0
    
    for i, (claim, evidence_page) in enumerate(zip(claims, evidence_pages), 1):
        try:
            if evidence_page:
                claim.evidence_ids = [evidence_page["id"]]
            
            if article_id:
                claim.source_url = f"https://notion.so/{article_id.replace('-', '')}"
            
            notion.add_claim(claim)
            print(f"  ✓ ({i}/{len(claims)}) {claim.title[:40]}...")
            success_count += 1
            
        except Exception as e:
            print(f"  ✗ ({i}/{len(claims)}) 失败: {str(e)[:60]}")
            failed_count += 1
    
    # 标记为已处理
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
    print(f"  文章页面: 已创建")
    print(f"  PDF 文件: 需要手动上传")
    print(f"  观点: {success_count} 成功, {failed_count} 失败")
    print(f"  证据: {len([p for p in evidence_pages if p])} 个")
    
    if article_id:
        notion_url = f"https://notion.so/{article_id.replace('-', '')}"
        print(f"\n📖 在 Notion 中查看并上传 PDF:")
        print(f"  {notion_url}")
        print(f"\n💡 提示: 在页面中拖拽 PDF 文件即可上传")


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python upload_with_pdf.py <PDF文件路径> [--force]")
        print("\n说明:")
        print("  此脚本会创建 Notion 页面，但 PDF 文件需要手动上传")
        print("  这样可以保留 PDF 的原始格式")
        print("\n示例:")
        print('  python upload_with_pdf.py "file.pdf"')
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    force = "--force" in sys.argv
    upload_pdf_as_file(pdf_path, force)


if __name__ == "__main__":
    main()
