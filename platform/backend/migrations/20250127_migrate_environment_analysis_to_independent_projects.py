"""
迁移环境音分析结果到独立项目
将合成项目config中的environment_analysis迁移到environment_projects表
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.models.novel_project import NovelProject
from app.models.environment_generation import EnvironmentProject
from sqlalchemy.orm import Session

def migrate_environment_analysis():
    """迁移环境音分析结果"""
    print("🚀 开始迁移环境音分析结果...")
    
    db = next(get_db())
    
    try:
        # 查找所有有环境音分析结果的合成项目
        projects_with_env = db.query(NovelProject).filter(
            NovelProject.config.isnot(None)
        ).all()
        
        # 过滤出有environment_analysis的项目
        projects_with_env = [
            project for project in projects_with_env 
            if project.config and 'environment_analysis' in project.config
        ]
        
        print(f"📊 找到 {len(projects_with_env)} 个有环境音分析的项目")
        
        migrated_count = 0
        
        for project in projects_with_env:
            try:
                # 检查是否已有对应的环境音项目
                existing_env_project = db.query(EnvironmentProject).filter(
                    EnvironmentProject.novel_project_id == project.id
                ).first()
                
                if existing_env_project:
                    print(f"⚠️ 项目 {project.id} 已有环境音项目，跳过")
                    continue
                
                # 提取环境音分析结果
                env_analysis = project.config.get('environment_analysis', {})
                if not env_analysis:
                    continue
                
                # 创建新的环境音项目
                env_project = EnvironmentProject(
                    novel_project_id=project.id,
                    name=f"环境音分析_{project.name}",
                    description=f"基于项目 '{project.name}' 的环境音分析",
                    status="analyzed",
                    analysis_result=env_analysis.get('analysis_result', {}),
                    matching_result={
                        'analysis_stats': env_analysis.get('analysis_stats', {}),
                        'session_stage': env_analysis.get('session_stage', 'analyzed')
                    },
                    chapter_ids=project.config.get('chapter_ids', []),
                    analysis_options=project.config.get('analysis_options', {}),
                    book_name=project.config.get('book_name', '未知书籍'),
                    chapter_name=project.config.get('chapter_name', '未知章节'),
                    created_at=project.created_at,
                    updated_at=datetime.utcnow()
                )
                
                db.add(env_project)
                migrated_count += 1
                
                print(f"✅ 迁移项目 {project.id}: {project.name}")
                
            except Exception as e:
                print(f"❌ 迁移项目 {project.id} 失败: {str(e)}")
                continue
        
        db.commit()
        print(f"🎉 迁移完成！成功迁移 {migrated_count} 个项目")
        
        # 清理合成项目中的环境音配置
        print("🧹 清理合成项目中的环境音配置...")
        cleaned_count = 0
        
        for project in projects_with_env:
            try:
                if 'environment_analysis' in project.config:
                    del project.config['environment_analysis']
                    # 标记JSON字段已修改
                    from sqlalchemy.orm import attributes
                    attributes.flag_modified(project, 'config')
                    cleaned_count += 1
            except Exception as e:
                print(f"❌ 清理项目 {project.id} 失败: {str(e)}")
                continue
        
        db.commit()
        print(f"🧹 清理完成！清理了 {cleaned_count} 个项目")
        
    except Exception as e:
        print(f"❌ 迁移失败: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_environment_analysis()
