from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.base import Base

class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    voice_profile = Column(String(255), nullable=True)
    voice_config = Column(Text, nullable=True)
    
    # 新增字段
    book_id = Column(Integer, ForeignKey("books.id", ondelete="SET NULL"), nullable=True)
    chapter_id = Column(Integer, ForeignKey("book_chapters.id", ondelete="SET NULL"), nullable=True)
    
    # 关联关系
    book = relationship("Book", back_populates="characters")
    chapter = relationship("BookChapter", back_populates="characters") 