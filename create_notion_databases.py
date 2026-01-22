#!/usr/bin/env python3
"""
在 Notion Page 下自动创建数据库
适用于 Notion 免费版用户（需要在 Page 下嵌套创建数据库）
"""

import sys
from pathlib import Path
from notion_client import Client
from src.config import config


def create_claims_database(client: Client, parent_page_id: str) -> str:
    """创建 Claims 数据库"""
    print("\n创建 Claims 数据库...")
    
    database = client.databases.create(
        parent={
            "type": "page_id",
            "page_id": parent_page_id
        },
        title=[
            {
                "type": "text",
                "text": {"content": "过敏知识图谱 - Claims (观点)"}
            }
        ],
        properties={
            "标题": {
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
    
    db_id = database["id"].replace("-", "")
    print(f"  ✓ 创建成功")
    print(f"  数据库 ID: {db_id}")
    
    return db_id


def create_ontology_database(client: Client, parent_page_id: str) -> str:
    """创建 Ontology 数据库"""
    print("\n创建 Ontology 数据库...")
    
    database = client.databases.create(
        parent={
            "type": "page_id",
            "page_id": parent_page_id
        },
        title=[
            {
                "type": "text",
                "text": {"content": "过敏知识图谱 - Ontology (本体)"}
            }
        ],
        properties={
            "名称": {
                "title": {}
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
    
    db_id = database["id"].replace("-", "")
    print(f"  ✓ 创建成功")
    print(f"  数据库 ID: {db_id}")
    
    return db_id


def create_evidence_database(client: Client, parent_page_id: str) -> str:
    """创建 Evidence 数据库"""
    print("\n创建 Evidence 数据库...")
    
    database = client.databases.create(
        parent={
            "type": "page_id",
            "page_id": parent_page_id
        },
        title=[
            {
                "type": "text",
                "text": {"content": "过敏知识图谱 - Evidence (证据)"}
            }
        ],
        properties={
            "标题": {
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
    
    db_id = database["id"].replace("-", "")
    print(f"  ✓ 创建成功")
    print(f"  数据库 ID: {db_id}")
    
    return db_id


def update_env_file(claims_id: str, ontology_id: str, evidence_id: str):
    """更新 .env 文件中的数据库 ID"""
    print("\n更新 .env 文件...")
    
    env_path = Path(__file__).parent / ".env"
    
    if not env_path.exists():
        print("  ✗ .env 文件不存在")
        return
    
    # 读取现有内容
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 更新数据库 ID
    new_lines = []
    updated = {
        "NOTION_CLAIMS_DB_ID": False,
        "NOTION_ONTOLOGY_DB_ID": False,
        "NOTION_EVIDENCE_DB_ID": False
    }
    
    for line in lines:
        if line.startswith("NOTION_CLAIMS_DB_ID="):
            new_lines.append(f"NOTION_CLAIMS_DB_ID={claims_id}\n")
            updated["NOTION_CLAIMS_DB_ID"] = True
        elif line.startswith("NOTION_ONTOLOGY_DB_ID="):
            new_lines.append(f"NOTION_ONTOLOGY_DB_ID={ontology_id}\n")
            updated["NOTION_ONTOLOGY_DB_ID"] = True
        elif line.startswith("NOTION_EVIDENCE_DB_ID="):
            new_lines.append(f"NOTION_EVIDENCE_DB_ID={evidence_id}\n")
            updated["NOTION_EVIDENCE_DB_ID"] = True
        else:
            new_lines.append(line)
    
    # 如果某些 ID 不存在，添加到末尾
    if not updated["NOTION_CLAIMS_DB_ID"]:
        new_lines.append(f"\nNOTION_CLAIMS_DB_ID={claims_id}\n")
    if not updated["NOTION_ONTOLOGY_DB_ID"]:
        new_lines.append(f"NOTION_ONTOLOGY_DB_ID={ontology_id}\n")
    if not updated["NOTION_EVIDENCE_DB_ID"]:
        new_lines.append(f"NOTION_EVIDENCE_DB_ID={evidence_id}\n")
    
    # 写回文件
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("  ✓ .env 文件已更新")


def get_page_id_from_url(url: str) -> str:
    """从 Notion URL 中提取 Page ID"""
    # URL 格式: https://www.notion.so/Page-Name-1234567890abcdef1234567890abcdef
    # 或: https://www.notion.so/workspace/1234567890abcdef1234567890abcdef
    
    # 移除 URL 参数
    if "?" in url:
        url = url.split("?")[0]
    
    # 提取最后一部分
    parts = url.rstrip("/").split("/")
    last_part = parts[-1]
    
    # 如果包含 '-'，提取最后32位字符
    if "-" in last_part:
        page_id = last_part.split("-")[-1]
    else:
        page_id = last_part
    
    # 移除所有 '-'
    page_id = page_id.replace("-", "")
    
    # 验证长度
    if len(page_id) != 32:
        raise ValueError(f"无效的 Page ID 长度: {len(page_id)} (应该是32位)")
    
    return page_id


def main():
    print("="*70)
    print("Notion 数据库自动创建工具")
    print("适用于免费版用户 - 在 Page 下创建嵌套数据库")
    print("="*70)
    
    # 检查 Token
    if not config.NOTION_TOKEN:
        print("\n✗ 错误: NOTION_TOKEN 未配置")
        print("  请在 .env 文件中设置 NOTION_TOKEN")
        sys.exit(1)
    
    # 获取父页面 ID
    if len(sys.argv) < 2:
        print("\n请提供 Notion 页面的 URL 或 ID：")
        print("\n用法:")
        print("  python create_notion_databases.py <PAGE_URL>")
        print("\n示例:")
        print("  python create_notion_databases.py https://www.notion.so/My-Page-abc123...")
        print("  python create_notion_databases.py abc123def456...")
        print("\n如何获取页面 URL:")
        print("  1. 在 Notion 中创建一个新页面（或使用现有页面）")
        print("  2. 点击右上角的 '...' 菜单")
        print("  3. 选择 'Copy link' 复制链接")
        print("  4. 将链接作为参数运行此脚本")
        sys.exit(1)
    
    page_input = sys.argv[1]
    
    try:
        # 解析页面 ID
        if page_input.startswith("http"):
            parent_page_id = get_page_id_from_url(page_input)
            print(f"\n从 URL 提取的 Page ID: {parent_page_id}")
        else:
            parent_page_id = page_input.replace("-", "")
            if len(parent_page_id) != 32:
                raise ValueError(f"无效的 Page ID 长度: {len(parent_page_id)}")
            print(f"\n使用 Page ID: {parent_page_id}")
        
        # 初始化客户端
        client = Client(auth=config.NOTION_TOKEN)
        
        # 测试连接并验证页面访问权限
        print("\n验证页面访问权限...")
        try:
            page = client.pages.retrieve(page_id=parent_page_id)
            print(f"  ✓ 页面访问成功")
        except Exception as e:
            print(f"  ✗ 无法访问页面: {str(e)}")
            print("\n请确保:")
            print("  1. 页面 ID 正确")
            print("  2. Integration 已添加到该页面")
            print("     (点击页面右上角 '...' -> 'Add connections' -> 选择你的 Integration)")
            sys.exit(1)
        
        # 创建数据库
        print("\n" + "="*70)
        print("开始创建数据库...")
        print("="*70)
        
        claims_id = create_claims_database(client, parent_page_id)
        ontology_id = create_ontology_database(client, parent_page_id)
        evidence_id = create_evidence_database(client, parent_page_id)
        
        # 更新 .env 文件
        print("\n" + "="*70)
        update_env_file(claims_id, ontology_id, evidence_id)
        
        # 显示摘要
        print("\n" + "="*70)
        print("✓ 所有数据库创建成功！")
        print("="*70)
        print("\n数据库 ID:")
        print(f"  Claims:   {claims_id}")
        print(f"  Ontology: {ontology_id}")
        print(f"  Evidence: {evidence_id}")
        
        print("\n下一步操作:")
        print("  1. 检查配置: uv run python main.py config")
        print("  2. 同步本体: uv run python main.py ontology sync")
        print("  3. 上传观点: uv run python upload_results.py results.json")
        
        print("\n💡 提示: 数据库已在你的 Notion 页面中创建，刷新页面即可看到")
        
    except Exception as e:
        print(f"\n✗ 创建失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
