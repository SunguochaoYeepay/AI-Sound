#!/usr/bin/env python3
"""
数据库检查脚本
"""
import os
import sys

# 添加app目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from database import SessionLocal
from models import VoiceProfile

def check_database():
    print("=== 检查数据库声音数据 ===")
    
    try:
        db = SessionLocal()
        voices = db.query(VoiceProfile).all()
        
        print(f"总计声音数量: {len(voices)}")
        print("===声音列表===")
        
        for voice in voices:
            print(f"ID: {voice.id}")
            print(f"  Name: {voice.name}")
            print(f"  Type: {voice.type}")
            print(f"  Quality: {voice.quality_score}")
            print(f"  Status: {voice.status}")
            print(f"  Usage Count: {voice.usage_count}")
            print(f"  Created: {voice.created_at}")
            print(f"  Color: {voice.color}")
            print("---")
            
        db.close()
        
    except Exception as e:
        print(f"数据库检查错误: {e}")

if __name__ == "__main__":
    check_database() 