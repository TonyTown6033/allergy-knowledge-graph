#!/usr/bin/env python3
"""
知识图谱 API 服务器
提供 Notion 数据的 RESTful API 接口，同时服务静态文件
"""

import json
import sys
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import mimetypes

# 添加父目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config
from src.ontology import ALLERGY_ONTOLOGY
from notion_client import Client


class GraphAPIHandler(SimpleHTTPRequestHandler):
    """API 请求处理器（支持静态文件）"""
    
    def do_GET(self):
        """处理 GET 请求"""
        parsed_path = urlparse(self.path)
        
        # API 路由
        if parsed_path.path.startswith('/api/'):
            self.handle_api_request(parsed_path.path)
        else:
            # 静态文件服务
            if self.path == '/':
                self.path = '/index.html'
            super().do_GET()
    
    def handle_api_request(self, path):
        """处理 API 请求"""
        if path == '/api/ontology':
            self.get_ontology()
        elif path == '/api/claims':
            self.get_claims()
        elif path == '/api/evidence':
            self.get_evidence()
        elif path == '/api/graph':
            self.get_graph_data()
        elif path == '/api/stats':
            self.get_statistics()
        else:
            self.send_error(404, "API Not Found")
    
    def do_OPTIONS(self):
        """处理 OPTIONS 请求（CORS 预检）"""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
    def send_cors_headers(self):
        """发送 CORS 头"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def send_json_response(self, data: dict, status: int = 200):
        """发送 JSON 响应"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def get_ontology(self):
        """获取本体节点数据"""
        try:
            nodes = []
            for node_id, node in ALLERGY_ONTOLOGY.items():
                nodes.append({
                    'id': node.id,
                    'name_zh': node.name_zh,
                    'name_en': node.name_en,
                    'category': node.category.value,
                    'aliases': node.aliases,
                    'description': node.description,
                    'parent_id': node.parent_id
                })
            
            self.send_json_response({
                'success': True,
                'data': nodes,
                'count': len(nodes)
            })
        except Exception as e:
            self.send_json_response({
                'success': False,
                'error': str(e)
            }, 500)
    
    def get_claims(self):
        """从 Notion 获取 Claims 数据"""
        if not config.NOTION_TOKEN or not config.NOTION_CLAIMS_DB_ID:
            self.send_json_response({
                'success': False,
                'error': 'Notion 配置缺失'
            }, 500)
            return
        
        try:
            client = Client(auth=config.NOTION_TOKEN)
            
            # 查询 Claims 数据库（限制返回数量）
            results = client.databases.query(
                database_id=config.NOTION_CLAIMS_DB_ID,
                page_size=100
            )
            
            claims = []
            for page in results.get('results', []):
                props = page.get('properties', {})
                
                # 提取属性值
                name = self._extract_title(props.get('Name', {}))
                content = self._extract_rich_text(props.get('内容', {}))
                polarity = self._extract_select(props.get('极性', {}))
                concepts = self._extract_multi_select(props.get('关联概念', {}))
                source = self._extract_rich_text(props.get('来源标题', {}))
                
                claims.append({
                    'id': page['id'],
                    'title': name,
                    'content': content,
                    'polarity': polarity,
                    'concepts': concepts,
                    'source': source,
                    'url': page.get('url', '')
                })
            
            self.send_json_response({
                'success': True,
                'data': claims,
                'count': len(claims)
            })
        except Exception as e:
            self.send_json_response({
                'success': False,
                'error': str(e)
            }, 500)
    
    def get_evidence(self):
        """从 Notion 获取 Evidence 数据"""
        if not config.NOTION_TOKEN or not config.NOTION_EVIDENCE_DB_ID:
            self.send_json_response({
                'success': False,
                'error': 'Notion 配置缺失'
            }, 500)
            return
        
        try:
            client = Client(auth=config.NOTION_TOKEN)
            
            results = client.databases.query(
                database_id=config.NOTION_EVIDENCE_DB_ID,
                page_size=100
            )
            
            evidences = []
            for page in results.get('results', []):
                props = page.get('properties', {})
                
                name = self._extract_title(props.get('Name', {}))
                content = self._extract_rich_text(props.get('内容', {}))
                source = self._extract_rich_text(props.get('来源标题', {}))
                
                evidences.append({
                    'id': page['id'],
                    'title': name,
                    'content': content,
                    'source': source
                })
            
            self.send_json_response({
                'success': True,
                'data': evidences,
                'count': len(evidences)
            })
        except Exception as e:
            self.send_json_response({
                'success': False,
                'error': str(e)
            }, 500)
    
    def get_graph_data(self):
        """获取完整的图谱数据（节点和边）"""
        try:
            # 本体节点
            ontology_nodes = []
            for node_id, node in ALLERGY_ONTOLOGY.items():
                ontology_nodes.append({
                    'id': node.id,
                    'label': node.name_zh,
                    'type': 'ontology',
                    'category': node.category.value,
                    'description': node.description,
                    'parent_id': node.parent_id
                })
            
            # 从 Notion 获取 Claims
            claims_nodes = []
            edges = []
            
            if config.NOTION_TOKEN and config.NOTION_CLAIMS_DB_ID:
                client = Client(auth=config.NOTION_TOKEN)
                results = client.databases.query(
                    database_id=config.NOTION_CLAIMS_DB_ID,
                    page_size=50  # 限制数量避免过载
                )
                
                for page in results.get('results', []):
                    props = page.get('properties', {})
                    claim_id = page['id']
                    
                    name = self._extract_title(props.get('Name', {}))
                    polarity = self._extract_select(props.get('极性', {}))
                    concepts = self._extract_multi_select(props.get('关联概念', {}))
                    
                    # Claims 节点
                    claims_nodes.append({
                        'id': claim_id,
                        'label': name[:30] + '...' if len(name) > 30 else name,
                        'type': 'claim',
                        'polarity': polarity,
                        'fullTitle': name
                    })
                    
                    # 创建 Claim → Ontology 的边
                    for concept in concepts:
                        edges.append({
                            'source': claim_id,
                            'target': concept,
                            'type': 'concept_relation'
                        })
            
            # 创建 Ontology 父子关系的边
            for node in ontology_nodes:
                if node.get('parent_id'):
                    edges.append({
                        'source': node['id'],
                        'target': node['parent_id'],
                        'type': 'parent_relation'
                    })
            
            all_nodes = ontology_nodes + claims_nodes
            
            self.send_json_response({
                'success': True,
                'data': {
                    'nodes': all_nodes,
                    'edges': edges
                },
                'stats': {
                    'ontology_count': len(ontology_nodes),
                    'claims_count': len(claims_nodes),
                    'edges_count': len(edges)
                }
            })
        except Exception as e:
            import traceback
            self.send_json_response({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }, 500)
    
    def get_statistics(self):
        """获取统计信息"""
        stats = {
            'ontology_nodes': len(ALLERGY_ONTOLOGY),
            'categories': {}
        }
        
        # 统计每个类别的节点数
        for node in ALLERGY_ONTOLOGY.values():
            category = node.category.value
            stats['categories'][category] = stats['categories'].get(category, 0) + 1
        
        self.send_json_response({
            'success': True,
            'data': stats
        })
    
    # 辅助方法：提取 Notion 属性值
    @staticmethod
    def _extract_title(prop: dict) -> str:
        """提取 title 属性"""
        title_array = prop.get('title', [])
        if title_array:
            return title_array[0].get('plain_text', '')
        return ''
    
    @staticmethod
    def _extract_rich_text(prop: dict) -> str:
        """提取 rich_text 属性"""
        rich_text = prop.get('rich_text', [])
        if rich_text:
            return rich_text[0].get('plain_text', '')
        return ''
    
    @staticmethod
    def _extract_select(prop: dict) -> str:
        """提取 select 属性"""
        select = prop.get('select', {})
        if select:
            return select.get('name', '')
        return ''
    
    @staticmethod
    def _extract_multi_select(prop: dict) -> list:
        """提取 multi_select 属性"""
        multi_select = prop.get('multi_select', [])
        return [item.get('name', '') for item in multi_select]


def main():
    PORT = 8001
    
    print("="*70)
    print("知识图谱 API 服务器")
    print("="*70)
    print(f"\n启动中...")
    print(f"端口: {PORT}")
    print(f"\nAPI 端点:")
    print(f"  GET /api/ontology    - 获取本体节点")
    print(f"  GET /api/claims      - 获取观点数据")
    print(f"  GET /api/evidence    - 获取证据数据")
    print(f"  GET /api/graph       - 获取完整图谱数据")
    print(f"  GET /api/stats       - 获取统计信息")
    print(f"\n访问前端: http://localhost:{PORT}/")
    print(f"\n按 Ctrl+C 停止服务器")
    print("="*70 + "\n")
    
    server = HTTPServer(('localhost', PORT), GraphAPIHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n服务器已停止")
        server.shutdown()


if __name__ == "__main__":
    main()
