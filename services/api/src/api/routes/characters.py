"""
角色管理API路由
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging

from ...models.character import Character, CharacterCreate, CharacterUpdate
from ...services.character_service import CharacterService
from ...core.dependencies import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/characters", tags=["characters"])


@router.get("/", response_model=List[Character])
async def list_characters(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=100, description="返回记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db=Depends(get_db)
):
    """获取角色列表"""
    try:
        service = CharacterService(db)
        characters = await service.list_characters(skip=skip, limit=limit, search=search)
        return characters
    except Exception as e:
        logger.error(f"获取角色列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{character_id}", response_model=Character)
async def get_character(character_id: str, db=Depends(get_db)):
    """获取指定角色"""
    try:
        service = CharacterService(db)
        character = await service.get_character(character_id)
        if not character:
            raise HTTPException(status_code=404, detail="角色未找到")
        return character
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取角色失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Character)
async def create_character(character_data: CharacterCreate, db=Depends(get_db)):
    """创建新角色"""
    try:
        service = CharacterService(db)
        character = await service.create_character(character_data)
        return character
    except Exception as e:
        logger.error(f"创建角色失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{character_id}", response_model=Character)
async def update_character(
    character_id: str, 
    character_data: CharacterUpdate, 
    db=Depends(get_db)
):
    """更新角色"""
    try:
        service = CharacterService(db)
        character = await service.update_character(character_id, character_data)
        if not character:
            raise HTTPException(status_code=404, detail="角色未找到")
        return character
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新角色失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{character_id}")
async def delete_character(character_id: str, db=Depends(get_db)):
    """删除角色"""
    try:
        service = CharacterService(db)
        success = await service.delete_character(character_id)
        if not success:
            raise HTTPException(status_code=404, detail="角色未找到")
        return {"message": "角色已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除角色失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{character_id}/voices")
async def assign_voice_to_character(
    character_id: str,
    voice_id: str,
    engine: Optional[str] = None,
    db=Depends(get_db)
):
    """为角色分配声音"""
    try:
        service = CharacterService(db)
        success = await service.assign_voice(character_id, voice_id, engine)
        if not success:
            raise HTTPException(status_code=404, detail="角色或声音未找到")
        return {"message": "声音已分配给角色"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分配声音失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{character_id}/voices/{voice_id}")
async def remove_voice_from_character(
    character_id: str,
    voice_id: str,
    db=Depends(get_db)
):
    """从角色移除声音"""
    try:
        service = CharacterService(db)
        success = await service.remove_voice(character_id, voice_id)
        if not success:
            raise HTTPException(status_code=404, detail="角色或声音映射未找到")
        return {"message": "声音已从角色移除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"移除声音失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{character_id}/test")
async def test_character_voice(
    character_id: str,
    text: str = "你好，这是声音测试。",
    voice_id: Optional[str] = None,
    db=Depends(get_db)
):
    """测试角色声音"""
    try:
        service = CharacterService(db)
        # 创建测试数据对象
        from ...models.character import CharacterVoiceTest
        test_data = CharacterVoiceTest(
            text=text,
            voice_id=voice_id
        )
        result = await service.test_character_voice(character_id, test_data)
        if not result:
            raise HTTPException(status_code=404, detail="角色未找到或没有可用声音")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试角色声音失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))