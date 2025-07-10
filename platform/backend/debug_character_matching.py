#!/usr/bin/env python3
"""
调试角色匹配过程
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models.character import Character
from app.models.book import Book
from app.models.book_chapter import BookChapter
from app.models.analysis_result import AnalysisResult

def debug_character_matching():
    """调试角色匹配过程"""
    db = next(get_db())
    
    print("=== 角色匹配调试 ===")
    
    # 1. 模拟智能准备过程
    chapter_id = 110
    chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
    
    if not chapter:
        print(f"❌ 章节{chapter_id}不存在")
        return
    
    book_id = chapter.book_id
    print(f"📄 章节{chapter_id}: {chapter.chapter_title}")
    print(f"📚 所属书籍: {book_id}")
    
    # 2. 获取角色配音库角色
    library_characters = db.query(Character).filter(Character.book_id == book_id).all()
    character_library = {char.name: char for char in library_characters}
    
    print(f"\n📚 角色配音库角色 ({len(character_library)}个):")
    for name, char in character_library.items():
        print(f"  - {name}: ID={char.id}, 配置状态={char.is_voice_configured}")
    
    # 3. 查看章节的分析结果
    analysis_result = db.query(AnalysisResult).filter(
        AnalysisResult.chapter_id == chapter_id
    ).order_by(AnalysisResult.created_at.desc()).first()
    
    if analysis_result and analysis_result.synthesis_plan:
        print(f"\n📊 章节分析结果:")
        synthesis_json = analysis_result.synthesis_plan
        
        if 'characters' in synthesis_json:
            print(f"  角色列表 ({len(synthesis_json['characters'])}个):")
            for char in synthesis_json['characters']:
                char_name = char.get('name', 'unknown')
                voice_id = char.get('voice_id', 'none')
                voice_name = char.get('voice_name', 'unknown')
                in_library = char.get('in_character_library', False)
                is_configured = char.get('is_voice_configured', False)
                
                print(f"    - {char_name}:")
                print(f"      * voice_id: {voice_id}")
                print(f"      * voice_name: {voice_name}")
                print(f"      * in_character_library: {in_library}")
                print(f"      * is_voice_configured: {is_configured}")
                
                # 检查是否应该匹配角色配音库
                if char_name in character_library:
                    library_char = character_library[char_name]
                    print(f"      * 🔍 角色配音库匹配: 应该使用ID={library_char.id}")
                    if str(voice_id) != str(library_char.id):
                        print(f"      * ❌ 匹配失败: 实际使用{voice_id}，应该使用{library_char.id}")
                    else:
                        print(f"      * ✅ 匹配成功")
                else:
                    print(f"      * ⚠️ 角色配音库中未找到'{char_name}'")
        
        if 'synthesis_plan' in synthesis_json:
            print(f"\n📋 合成计划:")
            plan = synthesis_json['synthesis_plan']
            speaker_voices = {}
            for segment in plan[:5]:  # 只显示前5个
                speaker = segment.get('speaker', 'unknown')
                voice_id = segment.get('voice_id', 'none')
                if speaker not in speaker_voices:
                    speaker_voices[speaker] = voice_id
                    
            print(f"  角色语音映射:")
            for speaker, voice_id in speaker_voices.items():
                print(f"    - {speaker}: voice_id={voice_id}")
                if speaker in character_library:
                    library_char = character_library[speaker]
                    if str(voice_id) != str(library_char.id):
                        print(f"      ❌ 应该使用{library_char.id}，实际使用{voice_id}")
                    else:
                        print(f"      ✅ 正确使用角色配音库")
    else:
        print(f"\n❌ 章节{chapter_id}没有分析结果")
    
    # 4. 测试匹配逻辑
    print(f"\n🧪 测试匹配逻辑:")
    test_characters = ['小明', '小红', '旁白', '不存在的角色']
    
    for char_name in test_characters:
        print(f"\n  测试角色: {char_name}")
        
        # 检查角色配音库
        if char_name in character_library:
            library_char = character_library[char_name]
            if library_char.is_voice_configured:
                print(f"    ✅ 角色配音库匹配: ID={library_char.id}, 名称={library_char.name}")
            else:
                print(f"    ⚠️ 角色配音库中存在但未配置语音")
        else:
            print(f"    ❌ 角色配音库中不存在")
    
    db.close()

if __name__ == "__main__":
    debug_character_matching() 