"""
Notion API 交互模块
处理与 Notion 数据库的所有交互
"""

from typing import Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import requests

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


@dataclass
class Article:
    """文章数据结构"""
    title: str                          # 文章标题
    content: str                        # 文章全文内容
    file_path: str                      # 文件路径
    file_md5: str                       # 文件 MD5
    file_size: int                      # 文件大小（字节）
    source_url: Optional[str] = None    # 来源URL


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
    
    def add_article(self, article: Article, database_id: Optional[str] = None, upload_file: bool = False) -> dict:
        """
        添加文章到 Notion 数据库
        
        Args:
            article: 文章数据
            database_id: 数据库ID，如果不提供则从配置读取
            
        Returns:
            创建的页面信息
        """
        db_id = database_id or config.NOTION_ARTICLES_DB_ID
        if not db_id:
            raise ValueError("Articles 数据库ID未配置")
        
        properties = {
            "Name": {
                "title": [{"text": {"content": article.title}}]
            },
            "MD5": {
                "rich_text": [{"text": {"content": article.file_md5}}]
            },
            "文件路径": {
                "rich_text": [{"text": {"content": article.file_path}}]
            },
            "文件大小": {
                "number": article.file_size
            }
        }
        
        if article.source_url:
            properties["来源链接"] = {"url": article.source_url}
        
        # 创建页面
        page = self.client.pages.create(
            parent={"database_id": db_id},
            properties=properties
        )
        
        # 添加文章内容到页面 body
        if article.content:
            # 将内容分段（Notion 限制每个 block 最多 2000 字符）
            content_chunks = self._split_text(article.content, 1900)
            blocks = []
            
            for chunk in content_chunks:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": chunk}}]
                    }
                })
            
            # 批量添加内容块
            if blocks:
                self.client.blocks.children.append(
                    block_id=page["id"],
                    children=blocks[:100]  # Notion 限制一次最多100个块
                )
        
        return page
    
    def upload_pdf_to_page(self, page_id: str, pdf_path: str | Path) -> dict:
        """
        上传 PDF 文件到 Notion 页面
        
        Args:
            page_id: Notion 页面 ID
            pdf_path: PDF 文件路径
            
        Returns:
            上传结果
        """
        pdf_path = Path(pdf_path)
        file_size = pdf_path.stat().st_size
        
        # 检查文件大小限制（免费版 5MB）
        max_size = 5 * 1024 * 1024  # 5 MB
        if file_size > max_size:
            raise ValueError(f"文件过大 ({file_size / 1024 / 1024:.2f} MB)，免费版限制 5 MB")
        
        # 步骤 1: 创建文件上传对象
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
        }
        
        # 获取上传 URL
        upload_response = requests.post(
            "https://api.notion.com/v1/file_uploads",
            headers=headers,
            json={
                "name": pdf_path.name,
                "file_size": file_size
            }
        )
        
        if upload_response.status_code != 200:
            raise Exception(f"创建上传失败: {upload_response.text}")
        
        upload_data = upload_response.json()
        upload_url = upload_data.get("upload_url")
        file_id = upload_data.get("id")
        
        # 步骤 2: 上传文件内容到 upload_url（不需要 Authorization）
        with open(pdf_path, 'rb') as f:
            files = {
                'file': (pdf_path.name, f, 'application/pdf')
            }
            
            # 注意：上传到 upload_url 时不要带 Authorization header
            upload_file_response = requests.post(
                upload_url,
                files=files
            )
            
            if upload_file_response.status_code not in [200, 201, 204]:
                raise Exception(f"上传文件失败 ({upload_file_response.status_code}): {upload_file_response.text[:200]}")
        
        # 步骤 3: 将文件添加到页面
        self.client.blocks.children.append(
            block_id=page_id,
            children=[
                {
                    "object": "block",
                    "type": "pdf",
                    "pdf": {
                        "type": "file",
                        "file": {
                            "file_id": file_id
                        }
                    }
                }
            ]
        )
        
        return {
            "file_id": file_id,
            "file_name": pdf_path.name,
            "file_size": file_size
        }
    
    def query_article_by_md5(self, md5: str, database_id: Optional[str] = None) -> Optional[dict]:
        """
        通过 MD5 查询文章是否已存在
        
        Args:
            md5: 文件 MD5 哈希值
            database_id: 数据库ID
            
        Returns:
            文章页面信息，如果不存在则返回 None
        """
        db_id = database_id or config.NOTION_ARTICLES_DB_ID
        if not db_id:
            return None
        
        try:
            # 注意: Notion API 不支持直接按 rich_text 字段筛选
            # 需要先查询所有，然后在客户端过滤
            # 更好的方式是使用 Notion 的 filter API（如果支持）
            results = self.client.databases.query(
                database_id=db_id
            )
            
            for page in results.get("results", []):
                properties = page.get("properties", {})
                md5_prop = properties.get("MD5", {})
                
                if md5_prop.get("type") == "rich_text":
                    rich_texts = md5_prop.get("rich_text", [])
                    if rich_texts and rich_texts[0].get("text", {}).get("content") == md5:
                        return page
            
            return None
            
        except Exception as e:
            print(f"查询失败: {e}")
            return None
    
    @staticmethod
    def _split_text(text: str, chunk_size: int = 1900) -> list[str]:
        """
        将长文本分割成小块
        
        Args:
            text: 原文本
            chunk_size: 每块最大字符数
            
        Returns:
            文本块列表
        """
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i:i + chunk_size])
        return chunks
    
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
