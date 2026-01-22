#!/usr/bin/env python3
"""
调试 Notion 数据库信息
查看完整的数据库结构
"""

import json
from src.config import config
from notion_client import Client


def debug_database(client: Client, database_id: str, name: str):
    """调试数据库信息"""
    print(f"\n{'='*70}")
    print(f"数据库: {name}")
    print(f"ID: {database_id}")
    print(f"{'='*70}")
    
    try:
        db = client.databases.retrieve(database_id=database_id)
        
        print("\n完整数据库信息:")
        print(json.dumps(db, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"错误: {str(e)}")


def main():
    if not config.NOTION_TOKEN:
        print("错误: NOTION_TOKEN 未配置")
        return
    
    client = Client(auth=config.NOTION_TOKEN)
    
    if config.NOTION_ONTOLOGY_DB_ID:
        debug_database(client, config.NOTION_ONTOLOGY_DB_ID, "Ontology")


if __name__ == "__main__":
    main()
