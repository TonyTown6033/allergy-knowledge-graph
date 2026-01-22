#!/usr/bin/env python3
"""
演示完整的 Evidence 工作流程
从样本文本中提取观点和证据，展示关联关系
"""

from src.extractor import ArticleExtractor
from src.notion_client import NotionDatabase


# 样本医学文本
SAMPLE_TEXT = """
过敏性鼻炎的诊断与治疗研究

摘要：
过敏性鼻炎（Allergic Rhinitis, AR）是最常见的过敏性疾病之一。本研究通过对500例AR患者的临床分析，探讨其诊断和治疗策略。

研究发现：
1. 血清特异性IgE检测在AR诊断中具有重要价值。在本研究的500例患者中，IgE阳性率达到85.2%。其中，对尘螨过敏的患者占比最高，达到62.4%（312/500）。这一发现与既往研究一致，证实了尘螨是中国人群中最主要的吸入性过敏原。

2. 症状评分与IgE水平显著相关。我们使用TNSS（总鼻症状评分）评估患者症状严重程度，发现IgE>200 IU/mL的患者TNSS评分平均为8.7±2.1分，显著高于IgE<100 IU/mL患者的5.2±1.8分（p<0.001）。

3. 抗组胺药物治疗效果显著。给予西替利嗪10mg/日治疗4周后，患者TNSS评分从治疗前的7.8±2.3分下降至3.1±1.5分，症状改善率达到60.3%。

4. 免疫治疗在中重度患者中疗效更佳。对187例中重度AR患者实施尘螨变应原免疫治疗，持续治疗1年后，症状评分下降55%，生活质量评分提高42%。

结论：
过敏性鼻炎的诊断需要结合临床症状和实验室检查。IgE检测和皮肤点刺试验是重要的诊断工具。治疗上应根据病情严重程度选择合适的方案，免疫治疗对中重度患者具有良好的长期疗效。
"""


def demo_extraction():
    """演示提取过程"""
    print("="*70)
    print("演示：完整的观点和证据提取流程")
    print("="*70)
    
    print("\n[步骤 1] 初始化提取器...")
    extractor = ArticleExtractor()
    print("  ✓ 初始化完成")
    
    print("\n[步骤 2] 从文本中提取观点和证据...")
    print("-"*70)
    print("样本文本（前200字）:")
    print(SAMPLE_TEXT[:200] + "...")
    print("-"*70)
    
    try:
        claims, evidences = extractor.extract_claims_with_evidence(
            text=SAMPLE_TEXT,
            source_title="过敏性鼻炎的诊断与治疗研究（示例）",
            source_url="https://example.com/ar-study"
        )
        
        print(f"\n  ✓ 提取完成")
        print(f"    观点数: {len(claims)}")
        print(f"    证据数: {len(evidences)}")
        
    except Exception as e:
        print(f"\n  ✗ 提取失败: {str(e)}")
        print("\n⚠ 注意: 需要有效的 OpenAI API key 才能运行此演示")
        return
    
    # 显示提取结果
    print("\n[步骤 3] 提取结果预览...")
    print("="*70)
    
    for i, claim in enumerate(claims, 1):
        print(f"\n观点 {i}: {claim.title}")
        print(f"  内容: {claim.content[:100]}...")
        print(f"  极性: {claim.polarity.value}")
        print(f"  关联概念: {', '.join(claim.mapped_nodes[:3])}")
    
    for i, evidence in enumerate(evidences, 1):
        print(f"\n证据 {i}: {evidence.title}")
        print(f"  内容: {evidence.content[:100]}...")
        print(f"  来源: {evidence.source_title}")
    
    # 询问是否上传
    print("\n" + "="*70)
    print("提取完成！")
    print("="*70)
    
    response = input("\n是否上传到 Notion？(y/n): ").strip().lower()
    
    if response == 'y':
        print("\n[步骤 4] 上传到 Notion...")
        upload_to_notion(claims, evidences)
    else:
        print("\n跳过上传。演示结束。")


def upload_to_notion(claims, evidences):
    """上传到 Notion"""
    notion = NotionDatabase()
    
    # 上传证据
    print("\n上传证据...")
    evidence_pages = []
    for i, evidence in enumerate(evidences, 1):
        try:
            page = notion.add_evidence(evidence)
            evidence_pages.append(page)
            print(f"  ✓ ({i}/{len(evidences)}) {evidence.title[:40]}...")
        except Exception as e:
            print(f"  ✗ ({i}/{len(evidences)}) 失败: {str(e)[:60]}")
            evidence_pages.append(None)
    
    # 上传观点并关联证据
    print("\n上传观点...")
    for i, (claim, evidence_page) in enumerate(zip(claims, evidence_pages), 1):
        try:
            if evidence_page:
                claim.evidence_ids = [evidence_page["id"]]
            
            notion.add_claim(claim)
            print(f"  ✓ ({i}/{len(claims)}) {claim.title[:40]}...")
            if evidence_page:
                print(f"       → 已关联证据")
        except Exception as e:
            print(f"  ✗ ({i}/{len(claims)}) 失败: {str(e)[:60]}")
    
    print("\n✓ 上传完成！请在 Notion 中查看结果。")


if __name__ == "__main__":
    try:
        demo_extraction()
    except KeyboardInterrupt:
        print("\n\n演示已取消")
    except Exception as e:
        print(f"\n✗ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
