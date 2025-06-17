# 调试项目34的声音映射问题
from app.database import get_db
from app.models import NovelProject, VoiceProfile
import json

def debug_voice_mapping():
    db = next(get_db())
    
    print("=== 调试项目34声音映射问题 ===")
    
    # 1. 检查项目配置
    project = db.query(NovelProject).filter(NovelProject.id == 34).first()
    if not project:
        print("❌ 项目34不存在")
        return
    
    print(f"📋 项目信息:")
    print(f"  名称: {project.name}")
    print(f"  状态: {project.status}")
    print(f"  关联书籍: {project.book_id}")
    
    # 2. 检查字符映射配置
    try:
        char_mapping = project.get_character_mapping()
        print(f"\n🎭 字符映射配置:")
        if char_mapping:
            print(json.dumps(char_mapping, indent=2, ensure_ascii=False))
        else:
            print("  无映射配置")
    except Exception as e:
        print(f"  获取映射配置失败: {e}")
    
    # 3. 检查可用声音档案
    voices = db.query(VoiceProfile).filter(VoiceProfile.status == 'active').all()
    print(f"\n🎤 可用声音档案 ({len(voices)}个):")
    for voice in voices[:5]:  # 只显示前5个
        print(f"  ID={voice.id}: {voice.name} (状态: {voice.status})")
    if len(voices) > 5:
        print(f"  ... 还有{len(voices) - 5}个声音档案")
    
    # 4. 检查智能准备结果
    print(f"\n📚 检查智能准备结果:")
    if project.book_id:
        from app.models import BookChapter
        chapters = db.query(BookChapter).filter(BookChapter.book_id == project.book_id).all()
        print(f"  关联书籍的章节数: {len(chapters)}")
        
        analyzed_chapters = [ch for ch in chapters if ch.analysis_results]
        print(f"  已分析章节数: {len(analyzed_chapters)}")
        
        if analyzed_chapters:
            sample_chapter = analyzed_chapters[0]
            try:
                analysis = json.loads(sample_chapter.analysis_results)
                characters = analysis.get('characters', [])
                print(f"  第一个分析章节的角色数: {len(characters)}")
                
                if characters:
                    print("  前3个角色:")
                    for char in characters[:3]:
                        char_name = char.get('name', '未知')
                        voice_id = char.get('voice_id', '无')
                        print(f"    - {char_name}: voice_id={voice_id}")
                        
            except Exception as e:
                print(f"  解析分析结果失败: {e}")
    else:
        print("  项目未关联书籍")
    
    # 5. 给出修复建议
    print(f"\n💡 修复建议:")
    if not char_mapping:
        print("  1. 项目缺少字符映射配置")
        print("  2. 需要在合成中心页面:")
        print("     - 选择章节")
        print("     - 加载智能准备结果")
        print("     - 配置角色声音映射")
        print("     - 然后开始合成")
    else:
        print("  1. 检查映射的voice_id是否有效")
        print("  2. 确保所有角色都有对应的声音配置")

if __name__ == "__main__":
    debug_voice_mapping()