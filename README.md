# 过敏知识图谱系统

基于 AI 的医学文献知识提取与管理系统，专注于过敏性疾病领域。

## ✨ 核心功能

### 📚 知识提取
- **PDF 自动提取**：使用 OpenAI GPT 从医学文献中提取结构化信息
- **观点识别**：自动识别文献中的核心论点和立场
- **证据追溯**：提取支持观点的原文引用
- **概念映射**：将观点关联到预定义的医学概念本体

### 🗄️ Notion 集成
- **四个数据库**：
  - **Articles**: 文章全文存储
  - **Claims**: 观点管理
  - **Evidence**: 证据引用
  - **Ontology**: 医学概念本体（27个核心概念）

### 🔄 智能去重
- **MD5 哈希追踪**：自动识别已处理文件
- **本地缓存**：维护处理历史记录
- **统计报告**：查看提取进度和统计

### 🔗 知识关联
```
Article (原文) → Claims (观点) ← Evidence (证据)
                     ↓
                 Ontology (概念)
```

---

## 🛠️ 部署与启动

> 本节为完整部署流程。如果只想快速跑起来，至少需要完成 **步骤 0~3**（环境 + 依赖 + `.env`），
> 再按 **步骤 6** 启动你需要的服务。

### 步骤 0：前置要求

| 工具 | 版本 | 说明 |
|------|------|------|
| Python | 3.11+ | 推荐用 `pyenv` 管理多版本 |
| uv | 最新 | 依赖与虚拟环境管理（推荐） |
| OpenAI API Key | — | 文本分析、观点提取 |
| Notion 集成 Token | — | 知识库存储（免费版即可） |

安装 `uv`（若未安装）：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

用 `pyenv` 准备 Python（可选）：

```bash
pyenv install 3.11.13
pyenv local 3.11.13
```

### 步骤 1：获取代码并创建虚拟环境

```bash
git clone <仓库地址> alergy
cd alergy

# 创建并使用本地虚拟环境（uv 会自动识别 .venv）
uv venv
```

### 步骤 2：安装依赖

```bash
uv pip install -r requirements.txt
# 不用 uv 时可退回：
# pip install -r requirements.txt
```

### 步骤 3：配置环境变量

```bash
cp env.example.txt .env
```

编辑 `.env`，填入真实值（字段含义见底部「🔧 配置说明」）：

```bash
NOTION_TOKEN=secret_xxx...           # 必填
NOTION_CLAIMS_DB_ID=xxx...           # 必填
NOTION_EVIDENCE_DB_ID=xxx...
NOTION_ONTOLOGY_DB_ID=xxx...
NOTION_ARTICLES_DB_ID=xxx...
OPENAI_API_KEY=sk-xxx...             # 必填
OPENAI_MODEL=gpt-4o                  # 可选，默认 gpt-4o
# OPENAI_BASE_URL=https://api.openai.com/v1   # 可选，自定义/兼容端点
```

校验配置是否就绪（最少需要 `NOTION_TOKEN`、`NOTION_CLAIMS_DB_ID`、`OPENAI_API_KEY`）：

```bash
uv run python main.py config
```

### 步骤 4：初始化 Notion 数据库

在 Notion 中新建一个页面，并把你的集成（integration）共享给该页面，复制页面 ID，然后：

```bash
# YOUR_PAGE_ID 为目标页面 ID
uv run python tools/create_notion_databases.py YOUR_PAGE_ID   # Ontology / Claims / Evidence
uv run python tools/create_articles_database.py YOUR_PAGE_ID  # Articles
```

把生成的各数据库 ID 回填到 `.env` 的 `NOTION_*_DB_ID`。
免费版用户的逐列设置请参考 `docs/免费版用户指南.md`。

### 步骤 5：同步本体（首次必做）

```bash
uv run python main.py ontology sync
```

### 步骤 6：启动服务

本项目包含 **三个相互独立的服务**，按需启动：

#### 6.1 后台管理系统（Flask，端口 5001）

文章上传、AI 分析、观点/本体管理的 Web 后台。

```bash
# 方式一：一键脚本（自动检测 5001~5010 可用端口）
./start_admin.sh

# 方式二：手动启动，可用 FLASK_PORT 指定端口
FLASK_PORT=5001 uv run python admin/app.py
```

访问：`http://localhost:5001`

#### 6.2 知识图谱可视化前台（端口 8000）

问答式 2D/3D 图谱浏览与文献预览。**启动前需先生成图谱数据**：

```bash
# 1) 从本地 results.json 生成图谱数据
uv run python scripts/export_graph_data.py --mode local

# 2) 启动可视化服务器
uv run python graph_view/server.py
```

访问：`http://localhost:8000`（启动后会自动打开浏览器）

#### 6.3 视频播放器（端口 8000，可选）

教学视频播放，附加功能。

```bash
cd video_player && python server.py
```

访问：`http://localhost:8000`

> ⚠️ **端口冲突提示**：`graph_view` 与 `video_player` 默认都用 **8000**，不要同时启动；
> 后台管理系统用 5001，与前者互不影响。

### 步骤 7：处理文献（日常使用）

```bash
# 智能上传单个 PDF（带 MD5 去重）
uv run python scripts/upload_auto.py your_file.pdf

# 查看处理统计
uv run python scripts/upload_complete.py --stats
```

### 步骤 8：运行测试（开发者）

```bash
# 项目自带 pytest；用项目环境运行：
uv run --with pytest python -m pytest tests/ -q
```

> 注意：直接 `uv run pytest` 会进入隔离环境而缺少项目依赖（如 `dotenv`），
> 请用上面的 `uv run --with pytest python -m pytest`，或先 `uv pip install pytest`
> 后用 `uv run python -m pytest tests/ -q`。

### 后台常驻运行（可选）

开发用 `debug=True` 自带自动重载，**生产环境请勿开 debug**。需要常驻时可用 `nohup`：

```bash
nohup uv run python admin/app.py > admin.log 2>&1 &
nohup uv run python graph_view/server.py > graph.log 2>&1 &
```

---

## 📖 使用指南

### 基础命令

```bash
# 查看所有本体节点
uv run python main.py ontology list

# 搜索文本中的概念
uv run python main.py search "IgE 过敏性鼻炎"

# 检查配置
uv run python main.py config
```

### 文献处理

```bash
# 智能上传（推荐）
uv run python scripts/upload_auto.py file.pdf          # PDF 格式（需手动拖拽）
uv run python scripts/upload_auto.py file.pdf --text   # 纯文本（全自动）

# 完整上传（带去重）
uv run python scripts/upload_complete.py file.pdf --force

# 批量处理（保存为 JSON）
uv run python main.py batch directory/ -o results.json

# 上传已提取的结果
uv run python scripts/upload_results.py results.json

# 查看统计
uv run python scripts/upload_complete.py --stats
```

### 测试和演示

```bash
# Evidence 功能演示
uv run python scripts/demo_evidence_workflow.py

# 测试 Evidence 数据库
uv run python scripts/test_evidence.py
```

### 视频播放器

```bash
# 启动视频服务器
cd video_player && python server.py
# 访问 http://localhost:8000
```

---

## 📊 数据库结构

### Articles (文章)
- **Name**: 文章标题
- **MD5**: 文件哈希（去重用）
- **文件路径**: 本地路径
- **文件大小**: 字节数
- **来源链接**: 外部链接
- **页面内容**: 文章全文

### Claims (观点)
- **Name**: 观点标题
- **内容**: 观点详细描述
- **极性**: 支持/反驳/中立
- **关联概念**: 关联的本体节点
- **来源标题**: 来源文献
- **来源链接**: 指向 Article

### Evidence (证据)
- **Name**: 证据标题
- **内容**: 原文引用
- **来源标题**: 来源文献
- **来源链接**: 外部链接
- **页码**: 页码信息

### Ontology (本体)
- **Name**: 概念名称（中文）
- **ID**: 概念唯一标识
- **英文名**: 英文名称
- **类别**: 8个类别
- **别名**: 同义词列表
- **描述**: 概念说明
- **父节点**: 层级关系

---

## 🏗️ 项目结构

```
alergy/
├── main.py                     # 主程序入口
├── requirements.txt            # Python 依赖
├── env.example.txt             # 配置模板
├── README.md                   # 项目说明
│
├── src/                        # 核心模块
│   ├── config.py               # 配置管理
│   ├── ontology.py             # 医学概念本体（27个节点）
│   ├── extractor.py            # PDF 提取和 AI 处理
│   ├── notion_client.py        # Notion API 集成
│   └── file_tracker.py         # 文件追踪和去重
│
├── scripts/                    # 上传和处理脚本
│   ├── upload_auto.py          # 智能上传（推荐）⭐
│   ├── upload_complete.py      # 完整上传（带去重）
│   ├── upload_with_evidence.py # 观点+证据上传
│   ├── upload_results.py       # 批量结果上传
│   ├── upload_with_pdf.py      # PDF 格式上传
│   ├── demo_evidence_workflow.py # 演示脚本
│   └── test_evidence.py        # 测试脚本
│
├── tools/                      # 数据库管理工具
│   ├── create_notion_databases.py    # 创建主数据库
│   ├── create_articles_database.py   # 创建 Articles 库
│   ├── check_notion_schema.py        # 检查数据库结构
│   ├── add_database_columns.py       # 添加数据库列
│   └── ...                           # 其他工具
│
├── docs/                       # 文档
│   ├── 文章上传和去重指南.md
│   ├── EVIDENCE使用指南.md
│   ├── PDF格式保留方案.md
│   ├── 功能测试清单.md
│   ├── 免费版用户指南.md
│   └── ...
│
├── video_player/               # 视频播放器（附加功能）
│   ├── server.py               # 视频服务器
│   └── index.html              # 播放器页面
│
└── download/                   # 医学文献和视频（gitignore）
```

---

## 📚 文档索引

- **`README.md`** (本文档) - 项目总览
- **`docs/文章上传和去重指南.md`** - 文章上传和 MD5 去重功能 ⭐
- **`docs/EVIDENCE使用指南.md`** - Evidence 功能详解
- **`docs/PDF格式保留方案.md`** - PDF 格式保留方案
- **`docs/功能测试清单.md`** - 所有功能和测试方法
- **`docs/免费版用户指南.md`** - Notion 免费版设置
- **`docs/NOTION_SETUP.md`** - Notion 数据库配置
- **`docs/手动初始化指南.md`** - 手动设置说明
- **`docs/VIDEO_PLAYER_README.md`** - 视频播放器说明
- **`docs/GRAPH_VIEW_README.md`** - 3D 知识图谱说明


---

## 🧪 测试状态

### ✅ 已测试功能
- [x] Ontology 管理和同步
- [x] 文本概念搜索
- [x] PDF 提取（单个/批量）
- [x] Claims 上传
- [x] Evidence 上传和关联
- [x] 配置检查

### 🆕 新功能
- [x] Articles 全文上传
- [x] MD5 去重机制
- [x] 处理历史追踪
- [x] 统计报告

---

## 🛠️ 技术栈

- **Python 3.11+**
- **OpenAI GPT-4** - 文本分析和观点提取
- **Notion API** - 知识库存储
- **pdfplumber** - PDF 文本提取
- **uv** - 依赖管理（推荐）

---

## ⚙️ 系统要求

- Python 3.11 或更高版本
- OpenAI API 访问权限
- Notion 工作区（免费版即可）
- 4GB+ RAM（处理大型 PDF）

---

## 🔧 配置说明

### 必需配置
```bash
NOTION_TOKEN=secret_xxx...           # Notion API Token
NOTION_CLAIMS_DB_ID=xxx...           # Claims 数据库 ID
NOTION_EVIDENCE_DB_ID=xxx...         # Evidence 数据库 ID
NOTION_ONTOLOGY_DB_ID=xxx...         # Ontology 数据库 ID
NOTION_ARTICLES_DB_ID=xxx...         # Articles 数据库 ID ⭐
OPENAI_API_KEY=sk-xxx...             # OpenAI API Key
```

### 可选配置
```bash
OPENAI_MODEL=gpt-4o                  # 模型选择
OPENAI_BASE_URL=https://...          # 自定义 API 端点
```

---

## 📈 使用示例

### 场景 1：处理新文献

```bash
# 1. 下载 PDF 到 download/ 目录
# 2. 处理文件
uv run python upload_complete.py "download/新文献.pdf"

# 输出：
# ✓ 文件未处理
# ✓ 提取文本: 50000 字符
# ✓ 提取观点: 6 个
# ✓ 提取证据: 6 个
# ✓ 文章已上传
# ✓ 观点和证据已上传
```

### 场景 2：批量处理目录

```bash
# 处理目录下所有 PDF
uv run python main.py batch download/目录/ -o batch_results.json

# 上传结果
uv run python upload_results.py batch_results.json
```

### 场景 3：查询和分析

在 Notion 中：
1. 打开 Claims 数据库
2. 按"关联概念"筛选（如：IgE）
3. 查看所有相关观点
4. 点击"来源链接"查看原文

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- OpenAI GPT-4 提供智能文本分析
- Notion 提供知识库平台
- 医学文献来源：各专家共识和诊疗指南

---

## 📞 联系方式

如有问题，请查看文档或提交 Issue。

**祝你使用愉快！**🎉
