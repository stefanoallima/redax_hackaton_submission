"""
Legal Article model
"""
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from pgvector.sqlalchemy import Vector
from app.db.base_class import Base
import uuid
from datetime import datetime


class LegalArticle(Base):
    __tablename__ = "legal_articles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_code = Column(String(50), unique=True, nullable=False, index=True)  # e.g., "CC Art. 1453"
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=True, index=True)  # Diritto contrattuale, etc.
    embedding = Column(Vector(1536), nullable=True)  # OpenAI text-embedding-ada-002
    related_article_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<LegalArticle {self.article_code}>"
