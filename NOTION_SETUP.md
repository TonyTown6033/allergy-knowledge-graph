# Notion 数据库设置指南

## 问题说明

由于 Notion API 的限制，无法直接通过 API 为完全空的数据库添加属性。需要先在 Notion Web 界面中手动创建数据库属性。

## 解决方案

### 方案 1：手动在 Notion 中创建数据库属性（推荐）

#### Claims 数据库需要的属性：

1. **标题** - Title (标题类型)
2. **内容** - Rich Text (富文本)
3. **极性** - Select (选择)
   - 选项：支持、反驳、中立
4. **关联概念** - Multi-select (多选)
5. **来源标题** - Rich Text (富文本)
6. **来源链接** - URL (链接)

#### Ontology 数据库需要的属性：

1. **名称** - Title (标题类型)
2. **ID** - Rich Text (富文本)
3. **英文名** - Rich Text (富文本)
4. **类别** - Select (选择)
   - 选项：过敏原、疾病、症状、检查、治疗、生物标志物、其他
5. **别名** - Rich Text (富文本)
6. **描述** - Rich Text (富文本)
7. **父节点** - Rich Text (富文本)

#### Evidence 数据库需要的属性：

1. **标题** - Title (标题类型)
2. **内容** - Rich Text (富文本)
3. **来源标题** - Rich Text (富文本)
4. **来源链接** - URL (链接)
5. **页码** - Number (数字)

### 方案 2：使用 Full Page Database

如果当前使用的是 inline database，可以：

1. 在 Notion 中创建一个新的 **Full Page Database**（完整页面数据库）
2. 手动添加上述属性
3. 获取新数据库的 ID 并更新 `.env` 文件

### 如何在 Notion 中手动创建属性

1. 打开你的 Notion 数据库页面
2. 点击数据库右上角的 `+` 或表格顶部的空白列
3. 选择属性类型（Title, Rich Text, Select 等）
4. 输入属性名称（必须与上面列表中的名称完全一致）
5. 对于 Select 类型，添加相应的选项

## 设置完成后

完成手动设置后，运行以下命令验证：

```bash
# 检查数据库结构
uv run python check_notion_schema.py

# 如果显示属性正常，继续同步
uv run python main.py ontology sync

# 上传提取的观点
uv run python upload_results.py results.json
```

## 获取 Notion 数据库 ID

数据库 ID 可以从数据库 URL 中获取：

```
https://www.notion.so/workspace/DATABASE_ID?v=...
                                ^^^^^^^^^^^
                                这部分就是 ID
```

复制 `DATABASE_ID` 部分（32位字符）到 `.env` 文件中。
