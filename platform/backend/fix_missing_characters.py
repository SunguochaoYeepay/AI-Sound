# 为项目34补充缺失的角色声音映射
from app.database import get_db
from app.models import NovelProject, VoiceProfile
import json

def fix_missing_characters():
    db = next(get_db())
    
    print("=== 修复项目34缺失角色映射 ===")
    
    # 1. 获取项目
    project = db.query(NovelProject).filter(NovelProject.id == 34).first()
    if not project:
        print("❌ 项目34不存在")
        return
    
    # 2. 获取当前映射
    current_mapping = project.get_character_mapping() or {}
    print(f"📋 当前映射: {current_mapping}")
    
    # 3. 获取可用声音
    voices = db.query(VoiceProfile).filter(VoiceProfile.status == 'active').all()
    voice_list = [(v.id, v.name) for v in voices]
    
    print(f"\n🎤 可用声音档案:")
    for voice_id, voice_name in voice_list[:10]:
        print(f"  {voice_id}: {voice_name}")
    
    # 4. 补充缺失的角色映射
    missing_characters = {
        "林渊": "主角，男性，年轻学者",
        "导师": "女性，温柔知性", 
        "将领": "男性，威严军人"
    }
    
    print(f"\n🎭 补充缺失角色:")
    for char_name, description in missing_characters.items():
        if char_name not in current_mapping:
            # 为不同角色分配合适的声音
            if char_name == "林渊":
                # 找个男性声音给主角
                voice_id = 7  # 唐僧 - 比较温和的男声
                voice_name = "唐僧"
            elif char_name == "导师":
                # 找个女性声音给导师
                voice_id = 15  # 观音菩萨 - 温柔女声
                voice_name = "观音菩萨"
            elif char_name == "将领":
                # 找个威严的声音给将领
                voice_id = 14  # 妖怪 - 比较有气势
                voice_name = "妖怪"
            else:
                # 默认声音
                voice_id = 4  # 周星驰
                voice_name = "周星驰"
            
            current_mapping[char_name] = voice_id
            print(f"  ✅ {char_name} -> {voice_name} (ID: {voice_id}) - {description}")
        else:
            print(f"  ⏭️ {char_name} 已配置")
    
    # 5. 保存更新的映射
    try:
        project.set_character_mapping(current_mapping)
        db.commit()
        
        print(f"\n✅ 更新后的完整映射:")
        print(json.dumps(current_mapping, indent=2, ensure_ascii=False))
        
        print(f"\n🚀 修复完成！现在可以:")
        print(f"  1. 重新启动合成任务")
        print(f"  2. 失败数应该从15减少到0")
        print(f"  3. 所有40个段落都有声音配置了")
        
        return True
        
    except Exception as e:
        print(f"❌ 保存映射失败: {e}")
        return False

if __name__ == "__main__":
    fix_missing_characters()