#!/usr/bin/env python3
"""
初始化 Notion 数据库
通过添加示例数据来激活数据库属性
"""

from src.config import config
from src.notion_client import Client


def initialize_ontology_database():
    """通过添加一个示例条目来初始化 Ontology 数据库"""
    print("\n初始化 Ontology 数据库...")
    
    client = Client(auth=config.NOTION_TOKEN)
    db_id = config.NOTION_ONTOLOGY_DB_ID
    
    try:
        # 创建一个示例页面来初始化属性
        page = client.pages.create(
            parent={"database_id": db_id},
            properties={
                "名称": {
                    "title": [{"text": {"content": "示例节点（可删除）"}}]
                }
            }
        )
        
        print(f"  ✓ 创建示例条目成功")
        print(f"  页面 ID: {page['id']}")
        print(f"  提示: 可以在 Notion 中手动删除这个示例条目")
        
        return page['id']
        
    except Exception as e:
        print(f"  ✗ 失败: {str(e)}")
        return None


def initialize_claims_database():
    """通过添加一个示例条目来初始化 Claims 数据库"""
    print("\n初始化 Claims 数据库...")
    
    client = Client(auth=config.NOTION_TOKEN)
    db_id = config.NOTION_CLAIMS_DB_ID
    
    try:
        # 创建一个示例页面
        page = client.pages.create(
            parent={"database_id": db_id},
            properties={
                "标题": {
                    "title": [{"text": {"content": "示例观点（可删除）"}}]
                }
            }
        )
        
        print(f"  ✓ 创建示例条目成功")
        print(f"  页面 ID: {page['id']}")
        
        return page['id']
        
    except Exception as e:
        print(f"  ✗ 失败: {str(e)}")
        return None


def initialize_evidence_database():
    """通过添加一个示例条目来初始化 Evidence 数据库"""
    print("\n初始化 Evidence 数据库...")
    
    client = Client(auth=config.NOTION_TOKEN)
    db_id = config.NOTION_EVIDENCE_DB_ID
    
    try:
        # 创建一个示例页面
        page = client.pages.create(
            parent={"database_id": db_id},
            properties={
                "标题": {
                    "title": [{"text": {"content": "示例证据（可删除）"}}]
                }
            }
        )
        
        print(f"  ✓ 创建示例条目成功")
        print(f"  页面 ID: {page['id']}")
        
        return page['id']
        
    except Exception as e:
        print(f"  ✗ 失败: {str(e)}")
        return None


def main():
    print("="*70)
    print("初始化 Notion 数据库")
    print("="*70)
    
    if not config.NOTION_TOKEN:
        print("\n✗ 错误: NOTION_TOKEN 未配置")
        return
    
    # 初始化数据库
    initialize_claims_database()
    initialize_ontology_database()
    initialize_evidence_database()
    
    print("\n" + "="*70)
    print("✓ 初始化完成")
    print("="*70)
    print("\n现在数据库已准备就绪，可以运行:")
    print("  uv run python main.py ontology sync")
    print("  uv run python upload_results.py results.json")
    print("\n提示: 可以在 Notion 中删除这些示例条目")


if __name__ == "__main__":
    main()
