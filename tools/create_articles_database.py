#!/usr/bin/env python3
"""
在 Notion 中创建 Articles 数据库
用于存储文章全文和文件信息
"""

import sys
from src.config import config
from notion_client import Client


def create_articles_database(parent_page_id: str):
    """
    创建 Articles 数据库
    
    Args:
        parent_page_id: 父页面 ID
    """
    print("="*70)
    print("创建 Articles (文章) 数据库")
    print("="*70)
    
    if not config.NOTION_TOKEN:
        print("\n✗ NOTION_TOKEN 未配置")
        sys.exit(1)
    
    client = Client(auth=config.NOTION_TOKEN)
    
    print(f"\n父页面 ID: {parent_page_id}")
    print("\n创建数据库...")
    
    try:
        database = client.databases.create(
            parent={
                "type": "page_id",
                "page_id": parent_page_id
            },
            title=[
                {
                    "type": "text",
                    "text": {"content": "过敏知识图谱 - Articles (文章)"}
                }
            ],
            properties={
                "Name": {
                    "title": {}
                },
                "MD5": {
                    "rich_text": {}
                },
                "文件路径": {
                    "rich_text": {}
                },
                "文件大小": {
                    "number": {
                        "format": "number"
                    }
                },
                "来源链接": {
                    "url": {}
                }
            }
        )
        
        db_id = database["id"].replace("-", "")
        
        print(f"  ✓ 创建成功")
        print(f"  数据库 ID: {db_id}")
        
        # 提示更新 .env
        print("\n" + "="*70)
        print("下一步：更新 .env 文件")
        print("="*70)
        print(f"\n请在 .env 文件中添加：")
        print(f"NOTION_ARTICLES_DB_ID={db_id}")
        
        print("\n然后可以使用：")
        print("  uv run python upload_complete.py your_file.pdf")
        
    except Exception as e:
        print(f"  ✗ 创建失败: {str(e)}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("用法: python create_articles_database.py <NOTION_PAGE_ID>")
        print("\n示例:")
        print("  python create_articles_database.py 2ef70e3608b980c88039fd4473fe7bd5")
        print("\n注意: 使用与之前相同的父页面 ID")
        sys.exit(1)
    
    page_id = sys.argv[1].replace("-", "")
    create_articles_database(page_id)


if __name__ == "__main__":
    main()
