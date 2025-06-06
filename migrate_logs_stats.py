#!/usr/bin/env python3
"""
系统日志和统计数据迁移脚本
"""
import psycopg2
import sqlite3

def migrate_logs_and_stats():
    print("🚀 开始迁移系统日志和统计数据...")
    
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
    
    # 迁移system_logs
    print("\n📋 迁移系统日志...")
    sqlite_cursor.execute("SELECT * FROM system_logs")
    logs = sqlite_cursor.fetchall()
    
    sqlite_cursor.execute("PRAGMA table_info(system_logs)")
    log_columns = [col[1] for col in sqlite_cursor.fetchall()]
    
    print(f"📊 找到 {len(logs)} 条系统日志")
    
    log_success = 0
    for log in logs:
        log_dict = dict(zip(log_columns, log))
        
        try:
            pg_cursor.execute("""
                INSERT INTO system_logs (level, message, module, details, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                log_dict['level'], log_dict['message'], log_dict['module'],
                log_dict['details'], log_dict['timestamp']
            ))
            log_success += 1
        except Exception as e:
            print(f"❌ 日志迁移失败: {e}")
    
    print(f"✅ 系统日志迁移: {log_success}/{len(logs)}")
    
    # 迁移usage_stats
    print("\n📊 迁移使用统计...")
    sqlite_cursor.execute("SELECT * FROM usage_stats")
    stats = sqlite_cursor.fetchall()
    
    sqlite_cursor.execute("PRAGMA table_info(usage_stats)")
    stat_columns = [col[1] for col in sqlite_cursor.fetchall()]
    
    print(f"📊 找到 {len(stats)} 条统计数据")
    
    stat_success = 0
    for stat in stats:
        stat_dict = dict(zip(stat_columns, stat))
        
        try:
            pg_cursor.execute("""
                INSERT INTO usage_stats (date, total_requests, successful_requests, failed_requests, 
                                       total_processing_time, audio_files_generated)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (date) DO UPDATE SET
                total_requests = EXCLUDED.total_requests,
                successful_requests = EXCLUDED.successful_requests,
                failed_requests = EXCLUDED.failed_requests,
                total_processing_time = EXCLUDED.total_processing_time,
                audio_files_generated = EXCLUDED.audio_files_generated
            """, (
                stat_dict['date'], stat_dict['total_requests'], 
                stat_dict['successful_requests'], stat_dict['failed_requests'],
                stat_dict['total_processing_time'], stat_dict['audio_files_generated']
            ))
            stat_success += 1
        except Exception as e:
            print(f"❌ 统计迁移失败: {e}")
    
    print(f"✅ 统计数据迁移: {stat_success}/{len(stats)}")
    
    pg_conn.commit()
    pg_conn.close()
    sqlite_conn.close()
    
    print(f"\n🎉 全部迁移完成!")
    print(f"   - 系统日志: {log_success} 条")
    print(f"   - 统计数据: {stat_success} 条")

if __name__ == "__main__":
    migrate_logs_and_stats()