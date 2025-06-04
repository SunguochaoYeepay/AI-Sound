#!/usr/bin/env python3
"""
初始化测试数据脚本
"""
import os
import sys

# 添加app目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from database import SessionLocal, init_db
from models import VoiceProfile
from datetime import datetime

def init_test_data():
    print("=== 初始化测试数据 ===")
    
    try:
        # 确保数据库已初始化
        init_db()
        
        db = SessionLocal()
        
        # 清空现有数据
        db.query(VoiceProfile).delete()
        db.commit()
        
        # 创建测试声音档案
        test_voices = [
            {
                "name": "温柔女声",
                "description": "温柔甜美的女性声音",
                "type": "female",
                "quality_score": 8.5,
                "status": "active",
                "color": "#ff6b9d"
            },
            {
                "name": "磁性男声", 
                "description": "低沉有磁性的男性声音",
                "type": "male",
                "quality_score": 8.8,
                "status": "active",
                "color": "#4e73df"
            },
            {
                "name": "专业主播",
                "description": "专业播音员声音",
                "type": "female",
                "quality_score": 9.2,
                "status": "active", 
                "color": "#1cc88a"
            },
            {
                "name": "老者声音",
                "description": "成熟稳重的老者声音",
                "type": "male",
                "quality_score": 8.0,
                "status": "active",
                "color": "#f6c23e"
            },
            {
                "name": "童声",
                "description": "清脆可爱的儿童声音",
                "type": "child", 
                "quality_score": 7.8,
                "status": "active",
                "color": "#e74a3b"
            }
        ]
        
        created_count = 0
        for voice_data in test_voices:
            voice = VoiceProfile(
                name=voice_data["name"],
                description=voice_data["description"],
                type=voice_data["type"],
                quality_score=voice_data["quality_score"],
                status=voice_data["status"],
                color=voice_data["color"],
                usage_count=0,
                parameters='{"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}',
                tags='[]',
                reference_audio_path='',
                latent_file_path='',
                sample_audio_path=''
            )
            
            db.add(voice)
            created_count += 1
            print(f"创建声音档案: {voice_data['name']} ({voice_data['type']})")
        
        db.commit()
        print(f"✅ 成功创建 {created_count} 个测试声音档案")
        
        # 验证数据
        voices = db.query(VoiceProfile).all()
        print(f"数据库中现有 {len(voices)} 个声音档案:")
        for voice in voices:
            print(f"  ID: {voice.id}, Name: {voice.name}, Type: {voice.type}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 初始化测试数据失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    init_test_data() 