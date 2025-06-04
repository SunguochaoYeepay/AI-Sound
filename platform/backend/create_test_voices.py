#!/usr/bin/env python3
"""
创建测试声音档案
"""
import sqlite3
from datetime import datetime

def create_test_voices():
    print("=== 创建测试声音档案 ===")
    
    try:
        # 连接数据库
        conn = sqlite3.connect('app/database.db')
        cursor = conn.cursor()
        
        # 检查表是否存在，如果不存在则创建
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS voice_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                type VARCHAR(20) NOT NULL,
                reference_audio_path VARCHAR(500),
                latent_file_path VARCHAR(500),
                sample_audio_path VARCHAR(500),
                parameters TEXT NOT NULL DEFAULT '{"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}',
                quality_score FLOAT DEFAULT 3.0,
                usage_count INTEGER DEFAULT 0,
                last_used DATETIME,
                color VARCHAR(20) DEFAULT '#06b6d4',
                tags TEXT DEFAULT '[]',
                status VARCHAR(20) DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 清空现有数据
        cursor.execute("DELETE FROM voice_profiles")
        
        # 测试声音档案数据
        test_voices = [
            ("温柔女声", "温柔甜美的女性声音", "female", None, None, None, '{"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}', 8.5, 0, None, "#ff6b9d", '[]', "active"),
            ("磁性男声", "低沉有磁性的男性声音", "male", None, None, None, '{"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}', 8.8, 0, None, "#4e73df", '[]', "active"),
            ("专业主播", "专业播音员声音", "female", None, None, None, '{"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}', 9.2, 0, None, "#1cc88a", '[]', "active"),
            ("老者声音", "成熟稳重的老者声音", "male", None, None, None, '{"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}', 8.0, 0, None, "#f6c23e", '[]', "active"),
            ("童声", "清脆可爱的儿童声音", "child", None, None, None, '{"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}', 7.8, 0, None, "#e74a3b", '[]', "active")
        ]
        
        # 插入数据
        created_count = 0
        for voice_data in test_voices:
            cursor.execute("""
                INSERT INTO voice_profiles 
                (name, description, type, reference_audio_path, latent_file_path, sample_audio_path, 
                 parameters, quality_score, usage_count, last_used, color, tags, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, voice_data)
            created_count += 1
            print(f"创建声音档案: {voice_data[0]} ({voice_data[2]})")
        
        conn.commit()
        print(f"✅ 成功创建 {created_count} 个测试声音档案")
        
        # 验证数据
        cursor.execute("SELECT id, name, type FROM voice_profiles")
        voices = cursor.fetchall()
        print(f"数据库中现有 {len(voices)} 个声音档案:")
        for voice in voices:
            print(f"  ID: {voice[0]}, Name: {voice[1]}, Type: {voice[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 创建测试声音档案失败: {e}")

if __name__ == "__main__":
    create_test_voices() 