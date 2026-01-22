#!/usr/bin/env python3
"""
通过 API 强制初始化 Notion 数据库
添加初始条目来激活数据库属性
"""

import sys
from src.config import config
from notion_client import Client


def force_init_ontology_database(client: Client, database_id: str):
    """强制初始化 Ontology 数据库"""
    print("\n初始化 Ontology 数据库...")
    
    # 尝试不同的属性组合，找到能工作的
    attempts = [
        # 尝试1: 只有标题
        {
            "Name": {
                "title": [{"text": {"content": "测试节点（初始化用）"}}]
            }
        },
        # 尝试2: 使用 Title 作为类型名
        {
            "Title": {
                "title": [{"text": {"content": "测试节点（初始化用）"}}]
            }
        },
    ]
    
    for i, properties in enumerate(attempts, 1):
        try:
            print(f"  尝试方案 {i}...")
            page = client.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )
            print(f"  ✓ 成功创建初始条目")
            print(f"  页面 ID: {page['id']}")
            return page['id']
        except Exception as e:
            print(f"  方案 {i} 失败: {str(e)}")
            continue
    
    print(f"  ✗ 所有方案都失败了")
    return None


def force_init_claims_database(client: Client, database_id: str):
    """强制初始化 Claims 数据库"""
    print("\n初始化 Claims 数据库...")
    
    attempts = [
        {
            "Name": {
                "title": [{"text": {"content": "测试观点（初始化用）"}}]
            }
        },
        {
            "Title": {
                "title": [{"text": {"content": "测试观点（初始化用）"}}]
            }
        },
    ]
    
    for i, properties in enumerate(attempts, 1):
        try:
            print(f"  尝试方案 {i}...")
            page = client.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )
            print(f"  ✓ 成功创建初始条目")
            print(f"  页面 ID: {page['id']}")
            return page['id']
        except Exception as e:
            print(f"  方案 {i} 失败: {str(e)}")
            continue
    
    print(f"  ✗ 所有方案都失败了")
    return None


def force_init_evidence_database(client: Client, database_id: str):
    """强制初始化 Evidence 数据库"""
    print("\n初始化 Evidence 数据库...")
    
    attempts = [
        {
            "Name": {
                "title": [{"text": {"content": "测试证据（初始化用）"}}]
            }
        },
        {
            "Title": {
                "title": [{"text": {"content": "测试证据（初始化用）"}}]
            }
        },
    ]
    
    for i, properties in enumerate(attempts, 1):
        try:
            print(f"  尝试方案 {i}...")
            page = client.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )
            print(f"  ✓ 成功创建初始条目")
            print(f"  页面 ID: {page['id']}")
            return page['id']
        except Exception as e:
            print(f"  方案 {i} 失败: {str(e)}")
            continue
    
    print(f"  ✗ 所有方案都失败了")
    return None


def update_database_with_properties(client: Client, database_id: str, properties: dict):
    """尝试更新数据库属性"""
    try:
        print(f"\n  尝试更新数据库属性...")
        result = client.databases.update(
            database_id=database_id,
            properties=properties
        )
        print(f"  ✓ 数据库属性更新成功")
        return True
    except Exception as e:
        print(f"  ✗ 更新失败: {str(e)}")
        return False


def main():
    print("="*70)
    print("强制初始化 Notion 数据库")
    print("="*70)
    
    if not config.NOTION_TOKEN:
        print("\n✗ 错误: NOTION_TOKEN 未配置")
        sys.exit(1)
    
    client = Client(auth=config.NOTION_TOKEN)
    
    success_count = 0
    
    # 初始化 Ontology 数据库
    if config.NOTION_ONTOLOGY_DB_ID:
        # 先尝试更新属性
        ontology_props = {
            "名称": {"title": {}},
            "ID": {"rich_text": {}},
            "英文名": {"rich_text": {}},
            "类别": {"select": {
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
            }},
            "别名": {"rich_text": {}},
            "描述": {"rich_text": {}},
            "父节点": {"rich_text": {}}
        }
        
        if update_database_with_properties(client, config.NOTION_ONTOLOGY_DB_ID, ontology_props):
            success_count += 1
        else:
            # 如果更新失败，尝试创建初始条目
            if force_init_ontology_database(client, config.NOTION_ONTOLOGY_DB_ID):
                success_count += 1
    
    # 初始化 Claims 数据库
    if config.NOTION_CLAIMS_DB_ID:
        claims_props = {
            "标题": {"title": {}},
            "内容": {"rich_text": {}},
            "极性": {"select": {
                "options": [
                    {"name": "支持", "color": "green"},
                    {"name": "反驳", "color": "red"},
                    {"name": "中立", "color": "gray"}
                ]
            }},
            "关联概念": {"multi_select": {}},
            "来源标题": {"rich_text": {}},
            "来源链接": {"url": {}}
        }
        
        if update_database_with_properties(client, config.NOTION_CLAIMS_DB_ID, claims_props):
            success_count += 1
        else:
            if force_init_claims_database(client, config.NOTION_CLAIMS_DB_ID):
                success_count += 1
    
    # 初始化 Evidence 数据库
    if config.NOTION_EVIDENCE_DB_ID:
        evidence_props = {
            "标题": {"title": {}},
            "内容": {"rich_text": {}},
            "来源标题": {"rich_text": {}},
            "来源链接": {"url": {}},
            "页码": {"number": {}}
        }
        
        if update_database_with_properties(client, config.NOTION_EVIDENCE_DB_ID, evidence_props):
            success_count += 1
        else:
            if force_init_evidence_database(client, config.NOTION_EVIDENCE_DB_ID):
                success_count += 1
    
    print("\n" + "="*70)
    if success_count == 3:
        print("✓ 所有数据库初始化成功！")
        print("="*70)
        print("\n现在可以运行:")
        print("  uv run python check_notion_schema.py  # 验证数据库结构")
        print("  uv run python main.py ontology sync   # 同步本体")
        print("  uv run python upload_results.py results.json  # 上传观点")
    else:
        print(f"⚠ 部分初始化成功 ({success_count}/3)")
        print("="*70)
        print("\n可能的原因:")
        print("  1. 数据库可能是 inline database，需要先在页面中打开一次")
        print("  2. Integration 权限未正确设置")
        print("\n建议:")
        print("  1. 在 Notion 中打开你的页面并查看数据库")
        print("  2. 点击每个数据库进入完整视图")
        print("  3. 重新运行此脚本")


if __name__ == "__main__":
    main()
