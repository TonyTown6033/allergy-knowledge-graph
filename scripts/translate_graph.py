import json
import os
import sys
from pathlib import Path
from openai import OpenAI

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.config import config

def translate_graph_data(input_path="graph_view/graph_data.json", output_path="graph_view/graph_data_zh.json"):
    """
    Translate content in graph_data.json to Chinese using OpenAI
    """
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not config.OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not configured.")
        return

    client = OpenAI(
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_BASE_URL
    )

    total_nodes = len(data.get("nodes", []))
    print(f"Translating {total_nodes} nodes...")

    # Process in batches to save time and API calls
    batch_size = 10
    nodes = data.get("nodes", [])
    
    for i in range(0, len(nodes), batch_size):
        batch = nodes[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(nodes)+batch_size-1)//batch_size}...")
        
        # Filter nodes that need translation (Article, Claim, Evidence)
        # Ontology is likely already in Chinese or has mixed content
        nodes_to_translate = []
        for node in batch:
            if node.get("group") in ["Article", "Claim", "Evidence"]:
                # Simple check if it contains Chinese characters
                has_chinese = any(u'\u4e00' <= c <= u'\u9fff' for c in node.get("name", ""))
                if not has_chinese:
                    nodes_to_translate.append(node)
        
        if not nodes_to_translate:
            continue

        # Prepare prompt
        texts_to_translate = []
        for node in nodes_to_translate:
            item = {"id": node["id"], "name": node.get("name", ""), "content": node.get("content", "")}
            texts_to_translate.append(item)
            
        prompt = f"""
        Translate the following JSON array of items to Simplified Chinese.
        Maintain the original JSON structure.
        Only translate 'name' and 'content' fields.
        
        Input:
        {json.dumps(texts_to_translate, ensure_ascii=False)}
        """

        try:
            response = client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional translator for medical texts."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
            
            translated_content = response.choices[0].message.content
            # The output might be wrapped in a key like "items" or just the list, depends on model behavior with json mode
            # But usually it respects structure. Let's try to parse it.
            
            try:
                translated_json = json.loads(translated_content)
                # Handle case where LLM wraps list in a key
                if isinstance(translated_json, dict):
                    # Try to find the list
                    for key, value in translated_json.items():
                        if isinstance(value, list):
                            translated_json = value
                            break
                
                if isinstance(translated_json, list):
                    # Map back to original nodes
                    trans_map = {item["id"]: item for item in translated_json}
                    for node in nodes_to_translate:
                        if node["id"] in trans_map:
                            trans_item = trans_map[node["id"]]
                            node["name"] = trans_item.get("name", node["name"])
                            if "content" in node:
                                node["content"] = trans_item.get("content", node["content"])
                                
            except json.JSONDecodeError:
                print(f"Error parsing JSON response for batch {i}")

        except Exception as e:
            print(f"Error translating batch {i}: {e}")

    # Save translated data
    # We overwrite the original file or save as new? 
    # To be safe, let's save as original file name so the frontend picks it up automatically.
    # But let's backup first.
    if os.path.exists(input_path):
        os.rename(input_path, input_path + ".bak")
        
    with open(input_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Translation complete. Saved to {input_path}")

if __name__ == "__main__":
    translate_graph_data()
