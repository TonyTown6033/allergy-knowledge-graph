"""
文件追踪和去重模块
使用 MD5 哈希值跟踪已处理的文件
"""

import json
import hashlib
from pathlib import Path
from typing import Optional
from datetime import datetime


class FileTracker:
    """文件处理追踪器"""
    
    def __init__(self, db_path: str = ".processed_files.json"):
        """
        初始化追踪器
        
        Args:
            db_path: 追踪数据库文件路径
        """
        self.db_path = Path(db_path)
        self.data = self._load_db()
    
    def _load_db(self) -> dict:
        """加载追踪数据库"""
        if self.db_path.exists():
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_db(self):
        """保存追踪数据库"""
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def calculate_md5(file_path: str | Path) -> str:
        """
        计算文件的 MD5 哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            MD5 哈希值（32位十六进制字符串）
        """
        md5_hash = hashlib.md5()
        
        with open(file_path, "rb") as f:
            # 分块读取以处理大文件
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        
        return md5_hash.hexdigest()
    
    def is_processed(self, file_path: str | Path) -> bool:
        """
        检查文件是否已处理
        
        Args:
            file_path: 文件路径
            
        Returns:
            True 如果已处理，False 如果未处理
        """
        file_path = Path(file_path)
        md5 = self.calculate_md5(file_path)
        return md5 in self.data
    
    def get_record(self, file_path: str | Path) -> Optional[dict]:
        """
        获取文件的处理记录
        
        Args:
            file_path: 文件路径
            
        Returns:
            处理记录字典，如果未处理则返回 None
        """
        file_path = Path(file_path)
        md5 = self.calculate_md5(file_path)
        return self.data.get(md5)
    
    def mark_processed(
        self, 
        file_path: str | Path,
        notion_article_id: Optional[str] = None,
        claims_count: int = 0,
        evidence_count: int = 0,
        metadata: Optional[dict] = None
    ):
        """
        标记文件为已处理
        
        Args:
            file_path: 文件路径
            notion_article_id: Notion 文章页面 ID
            claims_count: 提取的观点数量
            evidence_count: 提取的证据数量
            metadata: 额外的元数据
        """
        file_path = Path(file_path)
        md5 = self.calculate_md5(file_path)
        
        record = {
            "file_name": file_path.name,
            "file_path": str(file_path),
            "md5": md5,
            "processed_at": datetime.now().isoformat(),
            "notion_article_id": notion_article_id,
            "claims_count": claims_count,
            "evidence_count": evidence_count,
        }
        
        if metadata:
            record.update(metadata)
        
        self.data[md5] = record
        self._save_db()
    
    def remove_record(self, file_path: str | Path):
        """
        删除文件的处理记录
        
        Args:
            file_path: 文件路径
        """
        file_path = Path(file_path)
        md5 = self.calculate_md5(file_path)
        if md5 in self.data:
            del self.data[md5]
            self._save_db()
    
    def get_all_records(self) -> list[dict]:
        """获取所有处理记录"""
        return list(self.data.values())
    
    def get_statistics(self) -> dict:
        """获取统计信息"""
        records = self.get_all_records()
        return {
            "total_files": len(records),
            "total_claims": sum(r.get("claims_count", 0) for r in records),
            "total_evidence": sum(r.get("evidence_count", 0) for r in records),
        }
