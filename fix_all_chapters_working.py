import sys
import os
sys.path.append('platform/backend')

try:
    from app.database import SessionLocal
    from app.models import Book, BookChapter, AnalysisResult
    from app.services.chapter_analysis_service import ChapterAnalysisService
    import json
    import re
    print("✅ 导入成功")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

def fix_character_detection():
    """修复角色识别逻辑"""
    db = SessionLocal()
    try:
        print("🔍 查找第2章...")
        # 获取第2章（有分析结果的那一章）
        chapter = db.query(BookChapter).filter(
            BookChapter.book_id == 9, 
            BookChapter.chapter_number == 2
        ).first()
        
        if not chapter:
            print("❌ 未找到第2章")
            return
            
        print(f"✅ 找到第{chapter.chapter_number}章: {chapter.chapter_title}")
        
        # 从章节内容重新分析角色
        content = chapter.content
        if not content:
            print("❌ 章节内容为空")
            return
            
        print(f"📄 章节内容长度: {len(content)} 字符")
        
        # 重新分析角色和分段
        print("🔧 重新分析角色...")
        characters = extract_characters_from_text(content)
        
        print("🔧 重新分段...")
        segments = segment_text_with_speakers(content, characters)
        
        print(f"\n=== ✨ 重新识别的角色 ({len(characters)}个) ===")
        for char in characters:
            print(f"- {char['name']} (性别: {char['gender']}, 频次: {char['frequency']}, 主角: {char['is_main_character']})")
        
        print(f"\n=== 📝 重新分段结果 (前10段，共{len(segments)}段) ===")
        for i, seg in enumerate(segments[:10]):
            text = seg['text'][:50] + '...' if len(seg['text']) > 50 else seg['text']
            print(f"{i+1}. [{seg['speaker']}]: {text}")
        
        # 构建新的分析结果
        new_analysis = {
            'detected_characters': characters,
            'segments': segments,
            'processing_stats': {
                'total_segments': len(segments),
                'characters_found': len(characters),
                'processing_method': 'manual_fix',
                'confidence': 0.9
            }
        }
        
        print("💾 更新数据库...")
        # 更新数据库中的分析结果
        analysis_result = db.query(AnalysisResult).filter(
            AnalysisResult.chapter_id == chapter.id
        ).first()
        
        if analysis_result:
            analysis_result.result_data = json.dumps(new_analysis, ensure_ascii=False)
            analysis_result.confidence_score = 0.9
            db.commit()
            print(f"✅ 已更新章节 {chapter.id} 的分析结果")
        else:
            print("❌ 未找到分析结果记录")
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

def extract_characters_from_text(content):
    """从文本中提取角色"""
    characters = {}
    
    # 西游记常见角色模式
    character_patterns = [
        r'(孙悟空|悟空|大圣|猴王|行者)(?=[说道：，。！？]|$)',
        r'(唐僧|三藏|师父|长老)(?=[说道：，。！？]|$)',
        r'(猪八戒|八戒|呆子)(?=[说道：，。！？]|$)',
        r'(沙僧|沙和尚|沙师弟)(?=[说道：，。！？]|$)',
        r'(白骨精|妖精|女妖)(?=[说道：，。！？]|$)',
        r'(观音|菩萨)(?=[说道：，。！？]|$)',
        r'(如来|佛祖)(?=[说道：，。！？]|$)',
        r'(玉帝|天帝|皇帝)(?=[说道：，。！？]|$)',
        r'(老君|太上老君)(?=[说道：，。！？]|$)'
    ]
    
    # 统计角色出现频次
    for pattern in character_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            name = normalize_character_name(match)
            if name not in characters:
                characters[name] = {
                    'name': name,
                    'frequency': 0,
                    'gender': infer_gender(name),
                    'is_main_character': is_main_character(name)
                }
            characters[name]['frequency'] += 1
    
    # 添加旁白角色
    characters['旁白'] = {
        'name': '旁白',
        'frequency': 50,  # 旁白频次较高
        'gender': 'neutral',
        'is_main_character': False
    }
    
    return list(characters.values())

def normalize_character_name(name):
    """标准化角色名称"""
    name_mapping = {
        '悟空': '孙悟空',
        '大圣': '孙悟空', 
        '猴王': '孙悟空',
        '行者': '孙悟空',
        '三藏': '唐僧',
        '师父': '唐僧',
        '长老': '唐僧',
        '呆子': '猪八戒',
        '沙师弟': '沙僧',
        '沙和尚': '沙僧',
        '妖精': '白骨精',
        '女妖': '白骨精',
        '菩萨': '观音',
        '佛祖': '如来',
        '天帝': '玉帝',
        '皇帝': '玉帝',
        '太上老君': '老君'
    }
    return name_mapping.get(name, name)

def infer_gender(name):
    """推断角色性别"""
    male_chars = ['孙悟空', '唐僧', '猪八戒', '沙僧', '如来', '玉帝', '老君']
    female_chars = ['白骨精', '观音']
    
    if name in male_chars:
        return 'male'
    elif name in female_chars:
        return 'female'
    else:
        return 'unknown'

def is_main_character(name):
    """判断是否为主要角色"""
    main_chars = ['孙悟空', '唐僧', '猪八戒', '沙僧']
    return name in main_chars

def segment_text_with_speakers(content, characters):
    """重新分段并分配说话人"""
    segments = []
    
    # 按标点分割文本
    sentences = re.split(r'[。！？]', content)
    char_names = [char['name'] for char in characters if char['name'] != '旁白']
    
    for i, sentence in enumerate(sentences):
        if not sentence.strip():
            continue
            
        # 检查是否包含对话
        speaker = '旁白'  # 默认为旁白
        
        # 检查是否有角色说话的模式
        for char_name in char_names:
            if char_name in sentence:
                # 检查是否是对话而不是描述
                if '：' in sentence and '"' in sentence:
                    # 这是对话，但需要分离描述和对话内容
                    if sentence.find(char_name) < sentence.find('：'):
                        # 角色名在冒号前，这是描述性文字，应该是旁白
                        speaker = '旁白'
                    else:
                        speaker = char_name
                elif '"' in sentence:
                    # 包含引号，可能是对话
                    speaker = char_name
                # 如果只是提到角色名但没有对话标识，保持为旁白
        
        segment = {
            'text': sentence.strip() + '。',
            'speaker': speaker,
            'text_type': 'dialogue' if speaker != '旁白' else 'narration',
            'confidence': 0.8
        }
        segments.append(segment)
    
    return segments

if __name__ == "__main__":
    print("🚀 开始修复角色识别...")
    fix_character_detection()
    print("🎉 修复完成!") 