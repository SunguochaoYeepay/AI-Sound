#!/usr/bin/env python3
"""
直接检查SQLite数据库
"""
import sqlite3
import os

def check_db_direct():
    print("🔍 === 直接检查数据库 ===")
    
    db_path = "data/database.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    print(f"📋 数据库文件: {db_path}")
    print(f"📏 文件大小: {os.path.getsize(db_path)} 字节")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📋 数据库表: {[t[0] for t in tables]}")
        
        # 检查项目表
        if "novel_projects" in [t[0] for t in tables]:
            cursor.execute("SELECT COUNT(*) FROM novel_projects")
            count = cursor.fetchone()[0]
            print(f"📋 项目总数: {count}")
            
            if count > 0:
                cursor.execute("SELECT id, name, character_mapping FROM novel_projects ORDER BY id DESC LIMIT 5")
                projects = cursor.fetchall()
                print("📋 最新项目:")
                for p in projects:
                    print(f"  ID: {p[0]}, 名称: {p[1]}, 映射: {p[2]}")
        
        # 检查声音档案表  
        if "voice_profiles" in [t[0] for t in tables]:
            cursor.execute("SELECT COUNT(*) FROM voice_profiles")
            count = cursor.fetchone()[0]
            print(f"🎵 声音档案总数: {count}")
            
            if count > 0:
                cursor.execute("SELECT id, name, reference_audio_path FROM voice_profiles LIMIT 3")
                voices = cursor.fetchall()
                print("🎵 声音档案:")
                for v in voices:
                    print(f"  ID: {v[0]}, 名称: {v[1]}, 音频: {v[2] is not None}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")

if __name__ == "__main__":
    check_db_direct() 