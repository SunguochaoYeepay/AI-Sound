#!/usr/bin/env python3
"""
创建或更新AudioFile表
将现有音频文件导入数据库
"""

import sys
import os
sys.path.append('app')

from database import engine, SessionLocal
from models import Base, AudioFile, TextSegment, NovelProject
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_audio_table():
    """创建AudioFile表"""
    try:
        logger.info("创建AudioFile表...")
        Base.metadata.create_all(bind=engine)
        logger.info("AudioFile表创建成功!")
        return True
    except Exception as e:
        logger.error(f"创建AudioFile表失败: {str(e)}")
        return False

def sync_existing_audio_files():
    """同步现有音频文件到数据库"""
    db = SessionLocal()
    try:
        audio_dir = "data/audio"
        if not os.path.exists(audio_dir):
            logger.warning(f"音频目录不存在: {audio_dir}")
            return
        
        synced_count = 0
        skipped_count = 0
        
        logger.info("开始同步音频文件...")
        
        for filename in os.listdir(audio_dir):
            if not filename.lower().endswith(('.wav', '.mp3', '.flac', '.m4a')):
                continue
            
            # 检查是否已存在
            existing = db.query(AudioFile).filter(AudioFile.filename == filename).first()
            if existing:
                logger.debug(f"跳过已存在文件: {filename}")
                skipped_count += 1
                continue
            
            file_path = os.path.join(audio_dir, filename)
            try:
                file_size = os.path.getsize(file_path)
                
                # 解析文件名，尝试关联项目和段落
                project_id = None
                segment_id = None
                audio_type = 'unknown'
                text_content = None
                
                if filename.startswith('segment_'):
                    audio_type = 'segment'
                    # 尝试从文件名解析段落ID
                    parts = filename.split('_')
                    if len(parts) >= 2 and parts[1].isdigit():
                        segment_order = int(parts[1])
                        # 查找对应的段落
                        segment = db.query(TextSegment).filter(
                            TextSegment.segment_order == segment_order
                        ).first()
                        if segment:
                            segment_id = segment.id
                            project_id = segment.project_id
                            text_content = segment.text_content
                elif filename.startswith('project_'):
                    audio_type = 'project'
                    # 尝试从文件名解析项目ID
                    parts = filename.split('_')
                    if len(parts) >= 2 and parts[1].isdigit():
                        try:
                            project_id = int(parts[1])
                            # 验证项目是否存在
                            project = db.query(NovelProject).filter(NovelProject.id == project_id).first()
                            if not project:
                                project_id = None
                        except ValueError:
                            pass
                elif filename.startswith('tts_'):
                    audio_type = 'single'
                elif filename.startswith('test_'):
                    audio_type = 'test'
                
                # 获取文件创建时间
                from datetime import datetime
                created_time = datetime.fromtimestamp(os.path.getctime(file_path))
                
                # 创建数据库记录
                audio_file = AudioFile(
                    filename=filename,
                    original_name=filename,
                    file_path=file_path,
                    file_size=file_size,
                    duration=0.0,  # 暂时设为0，后续可以通过工具更新
                    project_id=project_id,
                    segment_id=segment_id,
                    audio_type=audio_type,
                    text_content=text_content,
                    status='active',
                    created_at=created_time
                )
                
                db.add(audio_file)
                synced_count += 1
                logger.info(f"同步文件: {filename} (类型: {audio_type})")
                
            except Exception as e:
                logger.warning(f"处理文件失败 {filename}: {str(e)}")
        
        db.commit()
        logger.info(f"音频文件同步完成! 新增: {synced_count}个, 跳过: {skipped_count}个")
        
    except Exception as e:
        logger.error(f"同步音频文件失败: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("开始更新数据库...")
    
    # 创建表
    if create_audio_table():
        # 同步现有文件
        sync_existing_audio_files()
        logger.info("数据库更新完成!")
    else:
        logger.error("数据库更新失败!")
        sys.exit(1) 