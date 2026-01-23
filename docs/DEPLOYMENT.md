# 服务器部署指南

本指南介绍如何将过敏知识图谱系统部署到生产服务器。

## 📋 前置要求

- **服务器**：Linux (Ubuntu 20.04+ 推荐) 或 CentOS
- **Python**：3.11+
- **域名**（可选）：如 `allergy.yourdomain.com`
- **端口**：80 (HTTP) 或 443 (HTTPS)

---

## 🚀 快速部署（推荐方式）

### 方案一：使用 Nginx + Gunicorn (生产级)

#### 1. 克隆项目到服务器

```bash
# SSH 登录到服务器
ssh user@your-server-ip

# 克隆仓库
cd /var/www/
git clone https://github.com/TonyTown6033/allergy-knowledge-graph.git
cd allergy-knowledge-graph
```

#### 2. 安装依赖

```bash
# 安装 Python 和 pip (如果没有)
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip -y

# 安装 uv (推荐)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装项目依赖
uv pip install -r requirements.txt
uv pip install gunicorn
```

#### 3. 配置环境变量

```bash
# 复制环境变量模板
cp env.example.txt .env

# 编辑配置文件
nano .env
# 填入你的 Notion Token、Database ID、OpenAI API Key 等
```

#### 4. 生成图谱数据

```bash
# 从 Notion 拉取数据（如果有配置）
uv run python scripts/export_graph_data.py --mode notion

# 或从本地 results.json 生成
uv run python scripts/export_graph_data.py --mode local

# 翻译成中文（可选，如果数据是英文）
uv run python scripts/translate_graph.py
```

#### 5. 创建 WSGI 入口文件

由于当前的 `graph_view/server.py` 使用的是简单的 HTTP Server，我们需要改造成 WSGI 应用。

创建 `graph_view/wsgi_app.py`：

```python
import os
import json
import sys
from pathlib import Path
from urllib.parse import parse_qs
from openai import OpenAI

# 添加项目根目录到 path
sys.path.append(str(Path(__file__).parent.parent))
from src.config import config

# 加载数据
DATA_FILE = os.path.join(os.path.dirname(__file__), "graph_data.json")
GRAPH_DATA = {"nodes": [], "links": []}
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        GRAPH_DATA = json.load(f)

# 初始化 OpenAI
client = None
if config.OPENAI_API_KEY:
    client = OpenAI(
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_BASE_URL
    )

def application(environ, start_response):
    """WSGI Application"""
    path = environ.get('PATH_INFO', '/')
    
    # API 路由
    if path.startswith('/api/search'):
        query_string = environ.get('QUERY_STRING', '')
        params = parse_qs(query_string)
        keyword = params.get('q', [''])[0].lower().strip()
        
        # 搜索逻辑（复用之前的逻辑）
        matched_nodes = []
        for node in GRAPH_DATA.get("nodes", []):
            name = (node.get("name") or "").lower()
            content = (node.get("content") or "").lower()
            desc = (node.get("description") or "").lower()
            if keyword in name or keyword in content or keyword in desc:
                matched_nodes.append(node)
        
        response_data = {"source": "db", "nodes": matched_nodes, "summary": ""}
        
        if len(matched_nodes) == 0 and client:
            # AI 兜底
            try:
                ai_response = call_ai_search(keyword, client, config)
                response_data["source"] = "ai"
                response_data["summary"] = ai_response
                response_data["nodes"] = [{"id": "ai-result", "group": "AI_Answer", "name": "AI 智能回答", "content": ai_response, "val": 20}]
            except:
                response_data["summary"] = "未找到相关内容。"
        else:
            top_claim = next((n for n in matched_nodes if n.get("group") == "Claim"), None)
            if top_claim:
                response_data["summary"] = f"为您找到相关观点：{top_claim.get('content') or top_claim.get('name')}"
            else:
                response_data["summary"] = f"在知识库中找到 {len(matched_nodes)} 条相关信息。"
        
        # 返回 JSON
        response_body = json.dumps(response_data).encode('utf-8')
        status = '200 OK'
        headers = [('Content-Type', 'application/json'), ('Content-Length', str(len(response_body)))]
        start_response(status, headers)
        return [response_body]
    
    # 静态文件（简化处理，生产环境建议用 Nginx 直接处理静态文件）
    # 这里返回 404，让 Nginx 处理
    status = '404 Not Found'
    start_response(status, [('Content-Type', 'text/plain')])
    return [b'Not Found']

def call_ai_search(keyword, client, config):
    prompt = f"用户查询：{keyword}。请作为过敏科医生回答，300字以内。"
    completion = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[{"role": "system", "content": "你是一个专业的过敏科医学助手。"}, {"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content
```

#### 6. 配置 Gunicorn

创建 `gunicorn_config.py`：

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
timeout = 120
accesslog = "/var/log/gunicorn_access.log"
errorlog = "/var/log/gunicorn_error.log"
```

#### 7. 配置 Nginx

创建 `/etc/nginx/sites-available/allergy`：

```nginx
server {
    listen 80;
    server_name allergy.yourdomain.com;  # 改成你的域名

    # 静态文件目录
    root /var/www/allergy-knowledge-graph/graph_view;
    index qa_demo.html;

    # API 转发到 Gunicorn
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 静态文件
    location / {
        try_files $uri $uri/ /qa_demo.html;
    }

    # 禁止访问敏感文件
    location ~ /\. {
        deny all;
    }
}
```

启用站点：

```bash
sudo ln -s /etc/nginx/sites-available/allergy /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 8. 启动 Gunicorn

```bash
cd /var/www/allergy-knowledge-graph/graph_view
gunicorn -c ../gunicorn_config.py wsgi_app:application
```

#### 9. 配置 Systemd 服务（自动启动）

创建 `/etc/systemd/system/allergy-graph.service`：

```ini
[Unit]
Description=Allergy Knowledge Graph Service
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/allergy-knowledge-graph/graph_view
Environment="PATH=/var/www/allergy-knowledge-graph/.venv/bin"
ExecStart=/var/www/allergy-knowledge-graph/.venv/bin/gunicorn -c ../gunicorn_config.py wsgi_app:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
Restart=always

[Install]
WantedBy=multi-user.target
```

启用并启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable allergy-graph
sudo systemctl start allergy-graph
sudo systemctl status allergy-graph
```

---

### 方案二：Docker 部署（简化版）

#### 1. 创建 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

# 生成图谱数据
RUN python scripts/export_graph_data.py --mode local

EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "graph_view.wsgi_app:application"]
```

#### 2. 构建并运行

```bash
docker build -t allergy-graph .
docker run -d -p 8000:8000 --name allergy-graph \
  -e OPENAI_API_KEY="your_key" \
  -e NOTION_TOKEN="your_token" \
  allergy-graph
```

---

### 方案三：最简单部署（适合开发/演示）

如果只是临时演示，可以直接在服务器后台运行：

```bash
cd /var/www/allergy-knowledge-graph
nohup uv run python graph_view/server.py > server.log 2>&1 &
```

但这**不推荐用于生产环境**（进程管理不稳定）。

---

## 🔒 安全建议

1.  **不要将 `.env` 文件提交到 Git**（已在 `.gitignore` 中）。
2.  **配置 HTTPS**：使用 Let's Encrypt (Certbot) 免费证书。
    ```bash
    sudo apt install certbot python3-certbot-nginx
    sudo certbot --nginx -d allergy.yourdomain.com
    ```
3.  **限制 API 访问频率**：防止恶意调用 OpenAI API。

---

## 📊 监控与日志

查看日志：

```bash
# Gunicorn 日志
tail -f /var/log/gunicorn_error.log

# Nginx 日志
tail -f /var/nginx/error.log

# Systemd 服务日志
journalctl -u allergy-graph -f
```

---

## 🔄 更新部署

当代码有更新时：

```bash
cd /var/www/allergy-knowledge-graph
git pull origin master
uv pip install -r requirements.txt
sudo systemctl restart allergy-graph
```

---

如有问题，请查看日志或联系开发者。
