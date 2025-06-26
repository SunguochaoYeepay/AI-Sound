#!/usr/bin/env python3
"""测试音乐生成数据库服务"""

from app.services.music_generation_db_service import get_music_generation_db_service
from app.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_music_db_service():
    """测试音乐生成数据库服务"""
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        db_service = get_music_generation_db_service(db)
        
        # 测试获取风格模板
        templates = db_service.get_style_templates()
        print(f'找到 {len(templates)} 个风格模板:')
        for template in templates[:3]:  # 只显示前3个
            print(f'  - {template.display_name} ({template.name})')
        
        # 测试获取系统设置
        enabled = db_service.get_setting('music_generation_enabled')
        print(f'音乐生成功能启用状态: {enabled}')
        
        # 测试创建生成任务
        task = db_service.create_generation_task(
            chapter_id="test_chapter_001",
            content="这是一个激烈的战斗场景，刀光剑影，血雨腥风。",
            target_duration=30,
            custom_style="battle"
        )
        print(f'创建测试任务: {task.task_id}')
        
        # 测试获取任务
        retrieved_task = db_service.get_generation_task(task.task_id)
        print(f'获取任务成功: {retrieved_task.content[:20]}...')
        
        # 测试统计信息
        stats = db_service.get_generation_stats()
        print(f'生成统计: 总任务数={stats["total_generations"]}, 成功率={stats["success_rate"]:.2f}')
        
        print('✅ 数据库服务测试成功')
        
    except Exception as e:
        print(f'❌ 测试失败: {e}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_music_db_service() 