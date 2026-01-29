import http.server
import socketserver
import webbrowser
import os
import json
import sys
import re
import hashlib
from pathlib import Path
from urllib.parse import urlparse, parse_qs, quote

# 添加项目根目录到 path 以便导入 src
sys.path.append(str(Path(__file__).parent.parent))

from src.config import config
from openai import OpenAI

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(DIRECTORY, "graph_data.json")
PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_FILE = PROJECT_ROOT / "results.json"
TRACKER_FILE = PROJECT_ROOT / ".processed_files.json"

# 加载图谱数据（支持热加载）
GRAPH_DATA = {"nodes": [], "links": []}
GRAPH_DATA_MTIME = None
NODES_BY_ID = {}
ARTICLE_IDS = set()
LINKS_BY_SOURCE = {}
LINKS_BY_TARGET = {}

def _normalize_link_id(value):
    if isinstance(value, dict):
        return value.get("id")
    return value

def _rebuild_graph_indexes():
    global NODES_BY_ID, ARTICLE_IDS, LINKS_BY_SOURCE, LINKS_BY_TARGET
    NODES_BY_ID = {node.get("id"): node for node in GRAPH_DATA.get("nodes", []) if node.get("id")}
    ARTICLE_IDS = {node_id for node_id, node in NODES_BY_ID.items() if node.get("group") == "Article"}
    LINKS_BY_SOURCE = {}
    LINKS_BY_TARGET = {}
    for link in GRAPH_DATA.get("links", []):
        source_id = _normalize_link_id(link.get("source"))
        target_id = _normalize_link_id(link.get("target"))
        if not source_id or not target_id:
            continue
        LINKS_BY_SOURCE.setdefault(source_id, []).append(target_id)
        LINKS_BY_TARGET.setdefault(target_id, []).append(source_id)

def _load_graph_data():
    global GRAPH_DATA, GRAPH_DATA_MTIME
    if not os.path.exists(DATA_FILE):
        GRAPH_DATA = {"nodes": [], "links": []}
        GRAPH_DATA_MTIME = None
        _rebuild_graph_indexes()
        return
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        GRAPH_DATA = json.load(f)
    GRAPH_DATA_MTIME = os.path.getmtime(DATA_FILE)
    _rebuild_graph_indexes()

def _reload_graph_if_changed():
    if not os.path.exists(DATA_FILE):
        return
    mtime = os.path.getmtime(DATA_FILE)
    if GRAPH_DATA_MTIME is None or mtime != GRAPH_DATA_MTIME:
        _load_graph_data()

_load_graph_data()

def _build_article_file_index():
    index = {}

    # Prefer tracker data (content md5) if available
    if TRACKER_FILE.exists():
        try:
            with TRACKER_FILE.open("r", encoding="utf-8") as f:
                tracker = json.load(f)
            for record in tracker.values():
                md5 = record.get("md5")
                file_path = record.get("file_path")
                if md5 and file_path:
                    index[md5] = file_path
        except Exception:
            pass

    if not RESULTS_FILE.exists():
        return index
    try:
        with RESULTS_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return index

    for entry in data:
        file_path = entry.get("file")
        if not file_path:
            continue
        try:
            md5 = hashlib.md5(Path(file_path).read_bytes()).hexdigest()
        except Exception:
            md5 = hashlib.md5(str(file_path).encode("utf-8")).hexdigest()
        index[md5] = file_path
    return index

ARTICLE_FILE_INDEX = {}
ARTICLE_INDEX_MTIME = None
RESULTS_MTIME = None
TRACKER_MTIME = None

def _load_article_file_index():
    global ARTICLE_FILE_INDEX, ARTICLE_INDEX_MTIME, RESULTS_MTIME, TRACKER_MTIME
    ARTICLE_FILE_INDEX = _build_article_file_index()
    RESULTS_MTIME = os.path.getmtime(RESULTS_FILE) if RESULTS_FILE.exists() else None
    TRACKER_MTIME = os.path.getmtime(TRACKER_FILE) if TRACKER_FILE.exists() else None
    ARTICLE_INDEX_MTIME = max(v for v in [RESULTS_MTIME, TRACKER_MTIME] if v is not None) if (RESULTS_MTIME or TRACKER_MTIME) else None

def _reload_article_index_if_changed():
    current_results = os.path.getmtime(RESULTS_FILE) if RESULTS_FILE.exists() else None
    current_tracker = os.path.getmtime(TRACKER_FILE) if TRACKER_FILE.exists() else None
    current = max(v for v in [current_results, current_tracker] if v is not None) if (current_results or current_tracker) else None
    if ARTICLE_INDEX_MTIME is None or current != ARTICLE_INDEX_MTIME:
        _load_article_file_index()

_load_article_file_index()
PROJECT_ROOT_RESOLVED = PROJECT_ROOT.resolve()

def _is_within_root(path: Path) -> bool:
    try:
        return path.resolve().is_relative_to(PROJECT_ROOT_RESOLVED)
    except AttributeError:
        return str(path.resolve()).startswith(str(PROJECT_ROOT_RESOLVED))

def _resolve_article_path(article_id: str):
    file_path = ARTICLE_FILE_INDEX.get(article_id)
    if not file_path:
        return None
    path = Path(file_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    if not _is_within_root(path):
        return None
    if not path.exists() or not path.is_file():
        return None
    return path

# 初始化 OpenAI 客户端
client = None
if config.OPENAI_API_KEY:
    client = OpenAI(
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_BASE_URL
    )

_SEARCH_STOPWORDS = [
    "相关", "有关", "的", "及", "与", "和", "或", "等", "及其", "以及"
]
_SEARCH_CLEAN_RE = re.compile(r"[\\s\\-_/\\\\()（）\\[\\]{}【】,，。.;；:：'\"“”‘’!?！？·•]")

def _normalize_search_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = _SEARCH_CLEAN_RE.sub("", text)
    for token in _SEARCH_STOPWORDS:
        text = text.replace(token, "")
    return text

def _article_url(node_id):
    if not node_id:
        return None
    if node_id in ARTICLE_FILE_INDEX:
        return f"/files/{node_id}"
    return None

def _with_article_url(node):
    if node.get("group") != "Article":
        return node
    url = _article_url(node.get("id"))
    if not url:
        return node
    enriched = dict(node)
    enriched["url"] = url
    return enriched

_GROUP_WEIGHT = {
    "Article": 0,
    "Claim": 1,
    "Evidence": 2,
    "Ontology": 3,
}

def _prioritize_nodes(nodes):
    seen = set()
    unique = []
    for node in nodes:
        node_id = node.get("id")
        if not node_id or node_id in seen:
            continue
        seen.add(node_id)
        unique.append(node)
    return sorted(unique, key=lambda n: _GROUP_WEIGHT.get(n.get("group"), 9))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def do_GET(self):
        # API 处理: 搜索
        if self.path.startswith('/api/search'):
            self.handle_search()
            return
        if self.path.startswith('/files/'):
            self.handle_file_preview()
            return

        # 默认重定向到问答首页
        if self.path == '/':
            self.path = '/qa_demo.html'
        
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def handle_search(self):
        """处理搜索请求"""
        try:
            _reload_graph_if_changed()
            _reload_article_index_if_changed()
            query_components = parse_qs(urlparse(self.path).query)
            keyword_raw = query_components.get('q', [''])[0].strip()
            keyword = keyword_raw.lower()
            keyword_norm = _normalize_search_text(keyword_raw)
            
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
                
                matched = keyword in name or keyword in content or keyword in desc
                if not matched and keyword_norm:
                    name_norm = _normalize_search_text(name)
                    content_norm = _normalize_search_text(content)
                    desc_norm = _normalize_search_text(desc)
                    matched = keyword_norm in name_norm or keyword_norm in content_norm or keyword_norm in desc_norm

                if matched:
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
                related_article_ids = set()
                matched_ids = {node.get("id") for node in matched_nodes if node.get("id")}

                for node in matched_nodes:
                    node_id = node.get("id")
                    if not node_id:
                        continue

                    if node_id in ARTICLE_IDS:
                        related_article_ids.add(node_id)

                    # Direct neighbors that are articles
                    for neighbor_id in LINKS_BY_SOURCE.get(node_id, []):
                        if neighbor_id in ARTICLE_IDS:
                            related_article_ids.add(neighbor_id)
                    for neighbor_id in LINKS_BY_TARGET.get(node_id, []):
                        if neighbor_id in ARTICLE_IDS:
                            related_article_ids.add(neighbor_id)

                    # Ontology -> Claim/Evidence -> Article
                    if node.get("group") == "Ontology":
                        for claim_id in LINKS_BY_TARGET.get(node_id, []):
                            claim_node = NODES_BY_ID.get(claim_id)
                            if not claim_node:
                                continue
                            if claim_node.get("group") not in {"Claim", "Evidence"}:
                                continue
                            for article_id in LINKS_BY_TARGET.get(claim_id, []):
                                if article_id in ARTICLE_IDS:
                                    related_article_ids.add(article_id)
                            for article_id in LINKS_BY_SOURCE.get(claim_id, []):
                                if article_id in ARTICLE_IDS:
                                    related_article_ids.add(article_id)

                # Append related articles after matched nodes
                related_article_nodes = []
                for article_id in related_article_ids:
                    if article_id in matched_ids:
                        continue
                    article_node = NODES_BY_ID.get(article_id)
                    if article_node:
                        related_article_nodes.append(article_node)

                combined_nodes = [
                    _with_article_url(node) for node in (related_article_nodes + matched_nodes)
                ]
                response_data["nodes"] = _prioritize_nodes(combined_nodes)

                top_claim = next((n for n in matched_nodes if n.get("group") == "Claim"), None)
                if top_claim:
                    response_data["summary"] = f"为您找到相关观点：{top_claim.get('content') or top_claim.get('name')}"
                else:
                    response_data["summary"] = f"在知识库中找到 {len(matched_nodes)} 条相关信息。"

            self.send_json(response_data)

        except Exception as e:
            print(f"Server Error: {e}")
            self.send_json({"error": str(e)}, status=500)

    def handle_file_preview(self):
        _reload_article_index_if_changed()
        article_id = self.path.split("/files/", 1)[-1].strip().split("?")[0]
        if not article_id:
            self.send_error(404, "File not found")
            return
        file_path = _resolve_article_path(article_id)
        if not file_path:
            self.send_error(404, "File not found")
            return
        try:
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            safe_name = quote(file_path.name)
            self.send_header("Content-Disposition", f"inline; filename*=UTF-8''{safe_name}")
            self.send_header("Content-Length", str(file_path.stat().st_size))
            self.end_headers()
            with open(file_path, "rb") as f:
                self.copyfile(f, self.wfile)
        except Exception as e:
            print(f"File preview error: {e}")
            self.send_error(500, "Failed to open file")

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
