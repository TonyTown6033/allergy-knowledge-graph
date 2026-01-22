#!/usr/bin/env python3
"""
设置 Notion 数据库的属性结构
为 Claims、Ontology 和 Evidence 数据库创建必要的属性
"""

from src.config import config
from notion_client import Client


def setup_claims_database(client: Client, database_id: str):
    """设置 Claims 数据库结构"""
    print("\n设置 Claims 数据库...")
    
    properties = {
        "标题": {"title": {}},
        "内容": {"rich_text": {}},
        "极性": {
            "select": {
                "options": [
                    {"name": "支持", "color": "green"},
                    {"name": "反驳", "color": "red"},
                    {"name": "中立", "color": "gray"}
                ]
            }
        },
        "关联概念": {"multi_select": {}},
        "来源标题": {"rich_text": {}},
        "来源链接": {"url": {}},
    }
    
    try:
        client.databases.update(
            database_id=database_id,
            properties=properties
        )
        print("  ✓ Claims 数据库设置成功")
        print("  - 标题 (Title)")
        print("  - 内容 (Rich Text)")
        print("  - 极性 (Select: 支持/反驳/中立)")
        print("  - 关联概念 (Multi-select)")
        print("  - 来源标题 (Rich Text)")
        print("  - 来源链接 (URL)")
    except Exception as e:
        print(f"  ✗ 设置失败: {str(e)}")


def setup_ontology_database(client: Client, database_id: str):
    """设置 Ontology 数据库结构"""
    print("\n设置 Ontology 数据库...")
    
    properties = {
        "名称": {"title": {}},
        "ID": {"rich_text": {}},
        "英文名": {"rich_text": {}},
        "类别": {
            "select": {
                "options": [
                    {"name": "过敏原", "color": "red"},
                    {"name": "疾病", "color": "orange"},
                    {"name": "症状", "color": "yellow"},
                    {"name": "检查", "color": "blue"},
                    {"name": "治疗", "color": "green"},
                    {"name": "生物标志物", "color": "purple"},
                    {"name": "其他", "color": "gray"}
                ]
            }
        },
        "别名": {"rich_text": {}},
        "描述": {"rich_text": {}},
        "父节点": {"rich_text": {}},
    }
    
    try:
        client.databases.update(
            database_id=database_id,
            properties=properties
        )
        print("  ✓ Ontology 数据库设置成功")
        print("  - 名称 (Title)")
        print("  - ID (Rich Text)")
        print("  - 英文名 (Rich Text)")
        print("  - 类别 (Select)")
        print("  - 别名 (Rich Text)")
        print("  - 描述 (Rich Text)")
        print("  - 父节点 (Rich Text)")
    except Exception as e:
        print(f"  ✗ 设置失败: {str(e)}")


def setup_evidence_database(client: Client, database_id: str):
    """设置 Evidence 数据库结构"""
    print("\n设置 Evidence 数据库...")
    
    properties = {
        "标题": {"title": {}},
        "内容": {"rich_text": {}},
        "来源标题": {"rich_text": {}},
        "来源链接": {"url": {}},
        "页码": {"number": {}},
    }
    
    try:
        client.databases.update(
            database_id=database_id,
            properties=properties
        )
        print("  ✓ Evidence 数据库设置成功")
        print("  - 标题 (Title)")
        print("  - 内容 (Rich Text)")
        print("  - 来源标题 (Rich Text)")
        print("  - 来源链接 (URL)")
        print("  - 页码 (Number)")
    except Exception as e:
        print(f"  ✗ 设置失败: {str(e)}")


def main():
    print("="*60)
    print("开始设置 Notion 数据库结构")
    print("="*60)
    
    if not config.NOTION_TOKEN:
        print("\n✗ 错误: NOTION_TOKEN 未配置")
        return
    
    client = Client(auth=config.NOTION_TOKEN)
    
    # 设置 Claims 数据库
    if config.NOTION_CLAIMS_DB_ID:
        setup_claims_database(client, config.NOTION_CLAIMS_DB_ID)
    else:
        print("\n⚠ NOTION_CLAIMS_DB_ID 未配置，跳过")
    
    # 设置 Ontology 数据库
    if config.NOTION_ONTOLOGY_DB_ID:
        setup_ontology_database(client, config.NOTION_ONTOLOGY_DB_ID)
    else:
        print("\n⚠ NOTION_ONTOLOGY_DB_ID 未配置，跳过")
    
    # 设置 Evidence 数据库
    if config.NOTION_EVIDENCE_DB_ID:
        setup_evidence_database(client, config.NOTION_EVIDENCE_DB_ID)
    else:
        print("\n⚠ NOTION_EVIDENCE_DB_ID 未配置（可选）")
    
    print("\n" + "="*60)
    print("数据库设置完成！")
    print("="*60)
    print("\n现在可以运行以下命令：")
    print("  1. 同步本体: uv run python main.py ontology sync")
    print("  2. 上传观点: uv run python upload_results.py results.json")


if __name__ == "__main__":
    main()
