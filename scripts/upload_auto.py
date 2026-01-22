#!/usr/bin/env python3
"""
自动上传脚本：提供模式选择
--pdf: 只创建页面，手动上传 PDF（保留格式）
--text: 上传文本内容（全自动，丢失格式）
"""

import sys
from pathlib import Path
from src.extractor import ArticleExtractor
from src.notion_client import NotionDatabase, Article
from src.file_tracker import FileTracker


def upload_with_mode(pdf_path: str, mode: str = "pdf", force: bool = False):
    """
    根据模式上传
    
    Args:
        pdf_path: PDF 文件路径
        mode: "pdf"（保留格式）或 "text"（纯文本）
        force: 强制处理
    """
    print("="*70)
    mode_name = "PDF 格式（需手动上传）" if mode == "pdf" else "纯文本（全自动）"
    print(f"知识图谱上传 - 模式: {mode_name}")
    print("="*70)
    
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"\n✗ 文件不存在: {pdf_path}")
        sys.exit(1)
    
    print(f"\n📄 文件: {pdf_file.name}")
    print(f"   大小: {pdf_file.stat().st_size / 1024 / 1024:.2f} MB")
    print("-"*70)
    
    # 去重检查
    tracker = FileTracker()
    md5 = tracker.calculate_md5(pdf_file)
    
    print(f"\n[1/4] 去重检查 (MD5: {md5[:16]}...)")
    
    if not force and tracker.is_processed(pdf_file):
        record = tracker.get_record(pdf_file)
        print(f"  ⚠ 文件已处理")
        print(f"  时间: {record.get('processed_at', 'N/A')[:19]}")
        print(f"  观点: {record.get('claims_count', 0)} 个")
        print("\n跳过处理（使用 --force 强制重新处理）")
        return
    else:
        print("  ✓ 未处理，继续")
    
    # 提取
    print(f"\n[2/4] AI 提取...")
    extractor = ArticleExtractor()
    
    try:
        full_text = extractor.extract_text_from_pdf(pdf_file)
        claims, evidences = extractor.extract_claims_with_evidence(
            text=full_text,
            source_title=pdf_file.stem
        )
        print(f"  ✓ 观点: {len(claims)} 个")
        print(f"  ✓ 证据: {len(evidences)} 个")
    except Exception as e:
        print(f"  ✗ 失败: {str(e)}")
        sys.exit(1)
    
    # 创建文章页面
    print(f"\n[3/4] 创建 Articles 页面...")
    notion = NotionDatabase()
    
    try:
        article = Article(
            title=pdf_file.stem,
            content=full_text[:50000] if mode == "text" else "",
            file_path=str(pdf_file),
            file_md5=md5,
            file_size=pdf_file.stat().st_size
        )
        
        article_page = notion.add_article(article)
        article_id = article_page["id"]
        notion_url = f"https://notion.so/{article_id.replace('-', '')}"
        
        print(f"  ✓ 页面已创建")
        
        if mode == "pdf":
            print(f"\n  📎 请手动上传 PDF:")
            print(f"     {notion_url}")
            print(f"     (在页面中拖拽 PDF 文件)")
        else:
            print(f"  ✓ 文本内容已上传 ({len(full_text)} 字符)")
        
    except Exception as e:
        print(f"  ✗ 失败: {str(e)}")
        article_id = None
        notion_url = None
    
    # 上传证据和观点
    print(f"\n[4/4] 上传观点和证据...")
    
    # 证据
    evidence_pages = []
    for evidence in evidences:
        try:
            page = notion.add_evidence(evidence)
            evidence_pages.append(page)
        except:
            evidence_pages.append(None)
    
    # 观点
    success = 0
    for claim, evidence_page in zip(claims, evidence_pages):
        try:
            if evidence_page:
                claim.evidence_ids = [evidence_page["id"]]
            if notion_url:
                claim.source_url = notion_url
            
            notion.add_claim(claim)
            success += 1
        except:
            pass
    
    print(f"  ✓ 观点: {success}/{len(claims)}")
    print(f"  ✓ 证据: {len([p for p in evidence_pages if p])}/{len(evidences)}")
    
    # 标记完成
    tracker.mark_processed(
        file_path=pdf_file,
        notion_article_id=article_id,
        claims_count=len(claims),
        evidence_count=len(evidences)
    )
    
    print("\n" + "="*70)
    print("✓ 完成")
    print("="*70)
    
    if mode == "pdf" and notion_url:
        print(f"\n📖 下一步：在 Notion 中上传 PDF")
        print(f"   {notion_url}")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print("用法:")
        print("  python upload_auto.py <PDF文件> [选项]")
        print("\n选项:")
        print("  --pdf     保留 PDF 格式（需手动上传）[默认]")
        print("  --text    上传纯文本（全自动，丢失格式）")
        print("  --force   强制重新处理")
        print("\n示例:")
        print('  python upload_auto.py "file.pdf"           # PDF 模式')
        print('  python upload_auto.py "file.pdf" --text    # 文本模式')
        print('  python upload_auto.py "file.pdf" --force   # 强制处理')
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    mode = "text" if "--text" in sys.argv else "pdf"
    force = "--force" in sys.argv
    
    upload_with_mode(pdf_path, mode, force)


if __name__ == "__main__":
    main()
