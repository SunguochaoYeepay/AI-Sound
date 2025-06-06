#!/usr/bin/env python3
"""
验证数据迁移结果
"""
from database import SessionLocal
from models import VoiceProfile, SystemLog, UsageStats

def verify_migration():
    print("🔍 === 验证PostgreSQL数据迁移结果 ===")
    
    db = SessionLocal()
    
    # 检查声音档案
    voices = db.query(VoiceProfile).all()
    print(f"🎵 声音档案: {len(voices)} 个")
    for voice in voices:
        print(f"   - {voice.name} ({voice.type}) - 质量评分: {voice.quality_score}")
    
    # 检查系统日志
    logs_count = db.query(SystemLog).count()
    recent_logs = db.query(SystemLog).order_by(SystemLog.id.desc()).limit(3).all()
    print(f"\n📋 系统日志: {logs_count} 条")
    for log in recent_logs:
        print(f"   - [{log.level}] {log.message[:50]}...")
    
    # 检查统计数据
    stats_count = db.query(UsageStats).count()
    stats = db.query(UsageStats).all()
    print(f"\n📊 统计数据: {stats_count} 条")
    for stat in stats:
        print(f"   - {stat.date}: 请求{stat.total_requests}次, 成功{stat.successful_requests}次")
    
    db.close()
    print("\n✅ 数据迁移验证完成!")

if __name__ == "__main__":
    verify_migration()