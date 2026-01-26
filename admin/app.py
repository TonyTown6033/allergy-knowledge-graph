#!/usr/bin/env python3
"""
过敏知识图谱 - 后台管理系统
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config
from src.notion_client import NotionDatabase
from src.file_tracker import FileTracker
from src.extractor import ArticleExtractor
from src.ontology import ALLERGY_ONTOLOGY, get_nodes_by_category, ConceptCategory

app = Flask(__name__)
app.config['SECRET_KEY'] = 'allergy-admin-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['MAX_FILENAME_BYTES'] = 255  # filesystem-friendly limit

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 全局变量
PROJECT_ROOT = Path(__file__).parent.parent


# ==================== 路由 ====================

@app.route('/')
def index():
    """首页 - 仪表板"""
    return render_template('index.html')


@app.route('/articles')
def articles():
    """文章管理页面"""
    return render_template('articles.html')


@app.route('/claims')
def claims():
    """观点管理页面"""
    return render_template('claims.html')


@app.route('/ontology')
def ontology():
    """本体管理页面"""
    return render_template('ontology.html')


@app.route('/sync')
def sync():
    """数据同步页面"""
    return render_template('sync.html')


# ==================== API 路由 ====================

@app.route('/api/dashboard/stats')
def api_dashboard_stats():
    """获取仪表板统计数据"""
    try:
        # 读取本地数据
        results_file = PROJECT_ROOT / 'results.json'
        graph_file = PROJECT_ROOT / 'graph_view' / 'graph_data.json'
        tracker_file = PROJECT_ROOT / '.processed_files.json'
        
        stats = {
            'local_articles': 0,
            'local_claims': 0,
            'uploaded_articles': 0,
            'uploaded_claims': 0,
            'graph_nodes': 0,
            'graph_links': 0,
            'ontology_nodes': len(ALLERGY_ONTOLOGY)
        }
        
        # 本地数据
        if results_file.exists():
            with open(results_file, encoding='utf-8') as f:
                results = json.load(f)
            stats['local_articles'] = len(results)
            stats['local_claims'] = sum(len(r.get('claims', [])) for r in results)
        
        # 上传记录
        if tracker_file.exists():
            with open(tracker_file, encoding='utf-8') as f:
                tracker = json.load(f)
            stats['uploaded_articles'] = len(tracker)
            stats['uploaded_claims'] = sum(r.get('claims_count', 0) for r in tracker.values())
        
        # 图谱数据
        if graph_file.exists():
            with open(graph_file, encoding='utf-8') as f:
                graph = json.load(f)
            stats['graph_nodes'] = len(graph.get('nodes', []))
            stats['graph_links'] = len(graph.get('links', []))
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/articles/list')
def api_articles_list():
    """获取文章列表"""
    try:
        results_file = PROJECT_ROOT / 'results.json'
        tracker_file = PROJECT_ROOT / '.processed_files.json'
        
        if not results_file.exists():
            return jsonify({'success': True, 'data': []})
        
        with open(results_file, encoding='utf-8') as f:
            articles = json.load(f)
        
        # 读取上传状态
        uploaded_files = set()
        if tracker_file.exists():
            with open(tracker_file, encoding='utf-8') as f:
                tracker = json.load(f)
            uploaded_files = {r['file_path'] for r in tracker.values()}
        
        # 添加上传状态
        for article in articles:
            article['uploaded'] = article.get('file', '') in uploaded_files
        
        return jsonify({
            'success': True,
            'data': articles
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/articles/upload', methods=['POST'])
def api_articles_upload():
    """上传新文章并执行 AI 分析"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '文件名为空'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': '只支持 PDF 文件'}), 400
        
        # 1. 保存文件到 download 目录（与主系统保持一致）
        filename = file.filename
        # 不自动处理长文件名：直接校验并报错
        if filename != os.path.basename(filename):
            return jsonify({'success': False, 'error': '文件名不合法'}), 400
        if len(filename.encode('utf-8')) > app.config['MAX_FILENAME_BYTES']:
            return jsonify({'success': False, 'error': '文件名过长，请缩短后再上传'}), 400
        download_dir = PROJECT_ROOT / 'download' / 'uploads'
        os.makedirs(download_dir, exist_ok=True)
        file_path = download_dir / filename
        file.save(file_path)
        
        # 2. 初始化工具
        extractor = ArticleExtractor()
        notion = NotionDatabase()
        tracker = FileTracker()
        
        # 3. 提取文本和观点
        print(f"正在分析文章: {filename}")
        full_text = extractor.extract_text_from_pdf(file_path)
        claims, evidences = extractor.process_pdf_with_evidence(file_path)
        
        # 4. 更新本地 results.json
        results_file = PROJECT_ROOT / 'results.json'
        results_data = []
        if results_file.exists():
            with open(results_file, 'r', encoding='utf-8') as f:
                results_data = json.load(f)
        
        # 检查是否已存在（去重）
        new_entry = {
            "file": str(file_path.relative_to(PROJECT_ROOT)),
            "title": file_path.stem,
            "claims": [
                {
                    "title": c.title,
                    "content": c.content,
                    "polarity": c.polarity.value,
                    "mapped_nodes": c.mapped_nodes
                } for c in claims
            ]
        }
        
        # 简单替换或添加
        existing_idx = next((i for i, r in enumerate(results_data) if r.get('title') == new_entry['title']), -1)
        if existing_idx >= 0:
            results_data[existing_idx] = new_entry
        else:
            results_data.append(new_entry)
            
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)

        # 5. 上传到 Notion
        print(f"正在同步到 Notion...")
        from src.notion_client import Article
        md5 = tracker.calculate_md5(file_path)
        
        article = Article(
            title=file_path.stem,
            content="", # PDF 模式不传全文
            file_path=str(file_path),
            file_md5=md5,
            file_size=file_path.stat().st_size
        )
        
        article_page = notion.add_article(article)
        article_id = article_page["id"]
        
        for claim in claims:
            claim.source_title = file_path.stem
            notion.add_claim(claim)
            
        for evidence in evidences:
            evidence.source_title = file_path.stem
            notion.add_evidence(evidence)
            
        # 6. 记录到追踪器
        tracker.mark_processed(
            file_path=file_path,
            notion_article_id=article_id,
            claims_count=len(claims),
            evidence_count=len(evidences)
        )
        
        # 7. 自动触发图谱重新生成（本地模式）
        import subprocess
        subprocess.run(['uv', 'run', 'python', 'scripts/export_graph_data.py', '--mode', 'local'], cwd=str(PROJECT_ROOT))
        
        return jsonify({
            'success': True,
            'message': f'成功分析并上传！提取了 {len(claims)} 个观点，{len(evidences)} 条证据。',
            'data': {
                'title': file_path.stem,
                'claims_count': len(claims),
                'evidence_count': len(evidences)
            }
        })
        
    except Exception as e:
        print(f"上传分析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/claims/list')
def api_claims_list():
    """获取观点列表"""
    try:
        results_file = PROJECT_ROOT / 'results.json'
        
        if not results_file.exists():
            return jsonify({'success': True, 'data': []})
        
        with open(results_file, encoding='utf-8') as f:
            articles = json.load(f)
        
        # 展开所有观点
        all_claims = []
        for article in articles:
            for claim in article.get('claims', []):
                claim['source'] = article.get('title', '未知')
                all_claims.append(claim)
        
        return jsonify({
            'success': True,
            'data': all_claims
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ontology/list')
def api_ontology_list():
    """获取本体列表"""
    try:
        nodes = []
        for node_id, node in ALLERGY_ONTOLOGY.items():
            nodes.append({
                'id': node_id,
                'name_zh': node.name_zh,
                'name_en': node.name_en,
                'category': node.category.value,
                'aliases': node.aliases,
                'description': node.description
            })
        
        return jsonify({
            'success': True,
            'data': nodes
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/sync/export-graph', methods=['POST'])
def api_sync_export_graph():
    """导出图谱数据"""
    try:
        data = request.get_json()
        mode = data.get('mode', 'local')  # 'local' 或 'notion'
        
        # 执行导出脚本
        import subprocess
        result = subprocess.run(
            ['uv', 'run', 'python', 'scripts/export_graph_data.py', '--mode', mode],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': '图谱数据生成成功',
                'output': result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'error': result.stderr
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/sync/upload-batch', methods=['POST'])
def api_sync_upload_batch():
    """批量上传文章"""
    try:
        # 执行批量上传脚本
        import subprocess
        result = subprocess.run(
            ['uv', 'run', 'python', 'scripts/batch_upload_all.py'],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=3600  # 1小时超时
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': '批量上传完成',
                'output': result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'error': result.stderr
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== 启动 ====================

if __name__ == '__main__':
    import os
    port = int(os.environ.get('FLASK_PORT', 5001))
    
    print("="*60)
    print("过敏知识图谱 - 后台管理系统")
    print("="*60)
    print(f"访问地址: http://localhost:{port}")
    print(f"项目根目录: {PROJECT_ROOT}")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=port)
