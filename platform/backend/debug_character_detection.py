# 调试角色识别算法的问题
from app.database import get_db
from app.models import NovelProject, BookChapter, AnalysisResult
import json

def debug_character_detection():
    db = next(get_db())
    
    print("=== 调试角色识别算法问题 ===")
    
    # 1. 获取项目34的智能分析原始数据
    project = db.query(NovelProject).filter(NovelProject.id == 34).first()
    if not project or not project.book_id:
        print("❌ 项目数据不完整")
        return
    
    chapters = db.query(BookChapter).filter(BookChapter.book_id == project.book_id).all()
    
    for chapter in chapters:
        print(f"\n📖 章节: {chapter.chapter_title}")
        
        if chapter.analysis_results:
            analysis = chapter.analysis_results[0]
            
            # 检查原始分析结果
            print(f"🔍 检查原始分析数据:")
            if hasattr(analysis, 'original_analysis') and analysis.original_analysis:
                original = analysis.original_analysis
                
                print(f"  原始数据类型: {type(original)}")
                
                if isinstance(original, dict):
                    # 检查detected_characters字段
                    detected_chars = original.get('detected_characters', [])
                    print(f"  🎭 原始检测角色数: {len(detected_chars)}")
                    
                    for i, char in enumerate(detected_chars):
                        if isinstance(char, dict):
                            name = char.get('name', '未知')
                            confidence = char.get('confidence', char.get('frequency', 0))
                            print(f"    {i+1}. {name} (置信度: {confidence})")
                        else:
                            print(f"    {i+1}. {char}")
                    
                    # 检查segments中实际出现的speaker
                    segments = original.get('segments', [])
                    print(f"  📝 段落数据中的说话人:")
                    
                    speakers = set()
                    for seg in segments[:10]:  # 只检查前10个段落
                        speaker = seg.get('speaker', '未知')
                        speakers.add(speaker)
                    
                    print(f"    实际说话人: {list(speakers)}")
                    
                    # 对比detected_characters和实际speakers
                    detected_names = set()
                    for char in detected_chars:
                        if isinstance(char, dict):
                            detected_names.add(char.get('name', '未知'))
                        else:
                            detected_names.add(str(char))
                    
                    missing_in_detection = speakers - detected_names
                    if missing_in_detection:
                        print(f"  ❌ 角色识别遗漏: {list(missing_in_detection)}")
                        
                        # 分析为什么这些角色没有被识别
                        print(f"  🔍 分析遗漏原因:")
                        for missing_char in missing_in_detection:
                            char_segments = [s for s in segments if s.get('speaker') == missing_char]
                            print(f"    - {missing_char}: 出现在{len(char_segments)}个段落中")
                            if char_segments:
                                sample_text = char_segments[0].get('text', '')[:50]
                                print(f"      示例文本: {sample_text}...")
                    else:
                        print(f"  ✅ 角色识别完整")
            
            # 检查final_config中的角色映射
            print(f"\n🎛️ 检查final_config:")
            if hasattr(analysis, 'final_config') and analysis.final_config:
                try:
                    final_config = json.loads(analysis.final_config) if isinstance(analysis.final_config, str) else analysis.final_config
                    
                    synthesis_json = final_config.get('synthesis_json', {})
                    characters = synthesis_json.get('characters', [])
                    
                    print(f"  final_config中的角色数: {len(characters)}")
                    for char in characters:
                        name = char.get('name', '未知')
                        voice_id = char.get('voice_id', '无')
                        count = char.get('count', 0)
                        print(f"    - {name}: voice_id={voice_id}, 出现{count}次")
                        
                except Exception as e:
                    print(f"  ❌ 解析final_config失败: {e}")
            
            # 检查detected_characters字段
            print(f"\n📊 检查detected_characters字段:")
            if hasattr(analysis, 'detected_characters'):
                detected = analysis.detected_characters
                print(f"  detected_characters: {detected}")
                print(f"  类型: {type(detected)}")
        else:
            print("  ❌ 无分析结果")
    
    print(f"\n💡 问题总结:")
    print(f"  1. 角色识别算法可能有缺陷，没有正确识别对话中的角色")
    print(f"  2. 或者识别后的数据在处理过程中丢失了")
    print(f"  3. 需要检查角色识别的具体算法和参数")

if __name__ == "__main__":
    debug_character_detection()