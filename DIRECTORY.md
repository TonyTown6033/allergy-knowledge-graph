# 项目目录说明

## 📁 目录结构

```
alergy/                         # 过敏知识图谱系统根目录
│
├── main.py                     # ⭐ 主程序入口
├── requirements.txt            # Python 依赖包
├── env.example.txt             # 环境变量配置模板
├── .gitignore                  # Git 忽略规则
├── README.md                   # 项目说明文档
├── DIRECTORY.md                # 本文件 - 目录说明
│
├── src/                        # 核心模块目录
│   ├── __init__.py             # Python 包初始化
│   ├── config.py               # 配置管理
│   ├── ontology.py             # 医学概念本体定义（27个节点）
│   ├── extractor.py            # PDF 提取和 AI 处理
│   ├── notion_client.py        # Notion API 客户端
│   └── file_tracker.py         # 文件追踪和 MD5 去重
│
├── scripts/                    # 上传和处理脚本目录
│   ├── upload_auto.py          # ⭐ 智能上传（推荐使用）
│   ├── upload_complete.py      # 完整上传（带去重和统计）
│   ├── upload_with_evidence.py # 观点+证据上传
│   ├── upload_with_pdf.py      # PDF 格式上传
│   ├── upload_results.py       # 批量结果上传
│   ├── demo_evidence_workflow.py # Evidence 功能演示
│   └── test_evidence.py        # Evidence 功能测试
│
├── tools/                      # 数据库管理工具目录
│   ├── create_notion_databases.py    # 创建主数据库（Ontology, Claims, Evidence）
│   ├── create_articles_database.py   # 创建 Articles 数据库
│   ├── check_notion_schema.py        # 检查数据库结构
│   ├── add_database_columns.py       # 添加数据库列
│   ├── debug_database.py             # 调试数据库
│   ├── query_database.py             # 查询数据库
│   └── ...                           # 其他辅助工具
│
├── docs/                       # 文档目录
│   ├── 文章上传和去重指南.md         # 文章上传功能说明
│   ├── EVIDENCE使用指南.md          # Evidence 功能详解
│   ├── PDF格式保留方案.md           # PDF 格式处理方案
│   ├── 功能测试清单.md              # 所有功能测试清单
│   ├── 免费版用户指南.md            # Notion 免费版设置指南
│   ├── NOTION_SETUP.md             # Notion 数据库配置
│   ├── 手动初始化指南.md            # 手动设置说明
│   └── VIDEO_PLAYER_README.md      # 视频播放器说明
│
├── video_player/               # 视频播放器（附加功能）
│   ├── server.py               # Python 视频服务器
│   └── index.html              # HTML5 播放器页面
│
└── download/                   # 医学文献和视频（不提交到 git）
    ├── learning/               # 教学视频
    │   └── *.mp4
    └── 过敏原及自身抗体相关指南共识/  # PDF 文献
        ├── 过敏原/
        │   └── *.pdf
        └── 自免/
            └── *.pdf
```

---

## 🎯 核心文件说明

### 主程序
- **`main.py`** - 命令行工具，提供 extract、batch、ontology、search、config 等命令

### 最常用的脚本
- **`scripts/upload_auto.py`** ⭐ - 智能上传，支持 PDF/文本两种模式
- **`scripts/upload_complete.py`** - 完整上传流程，带去重和统计
- **`main.py`** - 命令行工具（ontology list/sync, search 等）

### 数据库管理
- **`tools/create_notion_databases.py`** - 一键创建所有 Notion 数据库
- **`tools/check_notion_schema.py`** - 检查数据库结构是否正确

### 文档
- **`README.md`** - 从这里开始
- **`docs/`** - 所有详细文档

---

## 🚀 快速开始路径

### 第一次使用：

1. **安装**: `uv pip install -r requirements.txt`
2. **配置**: `cp env.example.txt .env` 并填写配置
3. **创建数据库**: `uv run python tools/create_notion_databases.py YOUR_PAGE_ID`
4. **同步本体**: `uv run python main.py ontology sync`
5. **开始使用**: `uv run python scripts/upload_auto.py file.pdf`

### 日常使用：

```bash
# 处理文献
uv run python scripts/upload_auto.py file.pdf

# 查看统计
uv run python scripts/upload_complete.py --stats

# 播放视频
cd video_player && python server.py
```

---

## 📂 目录用途

| 目录 | 用途 | 提交到 Git |
|------|------|-----------|
| `src/` | 核心业务逻辑 | ✅ 是 |
| `scripts/` | 用户脚本 | ✅ 是 |
| `tools/` | 管理工具 | ✅ 是 |
| `docs/` | 文档 | ✅ 是 |
| `video_player/` | 附加功能 | ✅ 是 |
| `download/` | 数据文件 | ❌ 否（.gitignore） |
| `.venv/` | 虚拟环境 | ❌ 否（.gitignore） |

---

## 🔍 查找文件指南

### 想要...找到...

- **开始使用** → `README.md`
- **上传文献** → `scripts/upload_auto.py`
- **查看功能** → `docs/功能测试清单.md`
- **设置 Notion** → `docs/免费版用户指南.md`
- **了解去重** → `docs/文章上传和去重指南.md`
- **创建数据库** → `tools/create_notion_databases.py`
- **播放视频** → `video_player/server.py`

---

## 🎨 目录设计原则

1. **`src/`** - 不直接运行的核心模块
2. **`scripts/`** - 用户经常运行的脚本
3. **`tools/`** - 一次性或管理用的工具
4. **`docs/`** - 所有文档集中管理
5. **`video_player/`** - 独立的附加功能

---

## 💡 提示

- 所有 Python 脚本都支持 `--help` 参数查看用法
- 使用 `uv run` 无需手动激活虚拟环境
- 文档都在 `docs/` 目录，按功能分类
