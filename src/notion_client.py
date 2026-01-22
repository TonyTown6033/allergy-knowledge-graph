"""
Notion API 交互模块
处理与 Notion 数据库的所有交互
"""

from typing import Optional
from dataclasses import dataclass
from enum import Enum

from notion_client import Client

from .config import config


class Polarity(str, Enum):
    """观点极性"""
    SUPPORT = "支持"
    REFUTE = "反驳"
    NEUTRAL = "中立"


@dataclass
class Claim:
    """观点数据结构"""
    title: str                          # 观点标题/摘要
    content: str                        # 观点详细内容
    polarity: Polarity                  # 极性：支持/反驳/中立
    mapped_nodes: list[str]             # 关联的本体节点ID
    evidence_ids: list[str]             # 关联的证据ID
    source_url: Optional[str] = None    # 来源URL
    source_title: Optional[str] = None  # 来源标题


@dataclass
class Evidence:
    """证据数据结构"""
    title: str                          # 证据标题
    content: str                        # 证据内容（原文引用）
    source_url: Optional[str] = None    # 来源URL
    source_title: Optional[str] = None  # 来源标题
    page_number: Optional[int] = None   # 页码（如果是PDF）


class NotionDatabase:
    """Notion 数据库操作类"""
    
    def __init__(self, token: Optional[str] = None):
        """
        初始化 Notion 客户端
        
        Args:
            token: Notion API token，如果不提供则从配置读取
        """
        self.token = token or config.NOTION_TOKEN
        if not self.token:
            raise ValueError("Notion token 未配置，请在 .env 文件中设置 NOTION_TOKEN")
        
        self.client = Client(auth=self.token)
    
    def _get_database(self, database_id: str) -> dict:
        """获取数据库信息"""
        return self.client.databases.retrieve(database_id=database_id)
    
    def add_claim(self, claim: Claim, database_id: Optional[str] = None) -> dict:
        """
        添加观点到 Notion 数据库
        
        Args:
            claim: 观点数据
            database_id: 数据库ID，如果不提供则从配置读取
            
        Returns:
            创建的页面信息
        """
        db_id = database_id or config.NOTION_CLAIMS_DB_ID
        if not db_id:
            raise ValueError("Claims 数据库ID未配置")
        
        # 使用完整的列结构
        properties = {
            "Name": {
                "title": [{"text": {"content": claim.title}}]
            },
            "内容": {
                "rich_text": [{"text": {"content": claim.content[:2000]}}]  # Notion 限制
            },
            "极性": {
                "select": {"name": claim.polarity.value}
            },
            "关联概念": {
                "multi_select": [{"name": node_id} for node_id in claim.mapped_nodes[:10]]
            },
        }
        
        # 可选属性
        if claim.source_url:
            properties["来源链接"] = {"url": claim.source_url}
        if claim.source_title:
            properties["来源标题"] = {
                "rich_text": [{"text": {"content": claim.source_title}}]
            }
        
        return self.client.pages.create(
            parent={"database_id": db_id},
            properties=properties
        )
    
    def add_evidence(self, evidence: Evidence, database_id: Optional[str] = None) -> dict:
        """
        添加证据到 Notion 数据库
        
        Args:
            evidence: 证据数据
            database_id: 数据库ID，如果不提供则从配置读取
            
        Returns:
            创建的页面信息
        """
        db_id = database_id or config.NOTION_EVIDENCE_DB_ID
        if not db_id:
            raise ValueError("Evidence 数据库ID未配置")
        
        properties = {
            "Name": {
                "title": [{"text": {"content": evidence.title}}]
            },
            "内容": {
                "rich_text": [{"text": {"content": evidence.content[:2000]}}]
            },
        }
        
        if evidence.source_url:
            properties["来源链接"] = {"url": evidence.source_url}
        if evidence.source_title:
            properties["来源标题"] = {
                "rich_text": [{"text": {"content": evidence.source_title}}]
            }
        if evidence.page_number:
            properties["页码"] = {"number": evidence.page_number}
        
        return self.client.pages.create(
            parent={"database_id": db_id},
            properties=properties
        )
    
    def query_claims(
        self, 
        database_id: Optional[str] = None,
        polarity: Optional[Polarity] = None,
        concept: Optional[str] = None,
        limit: int = 100
    ) -> list[dict]:
        """
        查询观点
        
        Args:
            database_id: 数据库ID
            polarity: 按极性筛选
            concept: 按关联概念筛选
            limit: 返回数量限制
            
        Returns:
            页面列表
        """
        db_id = database_id or config.NOTION_CLAIMS_DB_ID
        if not db_id:
            raise ValueError("Claims 数据库ID未配置")
        
        filters = []
        
        if polarity:
            filters.append({
                "property": "极性",
                "select": {"equals": polarity.value}
            })
        
        if concept:
            filters.append({
                "property": "关联概念",
                "multi_select": {"contains": concept}
            })
        
        query_params = {
            "database_id": db_id,
            "page_size": min(limit, 100)
        }
        
        if filters:
            if len(filters) == 1:
                query_params["filter"] = filters[0]
            else:
                query_params["filter"] = {"and": filters}
        
        return self.client.databases.query(**query_params).get("results", [])
    
    def sync_ontology(self, database_id: Optional[str] = None) -> list[dict]:
        """
        将本体同步到 Notion 数据库
        
        Args:
            database_id: 本体数据库ID
            
        Returns:
            创建的页面列表
        """
        from .ontology import ALLERGY_ONTOLOGY
        
        db_id = database_id or config.NOTION_ONTOLOGY_DB_ID
        if not db_id:
            raise ValueError("Ontology 数据库ID未配置")
        
        created_pages = []
        
        for i, (node_id, node) in enumerate(ALLERGY_ONTOLOGY.items(), 1):
            try:
                # 使用完整的列结构
                properties = {
                    "Name": {
                        "title": [{"text": {"content": node.name_zh}}]
                    },
                    "ID": {
                        "rich_text": [{"text": {"content": node.id}}]
                    },
                    "英文名": {
                        "rich_text": [{"text": {"content": node.name_en or ""}}]
                    },
                    "类别": {
                        "select": {"name": node.category.value}
                    },
                    "别名": {
                        "rich_text": [{"text": {"content": ", ".join(node.aliases)}}]
                    },
                }
                
                if node.description:
                    properties["描述"] = {
                        "rich_text": [{"text": {"content": node.description}}]
                    }
                
                if node.parent_id:
                    properties["父节点"] = {
                        "rich_text": [{"text": {"content": node.parent_id}}]
                    }
                
                page = self.client.pages.create(
                    parent={"database_id": db_id},
                    properties=properties
                )
                created_pages.append(page)
                print(f"  ✓ ({i}/{len(ALLERGY_ONTOLOGY)}) {node.name_zh}")
                
            except Exception as e:
                print(f"  ✗ ({i}/{len(ALLERGY_ONTOLOGY)}) {node.name_zh}: {str(e)}")
        
        return created_pages
