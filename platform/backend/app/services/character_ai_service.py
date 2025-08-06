"""角色AI相关服务（头像生成、语音合成、质量评估等）"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
import logging
import os
import json
import asyncio
from datetime import datetime
import requests
import base64
from PIL import Image
import io

from app.models.character import Character
from app.models import VoiceProfile, UsageStats
from app.utils import log_system_event, update_usage_stats
from app.core.config import settings

logger = logging.getLogger(__name__)

class CharacterAIService:
    """角色AI相关服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def generate_character_avatar(
        self, 
        character_id: int, 
        generation_request
    ) -> Dict[str, Any]:
        """生成角色头像"""
        try:
            character = self.db.query(Character).filter(
                Character.id == character_id
            ).first()
            
            if not character:
                raise HTTPException(status_code=404, detail="角色不存在")
            
            # 从请求对象中获取参数
            character_name = generation_request.character_name
            description = generation_request.description or ""
            style = generation_request.style or "default"
            
            # 构建生成提示词
            prompt = self._build_avatar_prompt_from_request(character, character_name, description, style)
            
            # 调用AI生成服务
            avatar_path = await self._call_avatar_generation_api(prompt, style)
            
            # 保存生成的头像
            avatar_path = self._save_generated_avatar(character_id, avatar_path)
            
            # 更新角色记录
            character.avatar_path = avatar_path
            character.updated_at = datetime.now()
            self.db.commit()
            
            # 记录系统日志
            await log_system_event(
                self.db,
                "character_avatar_generated",
                f"生成角色头像: {character.name}",
                {
                    "character_id": character_id,
                    "prompt": prompt,
                    "style": style,
                    "avatar_path": avatar_path
                }
            )
            
            return {
                "success": True,
                "avatar_url": f"/api/v1/characters/avatar/{character_id}",
                "task_id": None,
                "message": "头像生成成功"
            }
        except Exception as e:
            logger.error(f"生成角色头像失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"生成头像失败: {str(e)}")
    
    def _build_avatar_prompt_from_request(self, character, character_name: str, description: str, style: str) -> str:
        """根据请求参数构建头像生成提示词"""
        prompt_parts = []
        
        # 添加角色名称
        if character_name:
            prompt_parts.append(f"Character name: {character_name}")
        
        # 添加描述信息
        if description:
            prompt_parts.append(f"Description: {description}")
        elif character.description:
            prompt_parts.append(f"Description: {character.description}")
        
        # 添加风格信息
        style_prompts = {
            "anime": "anime style, detailed character design",
            "realistic": "realistic portrait, high quality",
            "cartoon": "cartoon style, colorful and vibrant",
            "default": "high quality character portrait"
        }
        
        style_prompt = style_prompts.get(style, style_prompts["default"])
        prompt_parts.append(style_prompt)
        
        return ", ".join(prompt_parts)
    
    def _build_avatar_prompt(self, character: Character, style: str, gender: str) -> str:
        """构建头像生成提示词"""
        base_prompt = f"Portrait of {character.name}"
        
        if character.description:
            base_prompt += f", {character.description}"
        
        # 添加性别信息
        if gender == "auto":
            if character.voice_type in ["male", "female"]:
                gender = character.voice_type
            else:
                gender = "person"
        
        if gender != "person":
            base_prompt += f", {gender}"
        
        # 添加风格信息
        style_prompts = {
            "anime": "anime style, detailed, high quality, colorful",
            "realistic": "photorealistic, detailed, professional portrait",
            "cartoon": "cartoon style, cute, colorful, friendly",
            "fantasy": "fantasy art style, magical, detailed, epic"
        }
        
        if style in style_prompts:
            base_prompt += f", {style_prompts[style]}"
        
        return base_prompt
    
    async def _call_avatar_generation_api(self, prompt: str, style: str) -> str:
        """调用头像生成API，返回文件路径"""
        try:
            # 🔧 修复：使用ComfyUI生成头像
            from app.clients.comfyui_client import ComfyUIClient
            
            # 构建负面提示词
            negative_prompt = "low quality, blurry, distorted, ugly, deformed"
            
            # 根据风格调整提示词
            style_prompts = {
                "realistic": f"{prompt}, realistic portrait, high quality, detailed",
                "anime": f"{prompt}, anime style, detailed character design, vibrant colors",
                "cartoon": f"{prompt}, cartoon style, colorful and vibrant, clean lines",
                "oil_painting": f"{prompt}, oil painting style, artistic, textured",
                "watercolor": f"{prompt}, watercolor style, soft colors, artistic"
            }
            
            enhanced_prompt = style_prompts.get(style, prompt)
            
            # 创建ComfyUI客户端
            comfyui_client = ComfyUIClient()
            
            try:
                image_path = await comfyui_client.generate_image(
                    prompt=enhanced_prompt,
                    negative_prompt=negative_prompt,
                    width=512,
                    height=512,
                    steps=20,
                    cfg=7.5,
                    filename_prefix=f"avatar_{style}"
                )
                
                return image_path
                    
            except Exception as e:
                logger.error(f"ComfyUI头像生成失败: {str(e)}")
                # 如果ComfyUI失败，返回默认头像路径
                return self._generate_default_avatar_path(style)
            
        except Exception as e:
            logger.error(f"头像生成失败: {str(e)}")
            # 返回默认头像路径
            return self._generate_default_avatar_path(style)
    
    def _generate_default_avatar(self, style: str) -> bytes:
        """生成默认头像"""
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        # 创建默认头像
        size = (512, 512)
        img = Image.new('RGB', size, color='#8b5cf6')
        draw = ImageDraw.Draw(img)
        
        # 尝试加载字体，如果失败则使用默认字体
        try:
            font = ImageFont.truetype("arial.ttf", 120)
        except:
            font = ImageFont.load_default()
        
        # 绘制文字
        text = f"AI\n{style.upper()}"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size[0] - text_width) // 2
        y = (size[1] - text_height) // 2
        
        draw.text((x, y), text, fill='white', font=font)
        
        # 转换为字节流
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return img_byte_arr.getvalue()
    
    def _generate_default_avatar_path(self, style: str) -> str:
        """生成默认头像并返回路径"""
        # 创建临时目录
        temp_dir = os.path.join(settings.UPLOAD_DIR, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"default_avatar_{style}_{timestamp}.png"
        file_path = os.path.join(temp_dir, filename)
        
        # 生成默认头像
        avatar_data = self._generate_default_avatar(style)
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(avatar_data)
        
        return file_path
    
    def _save_generated_avatar(self, character_id: int, avatar_path: str) -> str:
        """保存生成的头像"""
        # 创建保存目录
        avatar_dir = os.path.join(settings.UPLOAD_DIR, "characters", str(character_id), "avatar")
        os.makedirs(avatar_dir, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"generated_avatar_{timestamp}.png"
        file_path = os.path.join(avatar_dir, filename)
        
        # 复制文件
        try:
            with open(avatar_path, 'rb') as src_file:
                with open(file_path, 'wb') as dst_file:
                    dst_file.write(src_file.read())
            return file_path
        except Exception as e:
            logger.error(f"保存头像失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"保存头像失败: {str(e)}")
    
    def test_voice_synthesis(
        self, 
        character_id: int, 
        text: str = "这是一个语音测试。"
    ) -> Dict[str, Any]:
        """测试角色语音合成"""
        try:
            character = self.db.query(Character).filter(
                Character.id == character_id
            ).first()
            
            if not character:
                raise HTTPException(status_code=404, detail="角色不存在")
            
            if not character.reference_audio_path:
                raise HTTPException(status_code=400, detail="角色未配置参考音频")
            
            # 调用语音合成服务
            synthesis_result = self._call_voice_synthesis_api(character, text)
            
            # 更新使用统计
            update_usage_stats(self.db, character_id, "voice_test")
            
            # 记录系统日志
            log_system_event(
                self.db,
                "voice_synthesis_test",
                f"测试角色语音合成: {character.name}",
                {
                    "character_id": character_id,
                    "text": text,
                    "audio_path": synthesis_result.get("audio_path")
                }
            )
            
            return {
                "success": True,
                "data": synthesis_result,
                "message": "语音合成测试完成"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"语音合成测试失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"语音合成测试失败: {str(e)}")
    
    def _call_voice_synthesis_api(self, character: Character, text: str) -> Dict[str, Any]:
        """调用语音合成API"""
        try:
            api_url = settings.VOICE_SYNTHESIS_API_URL
            if not api_url:
                raise HTTPException(status_code=503, detail="语音合成服务未配置")
            
            payload = {
                "text": text,
                "reference_audio": character.reference_audio_path,
                "character_id": character.id,
                "voice_type": character.voice_type
            }
            
            response = requests.post(
                api_url,
                json=payload,
                headers={"Authorization": f"Bearer {settings.VOICE_SYNTHESIS_API_KEY}"},
                timeout=120
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"语音合成API调用失败: {response.text}"
                )
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"语音合成API调用失败: {str(e)}")
            raise HTTPException(status_code=503, detail="语音合成服务不可用")
    
    def evaluate_voice_quality(self, character_id: int) -> Dict[str, Any]:
        """评估角色语音质量"""
        try:
            character = self.db.query(Character).filter(
                Character.id == character_id
            ).first()
            
            if not character:
                raise HTTPException(status_code=404, detail="角色不存在")
            
            if not character.reference_audio_path:
                raise HTTPException(status_code=400, detail="角色未配置参考音频")
            
            # 调用语音质量评估服务
            quality_result = self._call_voice_quality_api(character)
            
            # 更新角色质量分数
            character.quality_score = quality_result.get("quality_score", 0)
            character.updated_at = datetime.now()
            self.db.commit()
            
            # 记录系统日志
            log_system_event(
                self.db,
                "voice_quality_evaluated",
                f"评估角色语音质量: {character.name}",
                {
                    "character_id": character_id,
                    "quality_score": character.quality_score,
                    "evaluation_details": quality_result
                }
            )
            
            return {
                "success": True,
                "data": {
                    "character_id": character_id,
                    "quality_score": character.quality_score,
                    "evaluation_details": quality_result
                },
                "message": "语音质量评估完成"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"语音质量评估失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"语音质量评估失败: {str(e)}")
    
    def _call_voice_quality_api(self, character: Character) -> Dict[str, Any]:
        """调用语音质量评估API"""
        try:
            api_url = settings.VOICE_QUALITY_API_URL
            if not api_url:
                # 如果没有配置API，使用简单的质量评估
                return self._simple_quality_evaluation(character)
            
            payload = {
                "audio_path": character.reference_audio_path,
                "character_id": character.id
            }
            
            response = requests.post(
                api_url,
                json=payload,
                headers={"Authorization": f"Bearer {settings.VOICE_QUALITY_API_KEY}"},
                timeout=60
            )
            
            if response.status_code != 200:
                logger.warning(f"语音质量API调用失败，使用简单评估: {response.text}")
                return self._simple_quality_evaluation(character)
            
            return response.json()
            
        except requests.RequestException as e:
            logger.warning(f"语音质量API调用失败，使用简单评估: {str(e)}")
            return self._simple_quality_evaluation(character)
    
    def _simple_quality_evaluation(self, character: Character) -> Dict[str, Any]:
        """简单的语音质量评估"""
        quality_score = 0.0
        factors = []
        
        # 检查是否有参考音频
        if character.reference_audio_path and os.path.exists(character.reference_audio_path):
            quality_score += 30
            factors.append("有参考音频文件")
        
        # 检查是否有潜在文件
        if character.latent_file_path and os.path.exists(character.latent_file_path):
            quality_score += 30
            factors.append("有潜在特征文件")
        
        # 检查音频时长（如果有的话）
        if hasattr(character, 'reference_audio_duration') and character.reference_audio_duration:
            if character.reference_audio_duration >= 10:  # 10秒以上
                quality_score += 20
                factors.append("音频时长充足")
            elif character.reference_audio_duration >= 5:  # 5-10秒
                quality_score += 10
                factors.append("音频时长适中")
        
        # 检查描述信息
        if character.description and len(character.description) > 10:
            quality_score += 10
            factors.append("有详细描述")
        
        # 检查声音类型
        if character.voice_type and character.voice_type != "custom":
            quality_score += 10
            factors.append("已设置声音类型")
        
        return {
            "quality_score": min(quality_score, 100),  # 最高100分
            "evaluation_factors": factors,
            "evaluation_method": "simple",
            "timestamp": datetime.now().isoformat()
        }
    
    def get_popular_tags(self, limit: int = 20) -> Dict[str, Any]:
        """获取热门标签"""
        try:
            # 获取所有角色的标签
            characters = self.db.query(Character).filter(
                Character.tags.isnot(None),
                Character.tags != ""
            ).all()
            
            tag_counts = {}
            
            for character in characters:
                try:
                    tags = character.get_tags()
                    for tag in tags:
                        if isinstance(tag, str) and tag.strip():
                            tag = tag.strip()
                            tag_counts[tag] = tag_counts.get(tag, 0) + 1
                except (Exception):
                    continue
            
            # 按使用次数排序
            popular_tags = sorted(
                tag_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:limit]
            
            return {
                "success": True,
                "data": {
                    "tags": [
                        {"name": tag, "count": count} 
                        for tag, count in popular_tags
                    ],
                    "total_unique_tags": len(tag_counts)
                },
                "message": f"获取到 {len(popular_tags)} 个热门标签"
            }
            
        except Exception as e:
            logger.error(f"获取热门标签失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取热门标签失败: {str(e)}")
    
    def search_similar_characters(
        self, 
        character_id: int, 
        similarity_threshold: float = 0.7,
        limit: int = 10
    ) -> Dict[str, Any]:
        """搜索相似角色"""
        try:
            target_character = self.db.query(Character).filter(
                Character.id == character_id
            ).first()
            
            if not target_character:
                raise HTTPException(status_code=404, detail="角色不存在")
            
            # 获取所有其他角色
            other_characters = self.db.query(Character).filter(
                Character.id != character_id
            ).all()
            
            similar_characters = []
            
            for character in other_characters:
                similarity = self._calculate_character_similarity(target_character, character)
                
                if similarity >= similarity_threshold:
                    similar_characters.append({
                        "character": character.to_dict(),
                        "similarity": similarity
                    })
            
            # 按相似度排序
            similar_characters.sort(key=lambda x: x["similarity"], reverse=True)
            similar_characters = similar_characters[:limit]
            
            return {
                "success": True,
                "data": {
                    "target_character": target_character.to_dict(),
                    "similar_characters": similar_characters,
                    "similarity_threshold": similarity_threshold
                },
                "message": f"找到 {len(similar_characters)} 个相似角色"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"搜索相似角色失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"搜索相似角色失败: {str(e)}")
    
    def _calculate_character_similarity(self, char1: Character, char2: Character) -> float:
        """计算角色相似度"""
        similarity = 0.0
        factors = 0
        
        # 声音类型相似度
        if char1.voice_type and char2.voice_type:
            if char1.voice_type == char2.voice_type:
                similarity += 0.3
            factors += 1
        
        # 标签相似度
        try:
            tags1 = set(char1.get_tags())
            tags2 = set(char2.get_tags())
            
            if tags1 and tags2:
                tag_similarity = len(tags1.intersection(tags2)) / len(tags1.union(tags2))
                similarity += tag_similarity * 0.4
                factors += 1
        except (Exception):
            pass
        
        # 书籍相似度
        if char1.book_id and char2.book_id:
            if char1.book_id == char2.book_id:
                similarity += 0.2
            factors += 1
        
        # 描述相似度（简单的关键词匹配）
        if char1.description and char2.description:
            desc1_words = set(char1.description.lower().split())
            desc2_words = set(char2.description.lower().split())
            
            if desc1_words and desc2_words:
                desc_similarity = len(desc1_words.intersection(desc2_words)) / len(desc1_words.union(desc2_words))
                similarity += desc_similarity * 0.1
                factors += 1
        
        return similarity / max(factors, 1) if factors > 0 else 0.0