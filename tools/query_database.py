#!/usr/bin/env python3
"""
查询数据库内容
"""

import json
from src.config import config
from notion_client import Client


def query_database(client: Client, database_id: str, name: str):
    """查询数据库"""
    print(f"\n{'='*70}")
    print(f"查询: {name}")
    print(f"{'='*70}")
    
    try:
        # 搜索数据库中的页面
        results = client.search(
            filter={"property": "object", "value": "page"},
            sort={"direction": "descending", "timestamp": "last_edited_time"}
        )
        
        # 过滤出属于这个数据库的页面
        db_pages = []
        for page in results.get("results", []):
            parent = page.get("parent", {})
            if parent.get("type") == "database_id":
                parent_db_id = parent.get("database_id", "").replace("-", "")
                if parent_db_id == database_id.replace("-", ""):
                    db_pages.append(page)
        
        print(f"\n找到 {len(db_pages)} 个页面\n")
        
        for i, page in enumerate(db_pages[:5], 1):  # 只显示前5个
            print(f"页面 {i}:")
            print(f"  ID: {page['id']}")
            print(f"  属性:")
            props = page.get("properties", {})
            for prop_name, prop_value in props.items():
                print(f"    {prop_name}: {prop_value.get('type', 'unknown')}")
            print()
        
        # 检查数据库结构
        db_info = client.databases.retrieve(database_id=database_id)
        print(f"\n数据库属性定义:")
        props_def = db_info.get("properties", {})
        if props_def:
            print(json.dumps(props_def, indent=2, ensure_ascii=False))
        else:
            print("  (空)")
        
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    if not config.NOTION_TOKEN:
        print("错误: NOTION_TOKEN 未配置")
        return
    
    client = Client(auth=config.NOTION_TOKEN)
    
    if config.NOTION_ONTOLOGY_DB_ID:
        query_database(client, config.NOTION_ONTOLOGY_DB_ID, "Ontology 数据库")


if __name__ == "__main__":
    main()
