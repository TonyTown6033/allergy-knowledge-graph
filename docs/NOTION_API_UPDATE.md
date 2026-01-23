# Notion API 更新说明

## 🔄 API 变更 (2025+)

### 问题描述

在服务器上运行 `uv run python scripts/export_graph_data.py --mode notion` 时出现以下错误:

```
AttributeError: 'DatabasesEndpoint' object has no attribute 'query'
```

### 根本原因

**Notion API 在 2025 年进行了重大更新**,将数据库查询功能从 `databases.query()` 迁移到了 `data_sources.query()`。

### 变更详情

#### 旧版 API (已废弃)
```python
# ❌ 不再工作
response = client.databases.query(
    database_id=database_id,
    start_cursor=start_cursor
)
```

#### 新版 API (2025-09-03)
```python
# ✅ 正确方式 - 需要两步
# Step 1: 从 database 获取 data_source_id
db_info = client.databases.retrieve(database_id=database_id)
data_sources = db_info.get("data_sources", [])
data_source_id = data_sources[0]["id"]  # 通常一个数据库只有一个 data source

# Step 2: 使用 data_source_id 查询
response = client.data_sources.query(
    data_source_id=data_source_id,
    start_cursor=start_cursor
)
```

#### 关键变化
- `databases.query()` 方法已被完全移除
- 一个 database 可以包含多个 data sources（多源数据库）
- **database_id ≠ data_source_id** - 必须先获取 data_source_id
- `data_sources` 是一个数组，包含所有 data source 的信息

### 修复的文件

1. **`scripts/export_graph_data.py`**
   - 修改 `fetch_all_pages()` 函数
   - 添加 database → data_source 的转换逻辑
   - 使用 `client.data_sources.query()` 查询页面

2. **`src/notion_client.py`**
   - 修改 `query_article_by_md5()` 方法
   - 修改 `query_claims()` 方法
   - 所有查询方法都先获取 data_source_id，再查询

3. **`scripts/test_notion_export.py`**
   - 更新所有测试用例使用正确的两步查询流程
   - 验证 database → data_source 转换

### 测试验证

创建了专门的测试脚本 `scripts/test_notion_export.py` 用于验证:

```bash
# 运行测试
uv run python scripts/test_notion_export.py
```

测试覆盖:
- ✅ Notion 客户端连接
- ✅ `data_sources.query` 方法存在性检查
- ✅ Articles、Claims、Evidence 数据库查询
- ✅ 分页功能测试
- ✅ 模块导入完整性

### 兼容性说明

- **Python**: 3.11+
- **notion-client**: 2.0.0+ (建议 2.2.1+)
- **Notion API Version**: 2025-09-03

### 服务器部署注意事项

如果在服务器上仍然遇到此错误,请执行以下步骤:

```bash
# 1. 更新 notion-client 到最新版
uv pip install --upgrade notion-client

# 2. 验证版本
uv pip show notion-client

# 3. 运行测试
uv run python scripts/test_notion_export.py

# 4. 如果测试通过,运行导出
uv run python scripts/export_graph_data.py --mode notion
```

### 完整示例

```python
from notion_client import Client
from src.config import config

client = Client(auth=config.NOTION_TOKEN)

# 方法 1: 完整的两步流程
def fetch_pages(database_id):
    # 获取 data_source_id
    db_info = client.databases.retrieve(database_id=database_id)
    data_sources = db_info.get("data_sources", [])
    
    if not data_sources:
        raise ValueError(f"Database {database_id} has no data sources")
    
    data_source_id = data_sources[0]["id"]
    
    # 查询页面
    response = client.data_sources.query(
        data_source_id=data_source_id,
        page_size=100
    )
    
    return response.get("results", [])

# 方法 2: 带分页的完整实现
def fetch_all_pages(database_id):
    db_info = client.databases.retrieve(database_id=database_id)
    data_source_id = db_info.get("data_sources", [{}])[0].get("id")
    
    all_results = []
    has_more = True
    start_cursor = None
    
    while has_more:
        response = client.data_sources.query(
            data_source_id=data_source_id,
            start_cursor=start_cursor
        )
        all_results.extend(response.get("results", []))
        has_more = response.get("has_more", False)
        start_cursor = response.get("next_cursor")
    
    return all_results
```

### 参考资料

- [Notion API Reference - Query a data source](https://developers.notion.com/reference/query-a-data-source)
- [Notion API Changelog - 2025-09-03](https://developers.notion.com/reference/changes-by-version)
- [Upgrading to Version 2025-09-03](https://developers.notion.com/docs/upgrade-guide-2025-09-03)
- [FAQs: Version 2025-09-03](https://developers.notion.com/docs/upgrade-faqs-2025-09-03)

### 时间线

- **2025-09-03**: Notion API 引入 `data_sources.query`
- **2026-01-23**: 发现并修复此问题

---

## 📝 相关命令

```bash
# 本地模式(不需要 Notion 连接)
uv run python scripts/export_graph_data.py --mode local

# Notion 模式(从 Notion 拉取数据)
uv run python scripts/export_graph_data.py --mode notion

# 测试 Notion 连接和 API
uv run python scripts/test_notion_export.py
```
