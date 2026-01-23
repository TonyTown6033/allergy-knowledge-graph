# 文章节点关联问题修复指南

## 🔍 问题描述

在生成的知识图谱中，**Article 节点虽然被创建了，但没有任何链接关系**，导致：
- Article 节点在图谱中孤立存在
- 无法看到文章与观点、证据之间的关联
- 图谱的完整性受损

## 🔬 根本原因

当前 Notion 数据库设计中：
- ❌ **Claims 数据库** 没有 Relation 字段关联到 Articles
- ❌ **Evidence 数据库** 没有 Relation 字段关联到 Articles  
- ❌ `export_graph_data.py --mode notion` 没有建立 Article 链接的逻辑

对比本地模式 (`--mode local`):
- ✅ 从 `results.json` 读取数据时，文章和观点的关系是明确的
- ✅ 有 Article → Claim 的 `contains` 链接

## ✅ 解决方案

### 方案 1: 完善 Notion 数据库结构 (推荐)

#### 步骤 1: 在 Claims 数据库中添加 Relation 字段

1. 打开 Notion 中的 **Claims** 数据库
2. 点击右上角 `+` 添加新属性
3. 配置如下：
   - **名称**: `来源文章` 或 `Source Article`
   - **类型**: `Relation` (关联)
   - **关联到**: `Articles` 数据库
   - **关联类型**: 单向关联即可

#### 步骤 2: 在 Evidence 数据库中添加 Relation 字段 (可选)

1. 打开 Notion 中的 **Evidence** 数据库
2. 添加两个 Relation 字段：
   - **关联到文章**: 关联到 `Articles` 数据库
   - **关联到观点**: 关联到 `Claims` 数据库

#### 步骤 3: 更新现有数据

手动或通过脚本为现有的 Claims 和 Evidence 添加关联关系。

#### 步骤 4: 更新导出代码

修改 `scripts/export_graph_data.py` 中的 `generate_notion_graph()` 函数：

```python
# 3. Fetch Claims
print("Fetching Claims...")
claims = fetch_all_pages(db.client, config.NOTION_CLAIMS_DB_ID)
for page in claims:
    page_id = page["id"]
    title = get_property_value(page, "Name")
    content = get_property_value(page, "内容")
    polarity = get_property_value(page, "极性")
    mapped_nodes = get_property_value(page, "关联概念")
    
    # ⭐ 新增：获取关联的文章
    source_articles = get_property_value(page, "来源文章")  # Relation 类型
    
    if page_id not in existing_nodes:
        nodes.append({
            "id": page_id,
            "group": "Claim",
            "name": title,
            "content": content,
            "polarity": polarity,
            "val": 5
        })
        existing_nodes.add(page_id)

    # Link Claim -> Ontology
    if mapped_nodes:
        for node_id in mapped_nodes:
            if node_id in ALLERGY_ONTOLOGY:
                links.append({
                    "source": page_id,
                    "target": node_id,
                    "type": "relates_to"
                })
    
    # ⭐ 新增：建立 Article -> Claim 链接
    if source_articles:
        for article_id in source_articles:
            if article_id in existing_nodes:
                links.append({
                    "source": article_id,
                    "target": page_id,
                    "type": "contains"
                })
```

### 方案 2: 使用来源标题匹配 (临时方案)

如果暂时无法修改 Notion 数据库结构，可以通过"来源标题"字段来建立关联：

```python
# 在 generate_notion_graph() 中，处理完所有数据后

# 建立基于标题的关联
article_titles = {}
for node in nodes:
    if node["group"] == "Article":
        article_titles[node["name"]] = node["id"]

for node in nodes:
    if node["group"] in ["Claim", "Evidence"]:
        # 从 Notion 获取来源标题
        # 如果匹配到某个文章标题，建立链接
        source_title = node.get("source_title")  # 需要在创建节点时保存
        if source_title and source_title in article_titles:
            links.append({
                "source": article_titles[source_title],
                "target": node["id"],
                "type": "contains"
            })
```

### 方案 3: 简化方案 - 全部关联

如果 Claims/Evidence 数量不多，可以简单地将它们全部关联到第一篇文章：

```python
# 在 generate_notion_graph() 最后，如果有文章节点

article_nodes = [n for n in nodes if n["group"] == "Article"]
if article_nodes:
    # 使用第一篇文章作为默认关联
    default_article_id = article_nodes[0]["id"]
    
    for node in nodes:
        if node["group"] in ["Claim", "Evidence"]:
            links.append({
                "source": default_article_id,
                "target": node["id"],
                "type": "contains"
            })
```

## 🧪 验证修复

修复后运行以下命令验证：

```bash
# 重新生成图谱数据
uv run python scripts/export_graph_data.py --mode notion

# 检查生成的数据
uv run python -c "
import json
with open('graph_view/graph_data.json', 'r') as f:
    data = json.load(f)

# 统计 Article 相关的链接
article_ids = {n['id'] for n in data['nodes'] if n.get('group') == 'Article'}
article_links = [l for l in data['links'] if l['source'] in article_ids or l['target'] in article_ids]

print(f'文章节点数: {len(article_ids)}')
print(f'文章相关链接数: {len(article_links)}')

if article_links:
    print('✅ 文章节点已正确关联!')
else:
    print('❌ 文章节点仍然孤立')
"
```

## 📝 推荐实施步骤

1. **立即**: 使用方案 3 快速修复，让文章节点显示出来
2. **短期**: 在 Notion 中添加 Relation 字段（方案 1）
3. **长期**: 完善数据导入流程，自动建立正确的关联关系

## 🔗 相关文档

- `docs/NOTION_SETUP.md` - Notion 数据库设置指南
- `docs/功能测试清单.md` - 功能测试清单
- `scripts/export_graph_data.py` - 图谱数据导出脚本
