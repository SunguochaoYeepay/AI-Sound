"""
添加角色外貌特征字段
Create Date: 2025-01-14
"""

from sqlalchemy import text
from app.database import get_db
import logging

logger = logging.getLogger(__name__)

def upgrade():
    """添加角色外貌特征字段"""
    db = next(get_db())
    
    try:
        # 添加外貌特征相关字段 - PostgreSQL语法
        alter_statements = [
            "ALTER TABLE characters ADD COLUMN IF NOT EXISTS age_range VARCHAR(20)",
            "ALTER TABLE characters ADD COLUMN IF NOT EXISTS build_type VARCHAR(20)", 
            "ALTER TABLE characters ADD COLUMN IF NOT EXISTS clothing_style VARCHAR(20)",
            "ALTER TABLE characters ADD COLUMN IF NOT EXISTS distinctive_features TEXT",
            "ALTER TABLE characters ADD COLUMN IF NOT EXISTS appearance_description TEXT",
            "ALTER TABLE characters ADD COLUMN IF NOT EXISTS avatar_prompt TEXT",
            "ALTER TABLE characters ADD COLUMN IF NOT EXISTS consistency_tag VARCHAR(100)"
        ]
        
        # 添加注释的单独语句
        comment_statements = [
            "COMMENT ON COLUMN characters.age_range IS '年龄范围: child, young, middle, elder'",
            "COMMENT ON COLUMN characters.build_type IS '身材类型: slim, average, sturdy, plump'",
            "COMMENT ON COLUMN characters.clothing_style IS '服装风格: ancient, modern, formal, casual'",
            "COMMENT ON COLUMN characters.distinctive_features IS '特殊外貌特征'",
            "COMMENT ON COLUMN characters.appearance_description IS '完整外貌描述'",
            "COMMENT ON COLUMN characters.avatar_prompt IS '头像生成AI提示词'",
            "COMMENT ON COLUMN characters.consistency_tag IS '视觉一致性标签'"
        ]
        
        # 执行字段添加
        for statement in alter_statements:
            try:
                db.execute(text(statement))
                logger.info(f"执行成功: {statement}")
            except Exception as e:
                if "already exists" in str(e) or "duplicate column" in str(e).lower():
                    logger.info(f"字段已存在，跳过: {statement}")
                else:
                    raise e
        
        # 执行注释添加
        for statement in comment_statements:
            try:
                db.execute(text(statement))
                logger.info(f"注释添加成功: {statement}")
            except Exception as e:
                logger.warning(f"注释添加失败: {statement}, 错误: {str(e)}")
        
        db.commit()
        logger.info("角色外貌特征字段添加完成")
        
    except Exception as e:
        db.rollback()
        logger.error(f"添加角色外貌特征字段失败: {str(e)}")
        raise e
    finally:
        db.close()

def downgrade():
    """移除角色外貌特征字段"""
    db = next(get_db())
    
    try:
        # 移除外貌特征相关字段
        drop_statements = [
            "ALTER TABLE characters DROP COLUMN age_range",
            "ALTER TABLE characters DROP COLUMN build_type",
            "ALTER TABLE characters DROP COLUMN clothing_style", 
            "ALTER TABLE characters DROP COLUMN distinctive_features",
            "ALTER TABLE characters DROP COLUMN appearance_description",
            "ALTER TABLE characters DROP COLUMN avatar_prompt",
            "ALTER TABLE characters DROP COLUMN consistency_tag"
        ]
        
        for statement in drop_statements:
            try:
                db.execute(text(statement))
                logger.info(f"执行成功: {statement}")
            except Exception as e:
                if "doesn't exist" in str(e):
                    logger.info(f"字段不存在，跳过: {statement}")
                else:
                    logger.warning(f"移除字段失败: {statement}, 错误: {str(e)}")
        
        db.commit()
        logger.info("角色外貌特征字段移除完成")
        
    except Exception as e:
        db.rollback()
        logger.error(f"移除角色外貌特征字段失败: {str(e)}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    print("正在执行角色外貌特征字段迁移...")
    upgrade()
    print("迁移完成！")