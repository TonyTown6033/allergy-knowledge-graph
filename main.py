#!/usr/bin/env python3
"""
过敏知识图谱 - 主程序入口
从医学文献中提取观点并存储到 Notion 数据库
"""

import argparse
import sys
from pathlib import Path

from src.config import config
from src.extractor import ArticleExtractor, batch_process_pdfs
from src.notion_client import NotionDatabase
from src.ontology import ALLERGY_ONTOLOGY, find_nodes_in_text, get_nodes_by_category, ConceptCategory


def cmd_extract(args):
    """提取命令：从文件中提取观点"""
    extractor = ArticleExtractor()
    
    if args.file.endswith('.pdf'):
        claims = extractor.process_pdf(args.file)
    else:
        # 假设是文本文件
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
        claims = extractor.extract_claims(text, source_title=Path(args.file).stem)
    
    print(f"\n从 {args.file} 中提取了 {len(claims)} 个观点:\n")
    
    for i, claim in enumerate(claims, 1):
        print(f"【观点 {i}】{claim.title}")
        print(f"  极性: {claim.polarity.value}")
        print(f"  内容: {claim.content}")
        print(f"  关联概念: {', '.join(claim.mapped_nodes)}")
        print()
    
    # 如果指定了上传到 Notion
    if args.upload:
        print("正在上传到 Notion...")
        notion = NotionDatabase()
        for claim in claims:
            notion.add_claim(claim)
        print(f"成功上传 {len(claims)} 个观点到 Notion")


def cmd_batch(args):
    """批量处理命令：处理目录下所有 PDF"""
    output_file = args.output or "extracted_claims.json"
    results = batch_process_pdfs(args.directory, output_file)
    
    total_claims = sum(len(r.get("claims", [])) for r in results if "claims" in r)
    print(f"\n总计: 处理了 {len(results)} 个文件，提取了 {total_claims} 个观点")


def cmd_sync_ontology(args):
    """同步本体命令：将本体上传到 Notion"""
    print("正在同步过敏知识本体到 Notion...")
    
    notion = NotionDatabase()
    pages = notion.sync_ontology()
    
    print(f"成功同步 {len(pages)} 个本体节点到 Notion")


def cmd_list_ontology(args):
    """列出本体命令：显示所有本体节点"""
    if args.category:
        try:
            category = ConceptCategory(args.category)
            nodes = get_nodes_by_category(category)
            print(f"\n{category.value} 类别的节点:\n")
        except ValueError:
            print(f"未知类别: {args.category}")
            print(f"可用类别: {', '.join(c.value for c in ConceptCategory)}")
            return
    else:
        nodes = list(ALLERGY_ONTOLOGY.values())
        print(f"\n所有本体节点 ({len(nodes)} 个):\n")
    
    for node in nodes:
        print(f"• {node.name_zh} ({node.name_en or '-'})")
        print(f"  ID: {node.id}")
        print(f"  类别: {node.category.value}")
        print(f"  别名: {', '.join(node.aliases[:5])}{'...' if len(node.aliases) > 5 else ''}")
        if node.description:
            print(f"  描述: {node.description}")
        print()


def cmd_search(args):
    """搜索命令：在文本中查找概念"""
    text = args.text
    nodes = find_nodes_in_text(text)
    
    if nodes:
        print(f"\n在文本中找到 {len(nodes)} 个概念:\n")
        for node in nodes:
            print(f"• {node.name_zh} ({node.category.value})")
    else:
        print("\n未在文本中找到匹配的概念")


def cmd_check_config(args):
    """检查配置命令"""
    print("\n配置检查:\n")
    
    errors = config.validate()
    
    # Notion 配置
    print("Notion 配置:")
    print(f"  TOKEN: {'✓ 已设置' if config.NOTION_TOKEN else '✗ 未设置'}")
    print(f"  CLAIMS_DB_ID: {'✓ 已设置' if config.NOTION_CLAIMS_DB_ID else '✗ 未设置'}")
    print(f"  EVIDENCE_DB_ID: {'✓ 已设置' if config.NOTION_EVIDENCE_DB_ID else '○ 未设置（可选）'}")
    print(f"  ONTOLOGY_DB_ID: {'✓ 已设置' if config.NOTION_ONTOLOGY_DB_ID else '○ 未设置（可选）'}")
    
    # OpenAI 配置
    print("\nOpenAI 配置:")
    print(f"  API_KEY: {'✓ 已设置' if config.OPENAI_API_KEY else '✗ 未设置'}")
    print(f"  MODEL: {config.OPENAI_MODEL}")
    print(f"  BASE_URL: {config.OPENAI_BASE_URL or '默认'}")
    
    if errors:
        print(f"\n⚠ 发现 {len(errors)} 个配置问题:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✓ 配置检查通过")


def main():
    parser = argparse.ArgumentParser(
        description="过敏知识图谱 - 从医学文献中提取和管理知识",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从 PDF 提取观点
  python main.py extract path/to/article.pdf
  
  # 提取并上传到 Notion
  python main.py extract path/to/article.pdf --upload
  
  # 批量处理目录
  python main.py batch path/to/pdfs/ -o results.json
  
  # 列出所有本体节点
  python main.py ontology list
  
  # 列出特定类别
  python main.py ontology list --category 过敏原
  
  # 在文本中搜索概念
  python main.py search "IgE介导的过敏性鼻炎"
  
  # 检查配置
  python main.py config
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # extract 命令
    extract_parser = subparsers.add_parser("extract", help="从文件中提取观点")
    extract_parser.add_argument("file", help="要处理的文件路径（PDF 或文本）")
    extract_parser.add_argument("--upload", "-u", action="store_true", help="上传到 Notion")
    extract_parser.set_defaults(func=cmd_extract)
    
    # batch 命令
    batch_parser = subparsers.add_parser("batch", help="批量处理目录下的 PDF")
    batch_parser.add_argument("directory", help="PDF 文件目录")
    batch_parser.add_argument("--output", "-o", help="输出 JSON 文件路径")
    batch_parser.set_defaults(func=cmd_batch)
    
    # ontology 命令组
    ontology_parser = subparsers.add_parser("ontology", help="本体管理")
    ontology_sub = ontology_parser.add_subparsers(dest="ontology_command")
    
    # ontology list
    list_parser = ontology_sub.add_parser("list", help="列出本体节点")
    list_parser.add_argument("--category", "-c", help="按类别筛选")
    list_parser.set_defaults(func=cmd_list_ontology)
    
    # ontology sync
    sync_parser = ontology_sub.add_parser("sync", help="同步本体到 Notion")
    sync_parser.set_defaults(func=cmd_sync_ontology)
    
    # search 命令
    search_parser = subparsers.add_parser("search", help="在文本中搜索概念")
    search_parser.add_argument("text", help="要搜索的文本")
    search_parser.set_defaults(func=cmd_search)
    
    # config 命令
    config_parser = subparsers.add_parser("config", help="检查配置")
    config_parser.set_defaults(func=cmd_check_config)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    # ontology 命令需要子命令
    if args.command == "ontology" and args.ontology_command is None:
        ontology_parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
