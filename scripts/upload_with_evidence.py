#!/usr/bin/env python3
"""
完整上传脚本：支持 Claims 和 Evidence 的关联
从 PDF 中提取观点和证据，建立它们之间的关联关系
"""

import sys
from pathlib import Path
from src.extractor import ArticleExtractor
from src.notion_client import NotionDatabase


def process_and_upload_pdf(pdf_path: str):
    """
    处理单个 PDF，提取观点和证据并上传到 Notion
    
    Args:
        pdf_path: PDF 文件路径
    """
    print("="*70)
    print("完整知识图谱提取与上传")
    print("="*70)
    
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"\n✗ 文件不存在: {pdf_path}")
        sys.exit(1)
    
    print(f"\n📄 处理文件: {pdf_file.name}")
    print("-"*70)
    
    # 1. 提取观点和证据
    print("\n[1/3] 提取观点和证据...")
    extractor = ArticleExtractor()
    
    try:
        claims, evidences = extractor.process_pdf_with_evidence(pdf_file)
        print(f"  ✓ 提取了 {len(claims)} 个观点")
        print(f"  ✓ 提取了 {len(evidences)} 个证据")
    except Exception as e:
        print(f"  ✗ 提取失败: {str(e)}")
        sys.exit(1)
    
    if not claims:
        print("\n⚠ 未提取到任何观点，退出")
        return
    
    # 2. 上传 Evidence 到 Notion
    print("\n[2/3] 上传证据到 Notion...")
    notion = NotionDatabase()
    evidence_pages = []
    
    for i, evidence in enumerate(evidences, 1):
        try:
            page = notion.add_evidence(evidence)
            evidence_pages.append(page)
            print(f"  ✓ ({i}/{len(evidences)}) {evidence.title[:50]}...")
        except Exception as e:
            print(f"  ✗ ({i}/{len(evidences)}) 上传失败: {str(e)}")
            evidence_pages.append(None)
    
    # 3. 关联 Evidence ID 并上传 Claims
    print("\n[3/3] 上传观点到 Notion（并关联证据）...")
    
    success_count = 0
    failed_count = 0
    
    for i, (claim, evidence_page) in enumerate(zip(claims, evidence_pages), 1):
        try:
            # 如果有对应的证据页面，添加其 ID
            if evidence_page:
                claim.evidence_ids = [evidence_page["id"]]
            
            notion.add_claim(claim)
            print(f"  ✓ ({i}/{len(claims)}) {claim.title[:50]}...")
            if evidence_page:
                print(f"       → 已关联证据 ID: {evidence_page['id'][:8]}...")
            success_count += 1
            
        except Exception as e:
            print(f"  ✗ ({i}/{len(claims)}) 上传失败: {str(e)[:80]}")
            failed_count += 1
    
    # 总结
    print("\n" + "="*70)
    print("✓ 处理完成")
    print("="*70)
    print(f"\n统计:")
    print(f"  观点: {success_count} 成功, {failed_count} 失败")
    print(f"  证据: {len([p for p in evidence_pages if p])} 个")
    print(f"  关联: {len([p for p in evidence_pages if p])} 对")
    print("\n💡 提示: 在 Notion 中查看:")
    print(f"  - Claims 数据库: 查看观点")
    print(f"  - Evidence 数据库: 查看支持证据")
    print(f"  - 每个观点都关联了对应的证据")


def main():
    if len(sys.argv) < 2:
        print("用法: python upload_with_evidence.py <PDF文件路径>")
        print("\n示例:")
        print('  python upload_with_evidence.py "download/过敏原及自身抗体相关指南共识/过敏原/中国儿童过敏原检测临床应用专家共识(2021版).pdf"')
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    process_and_upload_pdf(pdf_path)


if __name__ == "__main__":
    main()
