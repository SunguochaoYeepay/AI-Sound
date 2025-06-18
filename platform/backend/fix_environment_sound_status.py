#!/usr/bin/env python3
"""
直接修复环境音状态的脚本
"""

import psycopg2
import os
from datetime import datetime

def fix_environment_sound_status():
    """修复环境音状态"""
    
    # PostgreSQL连接配置
    db_config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "ai_sound"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "123456")
    }
    
    try:
        # 连接数据库
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # 查询处理中的环境音
        cursor.execute("""
            SELECT id, name, generation_status, created_at 
            FROM environment_sounds 
            WHERE generation_status = 'processing'
        """)
        
        processing_sounds = cursor.fetchall()
        
        if not processing_sounds:
            print("✅ 没有处理中的环境音")
            return
        
        print(f"🔍 发现 {len(processing_sounds)} 个处理中的环境音:")
        
        for sound_id, name, status, created_at in processing_sounds:
            print(f"   ID={sound_id}: {name} (状态: {status}, 创建时间: {created_at})")
        
        # 直接修复，不询问
        print(f"\n🔧 正在将这些环境音状态修改为'failed'...")
        
        # 更新状态为失败
        cursor.execute("""
            UPDATE environment_sounds 
            SET generation_status = 'failed',
                error_message = '手动修复：生成超时或异常' 
            WHERE generation_status = 'processing'
        """)
        
        affected_rows = cursor.rowcount
        conn.commit()
        
        print(f"✅ 成功修复 {affected_rows} 个环境音状态")
        
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_environment_sound_status() 