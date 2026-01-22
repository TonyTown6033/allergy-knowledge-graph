# 3D 知识图谱可视化

本模块提供了一个交互式的 3D 知识图谱视图，用于展示 Notion 数据库中的文章、观点、证据及其与医学本体的关联。

## ✨ 功能特点

- **3D 交互视图**：使用力导向图（Force-Directed Graph）展示知识网络
- **节点类型区分**：
  - 🔴 **Article (文章)**: 原始文献
  - 🟢 **Claim (观点)**: 提取的核心观点
  - 🔵 **Ontology (概念)**: 医学本体节点
  - 🟡 **Evidence (证据)**: 支持观点的原文证据
- **详情查看**：点击节点可查看详细信息（内容、极性、描述等）
- **自动聚焦**：点击节点自动调整相机视角

## 🚀 快速开始

### 1. 生成图谱数据

你可以选择从本地 `results.json` 生成，或直接从 Notion 数据库拉取。

#### 从本地结果生成 (推荐用于测试)
```bash
uv run python scripts/export_graph_data.py --mode local
```

#### 从 Notion 数据库生成
确保你已配置好 `.env` 文件中的 Notion 凭证。
```bash
uv run python scripts/export_graph_data.py --mode notion
```

### 2. 启动可视化服务

```bash
uv run python graph_view/server.py
```

服务启动后，浏览器将自动打开 `http://localhost:8000`。

## 📁 目录结构

```
graph_view/
├── index.html          # 前端可视化页面
├── server.py           # 轻量级 HTTP 服务器
└── graph_data.json     # 生成的图谱数据
```

## 🔗 关联逻辑

- **Article** 包含 **Claim**
- **Claim** 关联到 **Ontology** (通过 `mapped_nodes`)
- **Ontology** 之间存在层级关系 (通过 `parent_id`)
- **Evidence** (目前主要通过 Notion 关联，本地模式下视数据结构而定)

## 🛠️ 技术实现

- **前端**: [3d-force-graph](https://github.com/vasturiano/3d-force-graph)
- **后端**: Python HTTP Server
- **数据处理**: Python 脚本提取并转换为 JSON 格式
