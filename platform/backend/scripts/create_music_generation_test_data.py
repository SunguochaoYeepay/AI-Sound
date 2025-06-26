#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建音乐生成测试数据
初始化音乐风格模板和系统设置
"""

import sys
import os
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import (
    MusicStyleTemplate, MusicGenerationSettings, MusicSceneType
)
from app.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_style_templates(db_session):
    """创建默认音乐风格模板"""
    
    templates = [
        {
            "name": "battle",
            "display_name": "战斗场景",
            "description": "激烈的战斗场景音乐，节奏强烈，充满紧张感",
            "category": "action",
            "default_tempo": 128,
            "tempo_range_min": 120,
            "tempo_range_max": 140,
            "default_volume": -9.6,
            "volume_range_min": -12.0,
            "volume_range_max": -6.0,
            "default_intensity": 0.8,
            "intensity_range_min": 0.6,
            "intensity_range_max": 1.0,
            "keywords": ["战斗", "冲突", "激战", "厮杀", "对决", "交锋", "血战"],
            "emotion_tags": ["紧张", "激烈", "危险", "兴奋"],
            "scene_types": ["battle"],
            "generation_params": {
                "style": "epic orchestral",
                "instruments": ["drums", "brass", "strings"],
                "mood": "intense"
            },
            "post_processing_params": {
                "compression": 0.7,
                "eq_boost": "mid_high"
            },
            "is_system": True,
            "is_public": True
        },
        {
            "name": "romance",
            "display_name": "浪漫场景",
            "description": "温柔浪漫的场景音乐，适合爱情和温馨时刻",
            "category": "emotion",
            "default_tempo": 78,
            "tempo_range_min": 60,
            "tempo_range_max": 90,
            "default_volume": -13.8,
            "volume_range_min": -18.0,
            "volume_range_max": -10.0,
            "default_intensity": 0.4,
            "intensity_range_min": 0.2,
            "intensity_range_max": 0.6,
            "keywords": ["爱情", "浪漫", "温柔", "甜蜜", "情深", "缠绵", "柔情"],
            "emotion_tags": ["温馨", "浪漫", "甜蜜", "柔和"],
            "scene_types": ["romance"],
            "generation_params": {
                "style": "soft piano ballad",
                "instruments": ["piano", "strings", "harp"],
                "mood": "romantic"
            },
            "post_processing_params": {
                "reverb": 0.4,
                "warmth": 0.6
            },
            "is_system": True,
            "is_public": True
        },
        {
            "name": "mystery",
            "display_name": "悬疑场景",
            "description": "神秘悬疑的场景音乐，营造紧张和未知的氛围",
            "category": "atmosphere",
            "default_tempo": 89,
            "tempo_range_min": 80,
            "tempo_range_max": 100,
            "default_volume": -11.4,
            "volume_range_min": -15.0,
            "volume_range_max": -8.0,
            "default_intensity": 0.6,
            "intensity_range_min": 0.4,
            "intensity_range_max": 0.8,
            "keywords": ["神秘", "悬疑", "诡异", "阴森", "诡秘", "隐秘", "暗藏"],
            "emotion_tags": ["神秘", "紧张", "不安", "诡异"],
            "scene_types": ["mystery"],
            "generation_params": {
                "style": "dark ambient",
                "instruments": ["synthesizer", "celesta", "low_strings"],
                "mood": "mysterious"
            },
            "post_processing_params": {
                "echo": 0.3,
                "low_pass": 0.2
            },
            "is_system": True,
            "is_public": True
        },
        {
            "name": "peaceful",
            "display_name": "平静场景",
            "description": "宁静平和的场景音乐，适合日常和思考时刻",
            "category": "ambient",
            "default_tempo": 62,
            "tempo_range_min": 50,
            "tempo_range_max": 75,
            "default_volume": -17.7,
            "volume_range_min": -22.0,
            "volume_range_max": -15.0,
            "default_intensity": 0.2,
            "intensity_range_min": 0.1,
            "intensity_range_max": 0.4,
            "keywords": ["平静", "宁静", "安详", "祥和", "静谧", "悠闲", "舒缓"],
            "emotion_tags": ["平静", "安详", "放松", "宁静"],
            "scene_types": ["peaceful"],
            "generation_params": {
                "style": "ambient nature",
                "instruments": ["flute", "soft_strings", "nature_sounds"],
                "mood": "peaceful"
            },
            "post_processing_params": {
                "soft_compression": 0.3,
                "gentle_eq": True
            },
            "is_system": True,
            "is_public": True
        },
        {
            "name": "sad",
            "display_name": "悲伤场景",
            "description": "悲伤哀愁的场景音乐，表达离别和忧伤情感",
            "category": "emotion",
            "default_tempo": 55,
            "tempo_range_min": 45,
            "tempo_range_max": 70,
            "default_volume": -15.2,
            "volume_range_min": -20.0,
            "volume_range_max": -12.0,
            "default_intensity": 0.5,
            "intensity_range_min": 0.3,
            "intensity_range_max": 0.7,
            "keywords": ["悲伤", "哀愁", "忧郁", "凄凉", "哀伤", "沉痛", "悲怆"],
            "emotion_tags": ["悲伤", "忧郁", "哀愁", "沉重"],
            "scene_types": ["sad"],
            "generation_params": {
                "style": "melancholic piano",
                "instruments": ["piano", "violin", "cello"],
                "mood": "melancholic"
            },
            "post_processing_params": {
                "reverb": 0.5,
                "minor_key": True
            },
            "is_system": True,
            "is_public": True
        },
        {
            "name": "epic",
            "display_name": "史诗场景",
            "description": "宏大史诗的场景音乐，适合重大事件和转折点",
            "category": "cinematic",
            "default_tempo": 95,
            "tempo_range_min": 85,
            "tempo_range_max": 110,
            "default_volume": -8.5,
            "volume_range_min": -12.0,
            "volume_range_max": -5.0,
            "default_intensity": 0.9,
            "intensity_range_min": 0.7,
            "intensity_range_max": 1.0,
            "keywords": ["史诗", "宏大", "壮丽", "恢弘", "磅礴", "雄伟", "庄严"],
            "emotion_tags": ["宏大", "震撼", "庄严", "壮丽"],
            "scene_types": ["custom"],
            "generation_params": {
                "style": "epic orchestral",
                "instruments": ["full_orchestra", "choir", "timpani"],
                "mood": "epic"
            },
            "post_processing_params": {
                "wide_stereo": True,
                "dynamic_range": 0.8
            },
            "is_system": True,
            "is_public": True
        }
    ]
    
    created_count = 0
    for template_data in templates:
        # 检查是否已存在
        existing = db_session.query(MusicStyleTemplate).filter(
            MusicStyleTemplate.name == template_data["name"]
        ).first()
        
        if not existing:
            template = MusicStyleTemplate(**template_data)
            db_session.add(template)
            created_count += 1
            logger.info(f"创建风格模板: {template_data['display_name']}")
        else:
            logger.info(f"风格模板已存在: {template_data['display_name']}")
    
    if created_count > 0:
        db_session.commit()
        logger.info(f"成功创建 {created_count} 个风格模板")
    
    return created_count


def create_system_settings(db_session):
    """创建系统设置"""
    
    settings = [
        {
            "setting_key": "music_generation_enabled",
            "setting_value": "true",
            "setting_type": "boolean",
            "display_name": "启用音乐生成",
            "description": "是否启用音乐生成功能",
            "category": "general",
            "default_value": "true",
            "is_system": True
        },
        {
            "setting_key": "default_music_duration",
            "setting_value": "30",
            "setting_type": "integer",
            "display_name": "默认音乐时长",
            "description": "默认生成的音乐时长（秒）",
            "category": "generation",
            "validation_rules": {"min": 10, "max": 300},
            "default_value": "30",
            "is_system": True
        },
        {
            "setting_key": "default_volume_level",
            "setting_value": "-12.0",
            "setting_type": "float",
            "display_name": "默认音量等级",
            "description": "默认音乐音量等级（dB）",
            "category": "generation",
            "validation_rules": {"min": -30.0, "max": 0.0},
            "default_value": "-12.0",
            "is_system": True
        },
        {
            "setting_key": "max_concurrent_generations",
            "setting_value": "2",
            "setting_type": "integer",
            "display_name": "最大并发生成数",
            "description": "同时进行的音乐生成任务数量上限",
            "category": "performance",
            "validation_rules": {"min": 1, "max": 10},
            "default_value": "2",
            "is_system": True
        },
        {
            "setting_key": "songgeneration_service_url",
            "setting_value": "http://localhost:7862",
            "setting_type": "string",
            "display_name": "SongGeneration服务地址",
            "description": "SongGeneration服务的URL地址",
            "category": "service",
            "default_value": "http://localhost:7862",
            "is_system": True
        },
        {
            "setting_key": "music_output_format",
            "setting_value": "wav",
            "setting_type": "string",
            "display_name": "音乐输出格式",
            "description": "生成音乐的文件格式",
            "category": "generation",
            "validation_rules": {"choices": ["wav", "mp3", "flac"]},
            "default_value": "wav",
            "is_system": True
        },
        {
            "setting_key": "enable_auto_cleanup",
            "setting_value": "true",
            "setting_type": "boolean",
            "display_name": "启用自动清理",
            "description": "是否自动清理旧的音乐生成记录",
            "category": "maintenance",
            "default_value": "true",
            "is_system": True
        },
        {
            "setting_key": "cleanup_max_age_days",
            "setting_value": "30",
            "setting_type": "integer",
            "display_name": "清理最大保留天数",
            "description": "自动清理时保留记录的最大天数",
            "category": "maintenance",
            "validation_rules": {"min": 7, "max": 365},
            "default_value": "30",
            "is_system": True
        },
        {
            "setting_key": "enable_usage_analytics",
            "setting_value": "true",
            "setting_type": "boolean",
            "display_name": "启用使用分析",
            "description": "是否收集音乐生成使用统计",
            "category": "analytics",
            "default_value": "true",
            "is_system": True
        },
        {
            "setting_key": "music_quality_threshold",
            "setting_value": "0.7",
            "setting_type": "float",
            "display_name": "音乐质量阈值",
            "description": "音乐质量评分的最低阈值",
            "category": "quality",
            "validation_rules": {"min": 0.0, "max": 1.0},
            "default_value": "0.7",
            "is_system": True
        }
    ]
    
    created_count = 0
    for setting_data in settings:
        # 检查是否已存在
        existing = db_session.query(MusicGenerationSettings).filter(
            MusicGenerationSettings.setting_key == setting_data["setting_key"]
        ).first()
        
        if not existing:
            setting = MusicGenerationSettings(**setting_data)
            db_session.add(setting)
            created_count += 1
            logger.info(f"创建系统设置: {setting_data['display_name']}")
        else:
            # 更新现有设置
            for key, value in setting_data.items():
                if key != "setting_key":
                    setattr(existing, key, value)
            logger.info(f"更新系统设置: {setting_data['display_name']}")
    
    if created_count > 0 or len(settings) > 0:
        db_session.commit()
        logger.info(f"成功处理 {len(settings)} 个系统设置，新创建 {created_count} 个")
    
    return created_count


def main():
    """主函数"""
    try:
        # 创建数据库连接
        database_url = settings.database_url
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        db_session = SessionLocal()
        
        logger.info("开始创建音乐生成测试数据...")
        
        # 创建风格模板
        template_count = create_style_templates(db_session)
        
        # 创建系统设置
        setting_count = create_system_settings(db_session)
        
        db_session.close()
        
        logger.info("音乐生成测试数据创建完成！")
        logger.info(f"创建风格模板: {template_count} 个")
        logger.info(f"创建系统设置: {setting_count} 个")
        
        return True
        
    except Exception as e:
        logger.error(f"创建测试数据失败: {str(e)}")
        if 'db_session' in locals():
            db_session.rollback()
            db_session.close()
        return False


if __name__ == "__main__":
    success = main()
    if success:
        logger.info("✅ 音乐生成测试数据创建成功")
        sys.exit(0)
    else:
        logger.error("❌ 音乐生成测试数据创建失败")
        sys.exit(1) 