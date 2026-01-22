"""
配置管理模块
从 .env 文件加载环境变量
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class Config:
    """配置类"""
    
    # Notion 配置
    NOTION_TOKEN: str = os.getenv("NOTION_TOKEN", "")
    NOTION_CLAIMS_DB_ID: str = os.getenv("NOTION_CLAIMS_DB_ID", "")
    NOTION_EVIDENCE_DB_ID: str = os.getenv("NOTION_EVIDENCE_DB_ID", "")
    NOTION_ONTOLOGY_DB_ID: str = os.getenv("NOTION_ONTOLOGY_DB_ID", "")
    NOTION_ARTICLES_DB_ID: str = os.getenv("NOTION_ARTICLES_DB_ID", "")
    
    # OpenAI 配置
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    @classmethod
    def validate(cls) -> list[str]:
        """验证必需的配置项"""
        errors = []
        
        if not cls.NOTION_TOKEN:
            errors.append("NOTION_TOKEN 未配置")
        if not cls.NOTION_CLAIMS_DB_ID:
            errors.append("NOTION_CLAIMS_DB_ID 未配置")
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY 未配置")
            
        return errors
    
    @classmethod
    def is_valid(cls) -> bool:
        """检查配置是否有效"""
        return len(cls.validate()) == 0


config = Config()
