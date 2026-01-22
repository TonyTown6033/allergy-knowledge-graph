#!/usr/bin/env python3
"""
测试 Evidence 数据库功能
创建一些示例证据并上传到 Notion
"""

from src.notion_client import NotionDatabase, Evidence


def test_add_evidence():
    """测试添加证据到 Notion"""
    print("="*70)
    print("测试 Evidence 数据库")
    print("="*70)
    
    # 创建示例证据
    test_evidences = [
        Evidence(
            title="IgE水平与过敏严重程度的临床研究数据",
            content="研究表明，血清总IgE水平与过敏性疾病的严重程度呈正相关。在180例过敏性鼻炎患者中，重度患者的IgE中位数为256 IU/mL，显著高于轻度患者的89 IU/mL (p<0.001)。",
            source_title="中国变应性鼻炎诊断和治疗指南（2022年，修订版）",
            page_number=15
        ),
        Evidence(
            title="尘螨是中国最常见的吸入性过敏原",
            content="在中国不同地区的流行病学调查显示，户尘螨和粉尘螨是最主要的吸入性过敏原，阳性率可达60-80%。南方地区的尘螨过敏阳性率高于北方地区。",
            source_title="过敏原特异性IgE检测结果临床解读中国专家共识2022",
            source_url="https://example.com/consensus",
            page_number=8
        ),
        Evidence(
            title="食物过敏患儿的年龄分布",
            content="在0-2岁婴幼儿中，牛奶和鸡蛋是最常见的食物过敏原，占比分别为65%和55%。随着年龄增长，花生、坚果类过敏比例逐渐上升。",
            source_title="中国儿童食物过敏循证指南2022年",
            page_number=22
        ),
        Evidence(
            title="免疫治疗的疗效评估",
            content="一项包含1247例患者的多中心研究显示，标准化尘螨变应原免疫治疗3年后，症状评分较基线下降67%，药物使用减少72%，生活质量显著改善。",
            source_title="中国变应性鼻炎免疫治疗专家共识",
            page_number=34
        ),
        Evidence(
            title="特应性皮炎的患病率趋势",
            content="2020年全国流行病学调查显示，中国1-7岁儿童特应性皮炎患病率为12.94%，较2002年的3.07%显著上升。城市地区患病率(15.24%)高于农村地区(8.79%)。",
            source_title="中国特应性皮炎诊疗指南（2020版）",
            page_number=5
        ),
    ]
    
    # 初始化 Notion 客户端
    notion = NotionDatabase()
    
    print(f"\n准备上传 {len(test_evidences)} 条证据...\n")
    
    success_count = 0
    failed_count = 0
    
    for i, evidence in enumerate(test_evidences, 1):
        try:
            notion.add_evidence(evidence)
            print(f"✓ ({i}/{len(test_evidences)}) {evidence.title}")
            success_count += 1
        except Exception as e:
            print(f"✗ ({i}/{len(test_evidences)}) {evidence.title}")
            print(f"   错误: {str(e)}")
            failed_count += 1
    
    print("\n" + "="*70)
    print(f"上传完成")
    print(f"  成功: {success_count}")
    print(f"  失败: {failed_count}")
    print("="*70)
    
    if success_count > 0:
        print("\n✓ 请在 Notion 中查看 Evidence 数据库")
        print("  应该能看到新添加的证据条目")


if __name__ == "__main__":
    test_add_evidence()
