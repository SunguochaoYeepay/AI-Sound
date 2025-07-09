from typing import Optional
from pydantic import BaseModel

class CharacterBase(BaseModel):
    name: str
    description: Optional[str] = None
    voice_profile: Optional[str] = None
    voice_config: Optional[str] = None
    book_id: Optional[int] = None
    chapter_id: Optional[int] = None

class CharacterCreate(CharacterBase):
    pass

class CharacterUpdate(CharacterBase):
    name: Optional[str] = None

class CharacterInDB(CharacterBase):
    id: int
    
    class Config:
        from_attributes = True

class CharacterResponse(CharacterInDB):
    pass

class CharacterMatchResult(BaseModel):
    matched: bool
    character: Optional[CharacterResponse] = None
    current_config: Optional[str] = None  # 当前配置
    matched_config: Optional[str] = None  # 匹配到的配置 