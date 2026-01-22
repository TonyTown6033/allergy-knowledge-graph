"""
文章处理和观点提取模块
使用 AI 从文章中提取结构化的观点和证据
"""

import json
from typing import Optional
from pathlib import Path

from openai import OpenAI
import pdfplumber

from .config import config
from .ontology import find_nodes_in_text, ALLERGY_ONTOLOGY
from .notion_client import Claim, Evidence, Polarity


# 观点提取的系统提示词
CLAIM_EXTRACTION_PROMPT = """你是一位专业的医学文献分析专家，专注于过敏性疾病领域。
请从给定的文章内容中提取核心观点（Claims）。

对于每个观点，请提供：
1. **观点标题**：简洁的一句话总结
2. **观点内容**：2-3句话的详细描述
3. **极性**：该观点是"支持"、"反驳"还是"中立"
4. **关联概念**：与该观点相关的医学概念（如 IgE、过敏性鼻炎、尘螨等）
5. **支持证据**：文章中支持该观点的原文引用

请以 JSON 格式输出，格式如下：
{
    "claims": [
        {
            "title": "观点标题",
            "content": "观点详细内容",
            "polarity": "支持/反驳/中立",
            "concepts": ["概念1", "概念2"],
            "evidence": "支持该观点的原文引用"
        }
    ]
}

注意：
- 确保提取的观点是文章的核心论点，而非细节描述
- 关联概念应尽可能准确，使用标准医学术语
- 证据必须是文章原文，不要编造或改写
"""


class ArticleExtractor:
    """文章内容提取和处理器"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        初始化提取器
        
        Args:
            api_key: OpenAI API key
            model: 使用的模型名称
        """
        self.api_key = api_key or config.OPENAI_API_KEY
        self.model = model or config.OPENAI_MODEL
        
        if not self.api_key:
            raise ValueError("OpenAI API key 未配置，请在 .env 文件中设置 OPENAI_API_KEY")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=config.OPENAI_BASE_URL if config.OPENAI_BASE_URL else None
        )
    
    def extract_text_from_pdf(self, pdf_path: str | Path) -> str:
        """
        从 PDF 文件提取文本
        
        Args:
            pdf_path: PDF 文件路径
            
        Returns:
            提取的文本内容
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")
        
        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        
        return "\n\n".join(text_parts)
    
    def extract_claims(
        self, 
        text: str, 
        source_title: Optional[str] = None,
        source_url: Optional[str] = None
    ) -> list[Claim]:
        """
        从文本中提取观点
        
        Args:
            text: 文章文本
            source_title: 来源标题
            source_url: 来源URL
            
        Returns:
            提取的观点列表
        """
        # 截断过长的文本
        max_tokens = 8000
        if len(text) > max_tokens * 2:
            text = text[:max_tokens * 2]
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": CLAIM_EXTRACTION_PROMPT},
                {"role": "user", "content": f"请分析以下文章内容：\n\n{text}"}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        claims = []
        for item in result.get("claims", []):
            # 将概念映射到本体节点
            concepts = item.get("concepts", [])
            mapped_nodes = self._map_concepts_to_ontology(concepts)
            
            # 解析极性
            polarity_str = item.get("polarity", "中立")
            if "支持" in polarity_str:
                polarity = Polarity.SUPPORT
            elif "反驳" in polarity_str:
                polarity = Polarity.REFUTE
            else:
                polarity = Polarity.NEUTRAL
            
            claim = Claim(
                title=item.get("title", ""),
                content=item.get("content", ""),
                polarity=polarity,
                mapped_nodes=mapped_nodes,
                evidence_ids=[],  # 稍后关联
                source_title=source_title,
                source_url=source_url
            )
            claims.append(claim)
        
        return claims
    
    def _map_concepts_to_ontology(self, concepts: list[str]) -> list[str]:
        """
        将提取的概念映射到本体节点
        
        Args:
            concepts: 概念列表
            
        Returns:
            映射后的节点ID列表
        """
        mapped_ids = set()
        
        for concept in concepts:
            # 首先尝试直接文本匹配
            nodes = find_nodes_in_text(concept)
            for node in nodes:
                mapped_ids.add(node.id)
        
        # 如果没有找到精确匹配，尝试模糊匹配
        if not mapped_ids:
            for concept in concepts:
                concept_lower = concept.lower()
                for node_id, node in ALLERGY_ONTOLOGY.items():
                    if any(alias.lower() in concept_lower or concept_lower in alias.lower() 
                           for alias in node.aliases):
                        mapped_ids.add(node_id)
        
        return list(mapped_ids)
    
    def extract_claims_with_evidence(
        self, 
        text: str, 
        source_title: Optional[str] = None,
        source_url: Optional[str] = None
    ) -> tuple[list[Claim], list[Evidence]]:
        """
        从文本中提取观点和证据
        
        Args:
            text: 文章文本
            source_title: 来源标题
            source_url: 来源URL
            
        Returns:
            (观点列表, 证据列表)
        """
        # 截断过长的文本
        max_tokens = 8000
        if len(text) > max_tokens * 2:
            text = text[:max_tokens * 2]
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": CLAIM_EXTRACTION_PROMPT},
                {"role": "user", "content": f"请分析以下文章内容：\n\n{text}"}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        claims = []
        evidences = []
        
        for item in result.get("claims", []):
            # 将概念映射到本体节点
            concepts = item.get("concepts", [])
            mapped_nodes = self._map_concepts_to_ontology(concepts)
            
            # 解析极性
            polarity_str = item.get("polarity", "中立")
            if "支持" in polarity_str:
                polarity = Polarity.SUPPORT
            elif "反驳" in polarity_str:
                polarity = Polarity.REFUTE
            else:
                polarity = Polarity.NEUTRAL
            
            # 创建 Evidence 对象（如果有）
            evidence_text = item.get("evidence", "")
            if evidence_text:
                evidence = Evidence(
                    title=item.get('title', '')[:80],  # 直接使用观点标题，不加"证据："前缀
                    content=evidence_text,
                    source_title=source_title,
                    source_url=source_url,
                    page_number=None  # 可以后续添加页码识别
                )
                evidences.append(evidence)
            
            claim = Claim(
                title=item.get("title", ""),
                content=item.get("content", ""),
                polarity=polarity,
                mapped_nodes=mapped_nodes,
                evidence_ids=[],  # 将在上传后填充
                source_title=source_title,
                source_url=source_url
            )
            claims.append(claim)
        
        return claims, evidences
    
    def process_pdf(
        self, 
        pdf_path: str | Path,
        source_url: Optional[str] = None
    ) -> list[Claim]:
        """
        处理 PDF 文件，提取观点
        
        Args:
            pdf_path: PDF 文件路径
            source_url: 来源URL
            
        Returns:
            提取的观点列表
        """
        pdf_path = Path(pdf_path)
        
        # 提取文本
        text = self.extract_text_from_pdf(pdf_path)
        
        # 提取观点
        claims = self.extract_claims(
            text=text,
            source_title=pdf_path.stem,
            source_url=source_url
        )
        
        return claims
    
    def process_pdf_with_evidence(
        self, 
        pdf_path: str | Path,
        source_url: Optional[str] = None
    ) -> tuple[list[Claim], list[Evidence]]:
        """
        处理 PDF 文件，提取观点和证据
        
        Args:
            pdf_path: PDF 文件路径
            source_url: 来源URL
            
        Returns:
            (观点列表, 证据列表)
        """
        pdf_path = Path(pdf_path)
        
        # 提取文本
        text = self.extract_text_from_pdf(pdf_path)
        
        # 提取观点和证据
        claims, evidences = self.extract_claims_with_evidence(
            text=text,
            source_title=pdf_path.stem,
            source_url=source_url
        )
        
        return claims, evidences


def batch_process_pdfs(
    pdf_dir: str | Path,
    output_file: Optional[str | Path] = None
) -> list[dict]:
    """
    批量处理目录下的所有 PDF 文件
    
    Args:
        pdf_dir: PDF 文件目录
        output_file: 输出 JSON 文件路径（可选）
        
    Returns:
        所有提取结果的列表
    """
    pdf_dir = Path(pdf_dir)
    extractor = ArticleExtractor()
    
    results = []
    
    for pdf_path in pdf_dir.glob("**/*.pdf"):
        print(f"处理: {pdf_path.name}")
        try:
            claims = extractor.process_pdf(pdf_path)
            
            result = {
                "file": str(pdf_path),
                "title": pdf_path.stem,
                "claims": [
                    {
                        "title": c.title,
                        "content": c.content,
                        "polarity": c.polarity.value,
                        "mapped_nodes": c.mapped_nodes
                    }
                    for c in claims
                ]
            }
            results.append(result)
            print(f"  提取了 {len(claims)} 个观点")
            
        except Exception as e:
            print(f"  处理失败: {e}")
            results.append({
                "file": str(pdf_path),
                "error": str(e)
            })
    
    # 保存结果
    if output_file:
        output_path = Path(output_file)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {output_path}")
    
    return results
