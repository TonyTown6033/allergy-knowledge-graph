#!/usr/bin/env python3
"""
为 Notion 数据库添加列（属性）
通过更新数据库 schema 来添加所需的列
"""

from src.config import config
from notion_client import Client
import json


def add_ontology_columns(client: Client, database_id: str):
    """为 Ontology 数据库添加列"""
    print("\n为 Ontology 数据库添加列...")
    
    try:
        # 更新数据库，添加所需的列
        result = client.databases.update(
            database_id=database_id,
            properties={
                "Name": {
                    "title": {}  # 保留现有的 Name 列
                },
                "ID": {
                    "rich_text": {}
                },
                "英文名": {
                    "rich_text": {}
                },
                "类别": {
                    "select": {
                        "options": [
                            {"name": "免疫球蛋白", "color": "blue"},
                            {"name": "过敏原", "color": "red"},
                            {"name": "过敏性疾病", "color": "orange"},
                            {"name": "症状", "color": "yellow"},
                            {"name": "治疗方法", "color": "green"},
                            {"name": "诊断方法", "color": "purple"},
                            {"name": "细胞", "color": "pink"},
                            {"name": "介质", "color": "gray"}
                        ]
                    }
                },
                "别名": {
                    "rich_text": {}
                },
                "描述": {
                    "rich_text": {}
                },
                "父节点": {
                    "rich_text": {}
                }
            }
        )
        
        print("  ✓ 成功添加列")
        print("  列: Name, ID, 英文名, 类别, 别名, 描述, 父节点")
        return True
        
    except Exception as e:
        print(f"  ✗ 失败: {str(e)}")
        return False


def add_claims_columns(client: Client, database_id: str):
    """为 Claims 数据库添加列"""
    print("\n为 Claims 数据库添加列...")
    
    try:
        result = client.databases.update(
            database_id=database_id,
            properties={
                "Name": {
                    "title": {}
                },
                "内容": {
                    "rich_text": {}
                },
                "极性": {
                    "select": {
                        "options": [
                            {"name": "支持", "color": "green"},
                            {"name": "反驳", "color": "red"},
                            {"name": "中立", "color": "gray"}
                        ]
                    }
                },
                "关联概念": {
                    "multi_select": {}
                },
                "来源标题": {
                    "rich_text": {}
                },
                "来源链接": {
                    "url": {}
                }
            }
        )
        
        print("  ✓ 成功添加列")
        print("  列: Name, 内容, 极性, 关联概念, 来源标题, 来源链接")
        return True
        
    except Exception as e:
        print(f"  ✗ 失败: {str(e)}")
        return False


def add_evidence_columns(client: Client, database_id: str):
    """为 Evidence 数据库添加列"""
    print("\n为 Evidence 数据库添加列...")
    
    try:
        result = client.databases.update(
            database_id=database_id,
            properties={
                "Name": {
                    "title": {}
                },
                "内容": {
                    "rich_text": {}
                },
                "来源标题": {
                    "rich_text": {}
                },
                "来源链接": {
                    "url": {}
                },
                "页码": {
                    "number": {}
                }
            }
        )
        
        print("  ✓ 成功添加列")
        print("  列: Name, 内容, 来源标题, 来源链接, 页码")
        return True
        
    except Exception as e:
        print(f"  ✗ 失败: {str(e)}")
        return False


def main():
    print("="*70)
    print("为 Notion 数据库添加列")
    print("="*70)
    
    if not config.NOTION_TOKEN:
        print("\n✗ NOTION_TOKEN 未配置")
        return
    
    client = Client(auth=config.NOTION_TOKEN)
    
    success_count = 0
    
    # 添加 Ontology 列
    if config.NOTION_ONTOLOGY_DB_ID:
        if add_ontology_columns(client, config.NOTION_ONTOLOGY_DB_ID):
            success_count += 1
    
    # 添加 Claims 列
    if config.NOTION_CLAIMS_DB_ID:
        if add_claims_columns(client, config.NOTION_CLAIMS_DB_ID):
            success_count += 1
    
    # 添加 Evidence 列
    if config.NOTION_EVIDENCE_DB_ID:
        if add_evidence_columns(client, config.NOTION_EVIDENCE_DB_ID):
            success_count += 1
    
    print("\n" + "="*70)
    if success_count == 3:
        print("✓ 所有数据库列添加成功！")
        print("="*70)
        print("\n现在需要:")
        print("  1. 检查列: uv run python check_notion_schema.py")
        print("  2. 清空数据库中的旧数据（在 Notion 中手动删除）")
        print("  3. 重新同步: uv run python main.py ontology sync")
    else:
        print(f"⚠ 部分成功 ({success_count}/3)")
        print("="*70)


if __name__ == "__main__":
    main()
