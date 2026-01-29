import json
import os
import sys
import hashlib
import argparse
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.ontology import ALLERGY_ONTOLOGY
from src.file_tracker import FileTracker
from src.notion_client import NotionDatabase
from src.config import config

def generate_local_graph(results_path="results.json", output_path="graph_view/graph_data.json"):
    """
    Generate graph data from local results.json
    """
    if not os.path.exists(results_path):
        print(f"Error: {results_path} not found.")
        return

    with open(results_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    nodes = []
    links = []
    existing_nodes = set()

    # Add Ontology Nodes
    for node_id, node in ALLERGY_ONTOLOGY.items():
        if node_id not in existing_nodes:
            nodes.append({
                "id": node_id,
                "group": "Ontology",
                "name": node.name_zh,
                "description": node.description,
                "val": 10
            })
            existing_nodes.add(node_id)
            
            # Add parent links if any
            if node.parent_id and node.parent_id in ALLERGY_ONTOLOGY:
                 links.append({
                    "source": node_id,
                    "target": node.parent_id,
                    "type": "is_a"
                })

    tracker = FileTracker()
    # Process Articles and Claims
    for article in data:
        # Create Article Node
        # Prefer file content MD5 as ID for stable file-based preview
        file_path = article.get("file", "")
        article_id = ""
        if file_path:
            try:
                article_id = tracker.calculate_md5(file_path)
            except FileNotFoundError:
                article_id = ""
        if not article_id:
            article_id = hashlib.md5(file_path.encode()).hexdigest()
        article_title = article.get("title", "Unknown Article")
        
        if article_id not in existing_nodes:
            nodes.append({
                "id": article_id,
                "group": "Article",
                "name": article_title,
                "val": 20
            })
            existing_nodes.add(article_id)

        # Process Claims
        for claim in article.get("claims", []):
            # Create Claim Node
            claim_title = claim.get("title", "Unknown Claim")
            claim_content = claim.get("content", "")
            # Create a unique ID for the claim (combining article ID and claim title hash)
            claim_hash = hashlib.md5((article_id + claim_title).encode()).hexdigest()
            claim_id = f"claim_{claim_hash}"

            if claim_id not in existing_nodes:
                nodes.append({
                    "id": claim_id,
                    "group": "Claim",
                    "name": claim_title,
                    "content": claim_content,
                    "polarity": claim.get("polarity"),
                    "val": 5
                })
                existing_nodes.add(claim_id)

            # Link Article -> Claim
            links.append({
                "source": article_id,
                "target": claim_id,
                "type": "contains"
            })

            # Link Claim -> Ontology
            for mapped_node in claim.get("mapped_nodes", []):
                if mapped_node in ALLERGY_ONTOLOGY:
                    links.append({
                        "source": claim_id,
                        "target": mapped_node,
                        "type": "relates_to"
                    })

    save_graph(nodes, links, output_path)

def fetch_all_pages(client, database_id):
    """
    Helper to fetch all pages from a database with pagination
    
    Note: Notion API 2025-09-03 引入了 data source 概念
    一个 database 可以包含多个 data sources
    需要先从 database 获取 data_source_id，然后使用 data_sources.query
    """
    results = []
    
    # Step 1: 从 database 获取 data_source_id
    try:
        db_info = client.databases.retrieve(database_id=database_id)
        data_sources = db_info.get("data_sources", [])
        
        if not data_sources:
            raise ValueError(f"Database {database_id} has no data sources")
        
        # 通常一个数据库只有一个 data source
        # 如果有多个，我们查询第一个（也可以遍历所有）
        data_source_id = data_sources[0]["id"]
        
    except Exception as e:
        print(f"Error: Could not retrieve database info: {e}")
        raise

    # Step 2: 使用 data_source_id 查询所有页面（带分页）
    has_more = True
    start_cursor = None
    
    while has_more:
        response = client.data_sources.query(
            data_source_id=data_source_id,
            start_cursor=start_cursor
        )
        results.extend(response.get("results", []))
        has_more = response.get("has_more", False)
        start_cursor = response.get("next_cursor")
    
    return results

def get_property_value(page, property_name):
    """Helper to safely extract property value"""
    props = page.get("properties", {})
    prop = props.get(property_name, {})
    prop_type = prop.get("type")

    if not prop_type:
        return None

    if prop_type == "title":
        return "".join([t.get("text", {}).get("content", "") for t in prop.get("title", [])])
    elif prop_type == "rich_text":
        return "".join([t.get("text", {}).get("content", "") for t in prop.get("rich_text", [])])
    elif prop_type == "select":
        return prop.get("select", {}).get("name") if prop.get("select") else None
    elif prop_type == "multi_select":
        return [item.get("name") for item in prop.get("multi_select", [])]
    elif prop_type == "relation":
        return [item.get("id") for item in prop.get("relation", [])]
    
    return None

def generate_notion_graph(output_path="graph_view/graph_data.json"):
    """
    Generate graph data by fetching from Notion
    """
    print("Connecting to Notion...")
    try:
        db = NotionDatabase()
    except ValueError as e:
        print(f"Error: {e}")
        return

    nodes = []
    links = []
    existing_nodes = set()

    # 1. Fetch Ontology (or use local definition as base, but let's use local for consistency)
    print("Processing Ontology...")
    for node_id, node in ALLERGY_ONTOLOGY.items():
        if node_id not in existing_nodes:
            nodes.append({
                "id": node_id,
                "group": "Ontology",
                "name": node.name_zh,
                "description": node.description,
                "val": 10
            })
            existing_nodes.add(node_id)
            if node.parent_id and node.parent_id in ALLERGY_ONTOLOGY:
                 links.append({
                    "source": node_id,
                    "target": node.parent_id,
                    "type": "is_a"
                })

    # 2. Fetch Articles
    print("Fetching Articles...")
    articles = fetch_all_pages(db.client, config.NOTION_ARTICLES_DB_ID)
    article_title_to_id = {}  # 用于后续匹配
    
    for page in articles:
        page_id = page["id"]
        title = get_property_value(page, "Name")
        
        if page_id not in existing_nodes:
            nodes.append({
                "id": page_id,
                "group": "Article",
                "name": title,
                "val": 20
            })
            existing_nodes.add(page_id)
            # 保存标题映射（用于匹配 Claim/Evidence）
            if title:
                article_title_to_id[title] = page_id

    # 3. Fetch Claims
    print("Fetching Claims...")
    claims = fetch_all_pages(db.client, config.NOTION_CLAIMS_DB_ID)
    claim_sources = {}  # 记录 claim 的来源，用于建立 Article 链接
    
    for page in claims:
        page_id = page["id"]
        title = get_property_value(page, "Name")
        content = get_property_value(page, "内容")
        polarity = get_property_value(page, "极性")
        mapped_nodes = get_property_value(page, "关联概念") # These are names from multi-select
        source_title = get_property_value(page, "来源标题")  # 获取来源标题用于匹配
        
        if page_id not in existing_nodes:
            nodes.append({
                "id": page_id,
                "group": "Claim",
                "name": title,
                "content": content,
                "polarity": polarity,
                "val": 5
            })
            existing_nodes.add(page_id)
        
        # 记录来源标题
        if source_title:
            claim_sources[page_id] = source_title

        # Link Claim -> Ontology
        if mapped_nodes:
            for node_id in mapped_nodes:
                if node_id in ALLERGY_ONTOLOGY:
                    links.append({
                        "source": page_id,
                        "target": node_id,
                        "type": "relates_to"
                    })

    # 4. Fetch Evidence
    print("Fetching Evidence...")
    evidence_list = fetch_all_pages(db.client, config.NOTION_EVIDENCE_DB_ID)
    evidence_sources = {}  # 记录 evidence 的来源
    
    for page in evidence_list:
        page_id = page["id"]
        title = get_property_value(page, "Name")
        content = get_property_value(page, "内容")
        source_title = get_property_value(page, "来源标题")
        
        if page_id not in existing_nodes:
            nodes.append({
                "id": page_id,
                "group": "Evidence",
                "name": title,
                "content": content,
                "val": 3
            })
            existing_nodes.add(page_id)
        
        if source_title:
            evidence_sources[page_id] = source_title
    
    # 5. 建立 Article -> Claim/Evidence 的链接关系
    print("Building Article links...")
    links_created = 0
    
    # 方法1: 基于来源标题精确匹配
    for claim_id, source_title in claim_sources.items():
        if source_title in article_title_to_id:
            links.append({
                "source": article_title_to_id[source_title],
                "target": claim_id,
                "type": "contains"
            })
            links_created += 1
        # 方法2: 模糊匹配（如果精确匹配失败）
        elif source_title:
            for article_title, article_id in article_title_to_id.items():
                if source_title in article_title or article_title in source_title:
                    links.append({
                        "source": article_id,
                        "target": claim_id,
                        "type": "contains"
                    })
                    links_created += 1
                    break
    
    for evidence_id, source_title in evidence_sources.items():
        if source_title in article_title_to_id:
            links.append({
                "source": article_title_to_id[source_title],
                "target": evidence_id,
                "type": "supports"
            })
            links_created += 1
        elif source_title:
            for article_title, article_id in article_title_to_id.items():
                if source_title in article_title or article_title in source_title:
                    links.append({
                        "source": article_id,
                        "target": evidence_id,
                        "type": "supports"
                    })
                    links_created += 1
                    break
    
    print(f"  Created {links_created} article links")
    
    save_graph(nodes, links, output_path)


def save_graph(nodes, links, output_path):
    graph_data = {
        "nodes": nodes,
        "links": links
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, ensure_ascii=False, indent=2)
    
    print(f"Graph data generated at {output_path}")
    print(f"Nodes: {len(nodes)}, Links: {len(links)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate 3D Graph Data")
    parser.add_argument("--mode", choices=["local", "notion"], default="local", help="Source of data")
    args = parser.parse_args()

    if args.mode == "local":
        generate_local_graph()
    else:
        generate_notion_graph()
