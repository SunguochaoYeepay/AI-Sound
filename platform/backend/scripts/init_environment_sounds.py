#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境音管理模块初始化数据脚本
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.environment_sound import (
    EnvironmentSoundCategory, EnvironmentSoundTag, EnvironmentSoundPreset
)

def create_categories():
    """创建环境音分类"""
    categories = [
        {
            "name": "自然音效",
            "description": "来自大自然的各种声音，如雨声、风声、鸟叫等",
            "icon": "leaf",
            "color": "#52c41a",
            "sort_order": 100
        },
        {
            "name": "城市环境",
            "description": "城市生活中的各种环境音，如交通、人群、建筑等",
            "icon": "building",
            "color": "#1890ff",
            "sort_order": 90
        },
        {
            "name": "室内环境",
            "description": "室内场景的环境音，如咖啡厅、图书馆、办公室等",
            "icon": "home",
            "color": "#fa8c16",
            "sort_order": 80
        },
        {
            "name": "机械音效",
            "description": "各种机械设备产生的声音",
            "icon": "setting",
            "color": "#722ed1",
            "sort_order": 70
        },
        {
            "name": "动物声音",
            "description": "各种动物的叫声和活动声音",
            "icon": "bug",
            "color": "#13c2c2",
            "sort_order": 60
        },
        {
            "name": "水声音效",
            "description": "与水相关的各种声音，如海浪、河流、瀑布等",
            "icon": "water",
            "color": "#1677ff",
            "sort_order": 50
        },
        {
            "name": "天气音效",
            "description": "各种天气现象产生的声音",
            "icon": "cloud",
            "color": "#8c8c8c",
            "sort_order": 40
        },
        {
            "name": "音乐环境",
            "description": "背景音乐和音乐环境音效",
            "icon": "sound",
            "color": "#eb2f96",
            "sort_order": 30
        }
    ]
    
    db = SessionLocal()
    try:
        for cat_data in categories:
            # 检查是否已存在
            existing = db.query(EnvironmentSoundCategory).filter(
                EnvironmentSoundCategory.name == cat_data["name"]
            ).first()
            
            if not existing:
                category = EnvironmentSoundCategory(**cat_data)
                db.add(category)
                print(f"创建分类: {cat_data['name']}")
            else:
                print(f"分类已存在: {cat_data['name']}")
        
        db.commit()
        print("✅ 分类创建完成")
    except Exception as e:
        db.rollback()
        print(f"❌ 创建分类失败: {e}")
    finally:
        db.close()

def create_tags():
    """创建环境音标签"""
    tags = [
        # 情绪标签
        {"name": "放松", "color": "#52c41a", "description": "有助于放松和减压的声音"},
        {"name": "专注", "color": "#1890ff", "description": "有助于集中注意力的声音"},
        {"name": "睡眠", "color": "#722ed1", "description": "适合睡眠和休息的声音"},
        {"name": "冥想", "color": "#13c2c2", "description": "适合冥想和静心的声音"},
        {"name": "活力", "color": "#fa8c16", "description": "充满活力和能量的声音"},
        
        # 场景标签
        {"name": "户外", "color": "#52c41a", "description": "户外环境的声音"},
        {"name": "室内", "color": "#fa541c", "description": "室内环境的声音"},
        {"name": "办公", "color": "#2f54eb", "description": "办公环境的声音"},
        {"name": "家居", "color": "#eb2f96", "description": "家居环境的声音"},
        {"name": "旅行", "color": "#faad14", "description": "旅行场景的声音"},
        
        # 时间标签
        {"name": "白天", "color": "#fadb14", "description": "白天时段的声音"},
        {"name": "夜晚", "color": "#1f1f1f", "description": "夜晚时段的声音"},
        {"name": "清晨", "color": "#ffa39e", "description": "清晨时段的声音"},
        {"name": "黄昏", "color": "#ff7a45", "description": "黄昏时段的声音"},
        
        # 强度标签
        {"name": "轻柔", "color": "#b7eb8f", "description": "音量较小的轻柔声音"},
        {"name": "中等", "color": "#87d068", "description": "音量适中的声音"},
        {"name": "强烈", "color": "#ff4d4f", "description": "音量较大的强烈声音"},
        
        # 特殊标签
        {"name": "循环", "color": "#36cfc9", "description": "适合循环播放的声音"},
        {"name": "单次", "color": "#9254de", "description": "适合单次播放的声音"},
        {"name": "高清", "color": "#f759ab", "description": "高质量音频"},
        {"name": "立体声", "color": "#40a9ff", "description": "立体声效果"}
    ]
    
    db = SessionLocal()
    try:
        for tag_data in tags:
            # 检查是否已存在
            existing = db.query(EnvironmentSoundTag).filter(
                EnvironmentSoundTag.name == tag_data["name"]
            ).first()
            
            if not existing:
                tag = EnvironmentSoundTag(**tag_data)
                db.add(tag)
                print(f"创建标签: {tag_data['name']}")
            else:
                print(f"标签已存在: {tag_data['name']}")
        
        db.commit()
        print("✅ 标签创建完成")
    except Exception as e:
        db.rollback()
        print(f"❌ 创建标签失败: {e}")
    finally:
        db.close()

def create_presets():
    """创建环境音预设"""
    db = SessionLocal()
    try:
        # 获取分类ID
        categories = {cat.name: cat.id for cat in db.query(EnvironmentSoundCategory).all()}
        
        presets = [
            {
                "name": "雨声放松",
                "description": "轻柔的雨声，适合放松和睡眠",
                "category_id": categories.get("自然音效"),
                "default_duration": 15.0,
                "default_steps": 50,
                "default_cfg_scale": 3.5,
                "prompt_templates": [
                    "Gentle rain falling on leaves",
                    "Light rainfall on a quiet forest",
                    "Soft rain drops on window glass"
                ],
                "example_prompts": [
                    "Heavy rain falling on leaves with distant thunder",
                    "Light rain on a metal roof with wind",
                    "Gentle rainfall in a peaceful garden"
                ]
            },
            {
                "name": "海浪声音",
                "description": "海浪拍打海岸的声音，非常放松",
                "category_id": categories.get("水声音效"),
                "default_duration": 20.0,
                "default_steps": 60,
                "default_cfg_scale": 4.0,
                "prompt_templates": [
                    "Ocean waves crashing on beach",
                    "Gentle waves on sandy shore",
                    "Powerful waves hitting rocks"
                ],
                "example_prompts": [
                    "Ocean waves crashing on rocks with seagulls",
                    "Gentle waves lapping on a sandy beach",
                    "Strong waves during a storm at sea"
                ]
            },
            {
                "name": "鸟叫声音",
                "description": "清晨鸟儿的歌声，充满生机",
                "category_id": categories.get("动物声音"),
                "default_duration": 12.0,
                "default_steps": 40,
                "default_cfg_scale": 3.0,
                "prompt_templates": [
                    "Birds chirping in forest",
                    "Morning bird songs",
                    "Various birds singing"
                ],
                "example_prompts": [
                    "Birds chirping in a forest with gentle wind",
                    "Morning bird songs in a peaceful garden",
                    "Various birds singing at dawn"
                ]
            },
            {
                "name": "咖啡厅环境",
                "description": "咖啡厅的背景声音，适合工作和学习",
                "category_id": categories.get("室内环境"),
                "default_duration": 25.0,
                "default_steps": 55,
                "default_cfg_scale": 3.8,
                "prompt_templates": [
                    "Coffee shop ambient sounds",
                    "Cafe background noise",
                    "Busy coffee shop atmosphere"
                ],
                "example_prompts": [
                    "Coffee shop with quiet conversations and espresso machine",
                    "Busy cafe with people talking and music",
                    "Peaceful coffee shop with light background chatter"
                ]
            },
            {
                "name": "城市街道",
                "description": "城市街道的环境音，充满都市气息",
                "category_id": categories.get("城市环境"),
                "default_duration": 18.0,
                "default_steps": 45,
                "default_cfg_scale": 3.2,
                "prompt_templates": [
                    "City street ambient sounds",
                    "Urban traffic noise",
                    "Busy street atmosphere"
                ],
                "example_prompts": [
                    "City street with cars and pedestrians",
                    "Busy urban intersection with traffic",
                    "Quiet city street in the evening"
                ]
            },
            {
                "name": "风声音效",
                "description": "各种风声，从轻柔到强烈",
                "category_id": categories.get("天气音效"),
                "default_duration": 14.0,
                "default_steps": 35,
                "default_cfg_scale": 2.8,
                "prompt_templates": [
                    "Wind blowing through trees",
                    "Gentle breeze sounds",
                    "Strong wind effects"
                ],
                "example_prompts": [
                    "Wind blowing through trees in a forest",
                    "Gentle breeze on a summer day",
                    "Strong wind during a storm"
                ]
            }
        ]
        
        for preset_data in presets:
            # 检查是否已存在
            existing = db.query(EnvironmentSoundPreset).filter(
                EnvironmentSoundPreset.name == preset_data["name"]
            ).first()
            
            if not existing:
                # 转换JSON字段
                preset_data["prompt_templates"] = json.dumps(preset_data["prompt_templates"])
                preset_data["example_prompts"] = json.dumps(preset_data["example_prompts"])
                
                preset = EnvironmentSoundPreset(**preset_data)
                db.add(preset)
                print(f"创建预设: {preset_data['name']}")
            else:
                print(f"预设已存在: {preset_data['name']}")
        
        db.commit()
        print("✅ 预设创建完成")
    except Exception as e:
        db.rollback()
        print(f"❌ 创建预设失败: {e}")
    finally:
        db.close()

def main():
    """主函数"""
    print("🚀 开始初始化环境音管理数据...")
    print("=" * 50)
    
    # 创建分类
    print("\n📁 创建环境音分类...")
    create_categories()
    
    # 创建标签
    print("\n🏷️  创建环境音标签...")
    create_tags()
    
    # 创建预设
    print("\n⚙️  创建环境音预设...")
    create_presets()
    
    print("\n" + "=" * 50)
    print("✅ 环境音管理数据初始化完成！")
    print("\n📋 已创建的内容:")
    print("   - 8个环境音分类")
    print("   - 20个环境音标签")
    print("   - 6个环境音预设模板")
    print("\n🎯 下一步:")
    print("   1. 启动TangoFlux API服务 (端口7930)")
    print("   2. 访问前端环境音管理页面")
    print("   3. 开始生成你的第一个环境音！")

if __name__ == "__main__":
    main() 