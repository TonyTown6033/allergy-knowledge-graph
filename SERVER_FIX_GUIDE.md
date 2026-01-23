# 服务器端修复指南

## 🐛 问题描述

在服务器上运行以下命令时出错:

```bash
uv run python scripts/export_graph_data.py --mode notion
```

错误信息:
```
AttributeError: 'DatabasesEndpoint' object has no attribute 'query'
```

## ✅ 解决方案

### 方案一: 拉取最新代码 (推荐)

已经修复了代码,直接拉取最新版本:

```bash
# 在服务器上
cd ~/github/allergy-knowledge-graph  # 你的项目路径

# 拉取最新代码
git pull origin main

# 或者如果使用其他分支
git pull origin <你的分支名>
```

### 方案二: 手动更新文件

如果无法拉取代码,可以手动更新以下文件:

#### 1. 更新 `scripts/export_graph_data.py`

找到第 111 行的 `fetch_all_pages` 函数,修改:

```python
# 修改前 (❌ 错误)
response = client.databases.query(
    database_id=database_id,
    start_cursor=start_cursor
)

# 修改后 (✅ 正确)
response = client.data_sources.query(
    data_source_id=database_id,  # 参数名也要改
    start_cursor=start_cursor
)
```

#### 2. 更新 `src/notion_client.py`

找到所有 `client.databases.query` 的地方 (第 321 行和第 405 行),全部替换为:

```python
# 修改前 (❌ 错误)
self.client.databases.query(database_id=db_id)

# 修改后 (✅ 正确)
self.client.data_sources.query(data_source_id=db_id)
```

具体位置:
- **第 321 行**: `query_article_by_md5()` 方法
- **第 405 行**: `query_claims()` 方法

### 方案三: 使用补丁文件

如果你熟悉 `patch` 命令,可以创建补丁文件:

```bash
# 在本地创建补丁
git diff HEAD~1 > notion_api_fix.patch

# 上传到服务器并应用
scp notion_api_fix.patch user@server:/path/to/project/
ssh user@server
cd /path/to/project
git apply notion_api_fix.patch
```

## 🧪 验证修复

运行测试脚本验证修复是否成功:

```bash
# 1. 运行 Notion 导出测试
uv run python scripts/test_notion_export.py
```

期望输出:
```
✓ Notion 连接
✓ Query 方法检查  # 这个必须通过!
✓ 模块导入

✓ 核心功能测试通过!
  - Notion API 调用方式正确 (使用 data_sources.query)
  - 代码结构完整
```

如果看到上述输出,说明修复成功。

```bash
# 2. 测试本地模式 (不需要 Notion 连接)
uv run python scripts/export_graph_data.py --mode local
```

期望输出:
```
Graph data generated at graph_view/graph_data.json
Nodes: XXX, Links: XXX
```

```bash
# 3. 测试 Notion 模式 (需要正确的权限配置)
uv run python scripts/export_graph_data.py --mode notion
```

期望输出:
```
Connecting to Notion...
Processing Ontology...
Fetching Articles...
Fetching Claims...
Fetching Evidence...
Graph data generated at graph_view/graph_data.json
Nodes: XXX, Links: XXX
```

## 🔍 常见问题

### Q1: 仍然出现 AttributeError

**原因**: notion-client 库版本过旧

**解决**:
```bash
uv pip install --upgrade notion-client
uv pip show notion-client  # 确认版本 >= 2.0.0
```

### Q2: 出现 "Could not find database" 错误

**原因**: Notion Integration 权限未配置

**解决**:
1. 打开 Notion 工作区
2. 找到对应的 Database 页面
3. 点击右上角 "..." → "Connections"
4. 添加你的 Integration

### Q3: 如何获取测试脚本

测试脚本已包含在最新代码中:
- `scripts/test_notion_export.py` - Notion 导出测试

如果没有,可以从仓库下载:
```bash
# 只下载测试脚本
wget https://raw.githubusercontent.com/TonyTown6033/allergy-knowledge-graph/main/scripts/test_notion_export.py \
  -O scripts/test_notion_export.py
```

## 📚 更多信息

- **详细技术说明**: 查看 `docs/NOTION_API_UPDATE.md`
- **功能测试清单**: 查看 `docs/功能测试清单.md`
- **部署指南**: 查看 `docs/DEPLOYMENT.md`

## 📞 支持

如果按照上述步骤仍然有问题,请提供:
1. 错误的完整堆栈信息
2. `uv pip show notion-client` 的输出
3. Python 版本: `python --version`

---

**更新日期**: 2026-01-23  
**修复版本**: v1.1.0  
**影响范围**: Notion 数据导出功能
