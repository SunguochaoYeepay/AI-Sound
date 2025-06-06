#!/usr/bin/env python3
"""
声音档案迁移脚本
"""
import psycopg2
import sqlite3

def migrate_voices():
    print("🚀 开始迁移声音档案...")
    
    # 连接SQLite
    sqlite_conn = sqlite3.connect('/app/data/database.db')
    sqlite_cursor = sqlite_conn.cursor()
    
    # 连接PostgreSQL
    pg_conn = psycopg2.connect(
        host='database',
        database='ai_sound', 
        user='ai_sound_user',
        password='ai_sound_password'
    )
    pg_cursor = pg_conn.cursor()
    
    # 获取SQLite中的声音档案
    sqlite_cursor.execute("SELECT * FROM voice_profiles")
    voices = sqlite_cursor.fetchall()
    
    sqlite_cursor.execute("PRAGMA table_info(voice_profiles)")
    columns = [col[1] for col in sqlite_cursor.fetchall()]
    
    print(f"📊 找到 {len(voices)} 个声音档案")
    
    success_count = 0
    for voice in voices:
        voice_dict = dict(zip(columns, voice))
        
        # 修正文件路径
        if voice_dict['reference_audio_path']:
            voice_dict['reference_audio_path'] = voice_dict['reference_audio_path'].replace('..\\data\\uploads\\', '/app/data/uploads/').replace('\\', '/')
        if voice_dict['latent_file_path']:
            voice_dict['latent_file_path'] = voice_dict['latent_file_path'].replace('..\\data\\uploads\\', '/app/data/uploads/').replace('\\', '/')
        
        try:
            pg_cursor.execute("""
                INSERT INTO voice_profiles (name, description, type, reference_audio_path, latent_file_path, 
                                          sample_audio_path, parameters, quality_score, usage_count, 
                                          last_used, color, tags, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING
            """, (
                voice_dict['name'], voice_dict['description'], voice_dict['type'],
                voice_dict['reference_audio_path'], voice_dict['latent_file_path'], 
                voice_dict['sample_audio_path'], voice_dict['parameters'],
                voice_dict['quality_score'], voice_dict['usage_count'], voice_dict['last_used'],
                voice_dict['color'], voice_dict['tags'], voice_dict['status'],
                voice_dict['created_at'], voice_dict['updated_at']
            ))
            print(f"✅ 迁移声音: {voice_dict['name']}")
            success_count += 1
        except Exception as e:
            print(f"❌ 迁移失败 {voice_dict['name']}: {e}")
    
    pg_conn.commit()
    pg_conn.close()
    sqlite_conn.close()
    
    print(f"🎉 迁移完成! 成功迁移 {success_count}/{len(voices)} 个声音档案")

if __name__ == "__main__":
    migrate_voices()