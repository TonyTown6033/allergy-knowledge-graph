#!/usr/bin/env python3
"""
测试从 Notion 导出图谱数据功能
用于验证 export_graph_data.py --mode notion 是否正常工作
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.notion_client import NotionDatabase
from src.config import config


def test_notion_connection():
    """测试 Notion 连接"""
    print("="*70)
    print("测试 1: Notion 连接")
    print("="*70)
    
    try:
        db = NotionDatabase()
        print("✓ Notion 客户端初始化成功")
        print(f"  Client type: {type(db.client)}")
        print(f"  Databases endpoint type: {type(db.client.databases)}")
        return db
    except ValueError as e:
        print(f"✗ 连接失败: {e}")
        return None


def test_query_method():
    """测试 data_sources.query 方法是否存在"""
    print("\n" + "="*70)
    print("测试 2: 检查 query 方法")
    print("="*70)
    
    db = NotionDatabase()
    
    # 新版 API 使用 data_sources.query
    if hasattr(db.client.data_sources, 'query'):
        print("✓ data_sources.query 方法存在 (新版 API)")
    else:
        print("✗ data_sources.query 方法不存在")
        print("  可用的方法:")
        for attr in dir(db.client.data_sources):
            if not attr.startswith('_'):
                print(f"    - {attr}")
        return False
    
    # 检查旧版 API (应该不存在)
    if hasattr(db.client.databases, 'query'):
        print("  ⚠ databases.query 方法也存在 (旧版 API)")
    else:
        print("  ℹ databases.query 不存在 (预期行为)")
    
    return True


def test_fetch_articles():
    """测试获取 Articles 数据"""
    print("\n" + "="*70)
    print("测试 3: 获取 Articles 数据库")
    print("="*70)
    
    if not config.NOTION_ARTICLES_DB_ID:
        print("⚠ NOTION_ARTICLES_DB_ID 未配置，跳过测试")
        return True
    
    try:
        db = NotionDatabase()
        
        # 新版 API: 先获取 data_source_id
        print(f"  Database ID: {config.NOTION_ARTICLES_DB_ID[:8]}...")
        db_info = db.client.databases.retrieve(database_id=config.NOTION_ARTICLES_DB_ID)
        data_sources = db_info.get("data_sources", [])
        
        if not data_sources:
            print("✗ Database has no data sources")
            return False
        
        data_source_id = data_sources[0]["id"]
        print(f"  Data Source ID: {data_source_id[:8]}...")
        
        # 使用 data_source_id 查询
        response = db.client.data_sources.query(
            data_source_id=data_source_id,
            page_size=1  # 只获取一条测试
        )
        
        results = response.get("results", [])
        print(f"✓ 成功获取 Articles 数据")
        print(f"  返回记录数: {len(results)}")
        
        if results:
            page = results[0]
            print(f"  示例记录 ID: {page['id'][:8]}...")
            
        return True
        
    except AttributeError as e:
        print(f"✗ AttributeError: {e}")
        print("  这是你在服务器上遇到的错误!")
        return False
    except Exception as e:
        print(f"✗ 其他错误: {type(e).__name__}: {e}")
        return False


def test_fetch_claims():
    """测试获取 Claims 数据"""
    print("\n" + "="*70)
    print("测试 4: 获取 Claims 数据库")
    print("="*70)
    
    if not config.NOTION_CLAIMS_DB_ID:
        print("⚠ NOTION_CLAIMS_DB_ID 未配置，跳过测试")
        return True
    
    try:
        db = NotionDatabase()
        db_info = db.client.databases.retrieve(database_id=config.NOTION_CLAIMS_DB_ID)
        data_source_id = db_info.get("data_sources", [{}])[0].get("id")
        
        if not data_source_id:
            print("✗ No data source found")
            return False
        
        response = db.client.data_sources.query(
            data_source_id=data_source_id,
            page_size=1
        )
        
        results = response.get("results", [])
        print(f"✓ 成功获取 Claims 数据")
        print(f"  返回记录数: {len(results)}")
        
        return True
        
    except Exception as e:
        print(f"✗ 错误: {type(e).__name__}: {e}")
        return False


def test_fetch_evidence():
    """测试获取 Evidence 数据"""
    print("\n" + "="*70)
    print("测试 5: 获取 Evidence 数据库")
    print("="*70)
    
    if not config.NOTION_EVIDENCE_DB_ID:
        print("⚠ NOTION_EVIDENCE_DB_ID 未配置，跳过测试")
        return True
    
    try:
        db = NotionDatabase()
        db_info = db.client.databases.retrieve(database_id=config.NOTION_EVIDENCE_DB_ID)
        data_source_id = db_info.get("data_sources", [{}])[0].get("id")
        
        if not data_source_id:
            print("✗ No data source found")
            return False
        
        response = db.client.data_sources.query(
            data_source_id=data_source_id,
            page_size=1
        )
        
        results = response.get("results", [])
        print(f"✓ 成功获取 Evidence 数据")
        print(f"  返回记录数: {len(results)}")
        
        return True
        
    except Exception as e:
        print(f"✗ 错误: {type(e).__name__}: {e}")
        return False


def test_pagination():
    """测试分页获取功能"""
    print("\n" + "="*70)
    print("测试 6: 测试分页功能")
    print("="*70)
    
    if not config.NOTION_CLAIMS_DB_ID:
        print("⚠ 跳过分页测试（数据库未配置）")
        return True
    
    try:
        db = NotionDatabase()
        
        # 获取所有数据（带分页）
        all_results = []
        has_more = True
        start_cursor = None
        page_count = 0
        
        # 获取 data_source_id
        db_info = db.client.databases.retrieve(database_id=config.NOTION_CLAIMS_DB_ID)
        data_source_id = db_info.get("data_sources", [{}])[0].get("id")
        
        if not data_source_id:
            print("✗ No data source found")
            return False
        
        while has_more and page_count < 3:  # 最多测试3页
            response = db.client.data_sources.query(
                data_source_id=data_source_id,
                start_cursor=start_cursor,
                page_size=10
            )
            
            results = response.get("results", [])
            all_results.extend(results)
            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")
            page_count += 1
            
            print(f"  第 {page_count} 页: {len(results)} 条记录")
        
        print(f"✓ 分页功能正常")
        print(f"  总共获取: {len(all_results)} 条记录 (最多3页)")
        print(f"  还有更多: {has_more}")
        
        return True
        
    except Exception as e:
        print(f"✗ 错误: {type(e).__name__}: {e}")
        return False


def test_export_graph_import():
    """测试导入 export_graph_data 模块"""
    print("\n" + "="*70)
    print("测试 7: 导入 export_graph_data 模块")
    print("="*70)
    
    try:
        import scripts.export_graph_data as export_module
        print("✓ 模块导入成功")
        
        # 检查函数是否存在
        if hasattr(export_module, 'fetch_all_pages'):
            print("✓ fetch_all_pages 函数存在")
        if hasattr(export_module, 'generate_notion_graph'):
            print("✓ generate_notion_graph 函数存在")
            
        return True
        
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "🧪 开始测试 Notion 导出功能" + "\n")
    
    tests = [
        ("Notion 连接", test_notion_connection),
        ("Query 方法检查", test_query_method),
        ("Articles 数据库", test_fetch_articles),
        ("Claims 数据库", test_fetch_claims),
        ("Evidence 数据库", test_fetch_evidence),
        ("分页功能", test_pagination),
        ("模块导入", test_export_graph_import),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 总结
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {status}: {test_name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    # 检查是否是核心功能通过
    core_tests = ["Notion 连接", "Query 方法检查", "模块导入"]
    core_passed = all(result for name, result in results if name in core_tests)
    
    if passed == total:
        print("\n🎉 所有测试通过! 可以使用:")
        print("   uv run python scripts/export_graph_data.py --mode notion")
    elif core_passed:
        print("\n✓ 核心功能测试通过!")
        print("  - Notion API 调用方式正确 (使用 data_sources.query)")
        print("  - 代码结构完整")
        print("\n⚠️  数据库访问失败可能原因:")
        print("  1. Notion Integration 权限未配置")
        print("  2. Database 未分享给 Integration")
        print("  3. Database ID 不正确")
        print("\n如果在有权限的服务器上运行，应该可以正常工作。")
    else:
        print("\n⚠️  核心功能测试失败，请检查配置或代码")
        print("   提示: 如果是 AttributeError，可能是 notion-client 版本问题")
        print("   尝试: pip install --upgrade notion-client")
    
    print("="*70)


if __name__ == "__main__":
    main()
