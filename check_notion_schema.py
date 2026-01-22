#!/usr/bin/env python3
"""
检查 Notion 数据库的属性结构
帮助诊断属性名称不匹配的问题
"""

from src.config import config
from notion_client import Client


def check_database_schema(database_id: str, db_name: str):
    """检查并显示数据库的属性结构"""
    client = Client(auth=config.NOTION_TOKEN)
    
    try:
        db_info = client.databases.retrieve(database_id=database_id)
        
        print(f"\n{'='*60}")
        print(f"数据库: {db_name}")
        print(f"ID: {database_id}")
        print(f"{'='*60}")
        
        # 调试：打印完整的数据库信息
        import json
        print(f"\n调试信息:")
        print(json.dumps(db_info.get("properties", {}), indent=2, ensure_ascii=False))
        
        properties = db_info.get("properties", {})
        
        if not properties:
            print("  ⚠ 数据库没有属性！")
            print("\n  需要在 Notion 中手动创建属性。")
            print("  请查看 NOTION_SETUP.md 文件了解详细步骤。")
            return
        
        print(f"\n属性列表 (共 {len(properties)} 个):\n")
        
        for prop_name, prop_info in properties.items():
            prop_type = prop_info.get("type", "未知")
            print(f"  • {prop_name}")
            print(f"    类型: {prop_type}")
            
            # 显示额外信息（如 select 的选项）
            if prop_type == "select" and "select" in prop_info:
                options = prop_info["select"].get("options", [])
                if options:
                    option_names = [opt.get("name", "") for opt in options]
                    print(f"    选项: {', '.join(option_names)}")
            
            elif prop_type == "multi_select" and "multi_select" in prop_info:
                options = prop_info["multi_select"].get("options", [])
                if options:
                    option_names = [opt.get("name", "") for opt in options]
                    print(f"    选项: {', '.join(option_names[:5])}{'...' if len(option_names) > 5 else ''}")
            
            print()
        
    except Exception as e:
        print(f"\n✗ 检查数据库失败: {str(e)}")


def main():
    print("\n正在检查 Notion 数据库结构...")
    
    # 检查 Claims 数据库
    if config.NOTION_CLAIMS_DB_ID:
        check_database_schema(config.NOTION_CLAIMS_DB_ID, "Claims 数据库")
    else:
        print("\n⚠ NOTION_CLAIMS_DB_ID 未配置")
    
    # 检查 Ontology 数据库
    if config.NOTION_ONTOLOGY_DB_ID:
        check_database_schema(config.NOTION_ONTOLOGY_DB_ID, "Ontology 数据库")
    else:
        print("\n⚠ NOTION_ONTOLOGY_DB_ID 未配置")
    
    # 检查 Evidence 数据库
    if config.NOTION_EVIDENCE_DB_ID:
        check_database_schema(config.NOTION_EVIDENCE_DB_ID, "Evidence 数据库")
    else:
        print("\n⚠ NOTION_EVIDENCE_DB_ID 未配置（可选）")


if __name__ == "__main__":
    main()
