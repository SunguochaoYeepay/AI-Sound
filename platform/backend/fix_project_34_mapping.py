# 快速修复项目34的声音映射问题
from app.database import get_db
from app.models import NovelProject, VoiceProfile
import json

def fix_project_34_mapping():
    db = next(get_db())
    
    print("=== 修复项目34声音映射 ===")
    
    # 1. 获取项目
    project = db.query(NovelProject).filter(NovelProject.id == 34).first()
    if not project:
        print("❌ 项目34不存在")
        return
    
    # 2. 获取一个默认声音（用作旁白）
    default_voice = db.query(VoiceProfile).filter(VoiceProfile.status == 'active').first()
    if not default_voice:
        print("❌ 没有可用的声音档案")
        return
    
    print(f"📋 使用默认声音: {default_voice.name} (ID: {default_voice.id})")
    
    # 3. 设置默认角色映射
    default_mapping = {
        "旁白": default_voice.id,
        "narrator": default_voice.id,
        "系统旁白": default_voice.id,
        "心理旁白": default_voice.id,
        "未知角色": default_voice.id
    }
    
    # 4. 检查是否有智能准备结果中的角色
    if project.book_id:
        from app.models import BookChapter
        chapters = db.query(BookChapter).filter(BookChapter.book_id == project.book_id).all()
        
        detected_characters = set()
        for chapter in chapters:
            if chapter.analysis_results:
                try:
                    analysis = json.loads(chapter.analysis_results)
                    characters = analysis.get('characters', [])
                    for char in characters:
                        char_name = char.get('name')
                        if char_name:
                            detected_characters.add(char_name)
                except:
                    pass
        
        print(f"🎭 检测到的角色: {list(detected_characters)}")
        
        # 为检测到的角色分配声音
        voices = db.query(VoiceProfile).filter(VoiceProfile.status == 'active').limit(5).all()
        for i, char_name in enumerate(detected_characters):
            if i < len(voices):
                default_mapping[char_name] = voices[i].id
                print(f"  {char_name} -> {voices[i].name} (ID: {voices[i].id})")
            else:
                default_mapping[char_name] = default_voice.id
                print(f"  {char_name} -> {default_voice.name} (默认)")
    
    # 5. 保存映射配置
    try:
        project.set_character_mapping(default_mapping)
        db.commit()
        
        print(f"\n✅ 映射配置已保存:")
        print(json.dumps(default_mapping, indent=2, ensure_ascii=False))
        
        print(f"\n🚀 建议操作:")
        print(f"  1. 重新启动合成任务")
        print(f"  2. 或者在前端重新配置更合适的声音映射")
        
    except Exception as e:
        print(f"❌ 保存映射失败: {e}")

if __name__ == "__main__":
    fix_project_34_mapping()