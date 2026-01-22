#!/usr/bin/env python3
"""
通过向数据库页面添加内容来初始化
尝试直接插入表格行数据
"""

from src.config import config
from notion_client import Client


def try_add_page_with_minimal_props(client: Client, database_id: str, db_name: str):
    """尝试用最小属性创建页面"""
    print(f"\n初始化 {db_name} 数据库...")
    
    # 策略：尝试不同的"默认"属性名称
    property_attempts = [
        "Name",  # 英文
        "名称",  # 中文
        "Title",  # 另一个常见的
        "标题",  # 中文标题
    ]
    
    for prop_name in property_attempts:
        try:
            print(f"  尝试使用属性名: '{prop_name}'...")
            page = client.pages.create(
                parent={"database_id": database_id},
                properties={
                    prop_name: {
                        "title": [{"text": {"content": f"初始化条目 - {db_name}"}}]
                    }
                }
            )
            print(f"  ✓ 成功！使用的属性名: '{prop_name}'")
            print(f"  页面 ID: {page['id']}")
            return prop_name, page['id']
        except Exception as e:
            error_msg = str(e)
            print(f"    失败: {error_msg[:100]}")
            continue
    
    print(f"  ✗ 所有尝试都失败")
    return None, None


def main():
    print("="*70)
    print("通过尝试多种属性名来初始化数据库")
    print("="*70)
    
    if not config.NOTION_TOKEN:
        print("\n✗ NOTION_TOKEN 未配置")
        return
    
    client = Client(auth=config.NOTION_TOKEN)
    
    results = {}
    
    # 尝试初始化每个数据库
    if config.NOTION_ONTOLOGY_DB_ID:
        prop, page_id = try_add_page_with_minimal_props(
            client, config.NOTION_ONTOLOGY_DB_ID, "Ontology"
        )
        if prop:
            results["Ontology"] = {"property": prop, "page_id": page_id}
    
    if config.NOTION_CLAIMS_DB_ID:
        prop, page_id = try_add_page_with_minimal_props(
            client, config.NOTION_CLAIMS_DB_ID, "Claims"
        )
        if prop:
            results["Claims"] = {"property": prop, "page_id": page_id}
    
    if config.NOTION_EVIDENCE_DB_ID:
        prop, page_id = try_add_page_with_minimal_props(
            client, config.NOTION_EVIDENCE_DB_ID, "Evidence"
        )
        if prop:
            results["Evidence"] = {"property": prop, "page_id": page_id}
    
    print("\n" + "="*70)
    if results:
        print("✓ 部分或全部初始化成功")
        print("="*70)
        for db_name, info in results.items():
            print(f"\n{db_name}:")
            print(f"  默认属性名: {info['property']}")
            print(f"  示例页面 ID: {info['page_id']}")
        
        print("\n现在运行检查命令:")
        print("  uv run python check_notion_schema.py")
    else:
        print("✗ 所有数据库初始化失败")
        print("="*70)
        print("\n这可能是因为:")
        print("  1. 数据库没有任何默认属性")
        print("  2. 需要先在 Notion Web 界面中打开数据库")
        print("\n建议解决方案:")
        print("  1. 在浏览器中打开: https://www.notion.so/2ef70e3608b980c88039fd4473fe7bd5")
        print("  2. 点击打开每个数据库的完整视图")
        print("  3. Notion 会自动创建默认的 Name/Title 列")
        print("  4. 重新运行此脚本")


if __name__ == "__main__":
    main()
