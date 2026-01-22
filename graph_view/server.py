import http.server
import socketserver
import webbrowser
import os
import json
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# 添加项目根目录到 path 以便导入 src
sys.path.append(str(Path(__file__).parent.parent))

from src.config import config
from openai import OpenAI

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(DIRECTORY, "graph_data.json")

# 加载图谱数据
GRAPH_DATA = {"nodes": [], "links": []}
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        GRAPH_DATA = json.load(f)

# 初始化 OpenAI 客户端
client = None
if config.OPENAI_API_KEY:
    client = OpenAI(
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_BASE_URL
    )

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def do_GET(self):
        # API 处理: 搜索
        if self.path.startswith('/api/search'):
            self.handle_search()
            return

        # 默认重定向到问答首页
        if self.path == '/':
            self.path = '/qa_demo.html'
        
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def handle_search(self):
        """处理搜索请求"""
        try:
            query_components = parse_qs(urlparse(self.path).query)
            keyword = query_components.get('q', [''])[0].lower().strip()
            
            if not keyword:
                self.send_json({"error": "Empty query"})
                return

            print(f"🔍 收到搜索: {keyword}")

            # 1. 本地搜索
            matched_nodes = []
            for node in GRAPH_DATA.get("nodes", []):
                # 简单的文本匹配
                name = (node.get("name") or "").lower()
                content = (node.get("content") or "").lower()
                desc = (node.get("description") or "").lower()
                
                if keyword in name or keyword in content or keyword in desc:
                    matched_nodes.append(node)

            # 2. 判断是否需要 AI 介入
            response_data = {
                "source": "db",
                "nodes": matched_nodes,
                "summary": ""
            }

            # 如果本地结果太少 (或者完全没有)
            if len(matched_nodes) == 0:
                print("⚠️ 本地未找到结果，调用 AI...")
                if client:
                    try:
                        ai_response = self.call_ai_search(keyword)
                        response_data["source"] = "ai"
                        response_data["summary"] = ai_response
                        # 构造一个虚拟节点用于前端展示 AI 结果
                        response_data["nodes"] = [{
                            "id": "ai-result",
                            "group": "AI_Answer",
                            "name": "AI 智能回答",
                            "content": ai_response,
                            "val": 20
                        }]
                    except Exception as e:
                        print(f"❌ AI 调用失败: {e}")
                        response_data["summary"] = "本地知识库未找到相关内容，且 AI 服务暂时不可用。"
                else:
                    response_data["summary"] = "本地知识库未找到相关内容 (未配置 OpenAI API Key)。"
            else:
                # 本地有结果，简单生成一个统计摘要
                # (实际生产中这里也可以用 AI 来基于 matched_nodes 生成摘要)
                top_claim = next((n for n in matched_nodes if n.get("group") == "Claim"), None)
                if top_claim:
                    response_data["summary"] = f"为您找到相关观点：{top_claim.get('content') or top_claim.get('name')}"
                else:
                    response_data["summary"] = f"在知识库中找到 {len(matched_nodes)} 条相关信息。"

            self.send_json(response_data)

        except Exception as e:
            print(f"Server Error: {e}")
            self.send_json({"error": str(e)}, status=500)

    def call_ai_search(self, keyword):
        """调用 LLM 进行通用搜索"""
        prompt = f"""
        用户正在查询关于过敏的知识："{keyword}"。
        目前的本地专业知识库中没有找到相关条目。
        请你作为一名专业的过敏科医生，根据通用医学知识，简明扼要地回答这个问题。
        回答风格要求：专业、客观、通俗易懂，字数控制在 300 字以内。
        如果是严重的医疗问题，请在最后提醒用户及时就医。
        """
        
        completion = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的过敏科医学助手。"},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        # 禁止缓存
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

# 允许地址复用
socketserver.TCPServer.allow_reuse_address = True

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at http://localhost:{PORT}")
    print(f"Mode: API + Static Server")
    webbrowser.open(f"http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
