#!/usr/bin/env python3
"""
更新现有页面，将 Name 中的混合数据分离到独立的列
"""

from src.config import config
from src.ontology import ALLERGY_ONTOLOGY
from notion_client import Client


def get_all_pages_in_database(client: Client, database_id: str):
    """获取数据库中的所有页面"""
    results = client.search(
        filter={"property": "object", "value": "page"}
    )
    
    pages = []
    for page in results.get("results", []):
        parent = page.get("parent", {})
        if parent.get("type") in ["database_id", "data_source_id"]:
            parent_id = parent.get("database_id") or parent.get("data_source_id", "")
            if parent_id and parent_id.replace("-", "") == database_id.replace("-", ""):
                pages.append(page)
    
    return pages


def update_ontology_pages(client: Client, database_id: str):
    """更新 Ontology 数据库的页面"""
    print("\n更新 Ontology 数据库的页面...")
    
    # 获取所有现有页面
    pages = get_all_pages_in_database(client, database_id)
    print(f"  找到 {len(pages)} 个现有页面")
    
    if len(pages) == 0:
        print("  没有页面需要更新")
        return
    
    # 删除所有旧页面
    print("  删除旧页面...")
    for page in pages:
        try:
            client.pages.update(
                page_id=page["id"],
                archived=True
            )
        except Exception as e:
            print(f"    删除失败: {e}")
    
    print(f"  ✓ 已删除 {len(pages)} 个旧页面")
    
    # 重新创建页面，使用正确的列结构
    print("\n  重新创建页面...")
    success = 0
    failed = 0
    
    for node_id, node in ALLERGY_ONTOLOGY.items():
        try:
            properties = {
                "Name": {
                    "title": [{"text": {"content": node.name_zh}}]
                },
                "ID": {
                    "rich_text": [{"text": {"content": node.id}}]
                },
                "英文名": {
                    "rich_text": [{"text": {"content": node.name_en or ""}}]
                },
                "类别": {
                    "select": {"name": node.category.value}
                },
                "别名": {
                    "rich_text": [{"text": {"content": ", ".join(node.aliases)}}]
                },
            }
            
            if node.description:
                properties["描述"] = {
                    "rich_text": [{"text": {"content": node.description}}]
                }
            
            if node.parent_id:
                properties["父节点"] = {
                    "rich_text": [{"text": {"content": node.parent_id}}]
                }
            
            client.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )
            success += 1
            print(f"    ✓ {node.name_zh}")
            
        except Exception as e:
            failed += 1
            print(f"    ✗ {node.name_zh}: {str(e)[:80]}")
    
    print(f"\n  完成: 成功 {success}, 失败 {failed}")


def main():
    print("="*70)
    print("更新 Notion 数据库页面")
    print("将混合数据分离到独立的列")
    print("="*70)
    
    if not config.NOTION_TOKEN:
        print("\n✗ NOTION_TOKEN 未配置")
        return
    
    client = Client(auth=config.NOTION_TOKEN)
    
    # 更新 Ontology
    if config.NOTION_ONTOLOGY_DB_ID:
        update_ontology_pages(client, config.NOTION_ONTOLOGY_DB_ID)
    
    print("\n" + "="*70)
    print("✓ 更新完成")
    print("="*70)
    print("\n请在 Notion 中查看更新后的数据库")


if __name__ == "__main__":
    main()
