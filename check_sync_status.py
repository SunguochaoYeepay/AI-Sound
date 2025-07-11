#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append('.')
from app.database import get_db
from app.models import Book, Character, AnalysisResult
import json

def check_xiaohong_sync():
    """检查小红角色的数据同步状态"""
    print("开始检查数据同步状态...")
    
    db = next(get_db())
    try:
        # 首先检查是否有Character数据
        all_characters = db.query(Character).all()
        print(f"数据库中总共有 {len(all_characters)} 个角色")
        
        # 检查book_id=12的角色
        book_12_characters = db.query(Character).filter(Character.book_id == 12).all()
        print(f"书籍ID=12中有 {len(book_12_characters)} 个角色:")
        for char in book_12_characters:
            print(f"  - {char.name} (ID: {char.id})")
        
        # 1. 检查角色配音库中的小红
        xiaohong = db.query(Character).filter(Character.name == '小红', Character.book_id == 12).first()
        if xiaohong:
            print('\n=== 角色配音库中的小红 ===')
            print(f'ID: {xiaohong.id}')
            print(f'音频路径: {xiaohong.reference_audio_path}')
            print(f'最后更新: {xiaohong.updated_at}')
        else:
            print('\n❌ 未找到小红角色 (name="小红", book_id=12)')
            return
            
        # 2. 检查书籍角色汇总中的小红
        book = db.query(Book).filter(Book.id == 12).first()
        if book:
            print(f'\n=== 书籍信息 ===')
            print(f'书籍标题: {book.title}')
            
            character_summary = book.get_character_summary()
            print(f'\n=== 书籍角色汇总中的小红 ===')
            print(f'角色汇总数据: {character_summary}')
            
            if character_summary and 'voice_mappings' in character_summary:
                xiaohong_mapping = character_summary['voice_mappings'].get('小红')
                if xiaohong_mapping:
                    voice_id = xiaohong_mapping.get('voice_id')
                    voice_name = xiaohong_mapping.get('voice_name')
                    print(f'语音ID: {voice_id}')
                    print(f'语音名称: {voice_name}')
                    
                    # 检查是否匹配角色配音库
                    if voice_id == xiaohong.id:
                        print('✅ 书籍汇总与角色配音库数据一致')
                    else:
                        print(f'❌ 数据不一致! 书籍汇总voice_id={voice_id}, 角色配音库id={xiaohong.id}')
                else:
                    print('❌ 未找到小红的语音映射')
            else:
                print('❌ 书籍没有角色汇总数据或缺少voice_mappings字段')
            
            # 3. 检查章节分析结果中的小红
            chapters = db.query(AnalysisResult).filter(AnalysisResult.book_id == 12).limit(3).all()
            print(f'\n=== 检查前3个章节中的小红 ===')
            print(f'找到 {len(chapters)} 个章节分析结果')
            
            for chapter in chapters:
                print(f'\n章节 {chapter.chapter_number}:')
                if chapter.synthesis_plan:
                    try:
                        synthesis_data = json.loads(chapter.synthesis_plan)
                        segments = synthesis_data.get('segments', [])
                        xiaohong_segments = [s for s in segments if s.get('character') == '小红']
                        
                        print(f'  总段落: {len(segments)}, 小红段落: {len(xiaohong_segments)}')
                        
                        if xiaohong_segments:
                            first_segment = xiaohong_segments[0]
                            chapter_voice_id = first_segment.get('voice_id')
                            chapter_voice_name = first_segment.get('voice_name')
                            
                            print(f'  voice_id={chapter_voice_id}, voice_name={chapter_voice_name}')
                            
                            if chapter_voice_id == xiaohong.id:
                                print(f'  ✅ 与角色配音库一致')
                            else:
                                print(f'  ❌ 不一致! 应该是{xiaohong.id}')
                        else:
                            print('  未找到小红的段落')
                    except Exception as e:
                        print(f'  解析synthesis_plan失败 - {e}')
                else:
                    print('  没有synthesis_plan数据')
        else:
            print('\n❌ 未找到书籍ID=12')
        
    except Exception as e:
        print(f"执行过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    check_xiaohong_sync() 