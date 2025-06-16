#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'platform', 'backend'))

from app.database import get_db
from app.models import VoiceProfile

def check_voice_profile():
    print("=== 检查声音档案状态 ===")
    
    db = next(get_db())
    
    # 检查声音ID 5
    voice = db.query(VoiceProfile).filter(VoiceProfile.id == 5).first()
    
    if not voice:
        print("❌ 声音ID 5 不存在")
        return
    
    print(f"🎤 声音档案 ID 5:")
    print(f"   名称: {voice.name}")
    print(f"   状态: {voice.status}")
    print(f"   类型: {voice.type}")
    print(f"   描述: {voice.description}")
    print(f"   参考音频路径: {voice.reference_audio_path}")
    print(f"   Latent文件路径: {voice.latent_file_path}")
    print(f"   示例音频路径: {voice.sample_audio_path}")
    print(f"   参数: {voice.parameters}")
    print(f"   质量评分: {voice.quality_score}")
    print(f"   使用次数: {voice.usage_count}")
    print(f"   创建时间: {voice.created_at}")
    print(f"   更新时间: {voice.updated_at}")
    
    # 检查文件是否存在
    if voice.reference_audio_path:
        if os.path.exists(voice.reference_audio_path):
            print(f"   ✅ 参考音频文件存在")
        else:
            print(f"   ❌ 参考音频文件不存在: {voice.reference_audio_path}")
    
    if voice.latent_file_path:
        if os.path.exists(voice.latent_file_path):
            print(f"   ✅ Latent文件存在")
        else:
            print(f"   ❌ Latent文件不存在: {voice.latent_file_path}")
    
    if voice.sample_audio_path:
        if os.path.exists(voice.sample_audio_path):
            print(f"   ✅ 示例音频文件存在")
        else:
            print(f"   ❌ 示例音频文件不存在: {voice.sample_audio_path}")
    
    # 检查项目22中使用声音ID 5的所有段落
    from app.models import TextSegment
    segments_with_voice_5 = db.query(TextSegment).filter(
        TextSegment.project_id == 22,
        TextSegment.voice_id == '5'  # 转换为字符串
    ).all()
    
    print(f"\n📝 项目22中使用声音ID 5的段落:")
    print(f"   总数: {len(segments_with_voice_5)}")
    
    if segments_with_voice_5:
        status_count = {}
        for segment in segments_with_voice_5:
            status = segment.status
            status_count[status] = status_count.get(status, 0) + 1
        
        print(f"   状态统计:")
        for status, count in status_count.items():
            emoji = "✅" if status == "completed" else "❌" if status == "failed" else "🔄" if status == "processing" else "⏸️"
            print(f"      {emoji} {status}: {count} 个")
        
        # 显示失败的段落
        failed_segments = [s for s in segments_with_voice_5 if s.status == 'failed']
        if failed_segments:
            print(f"\n   失败的段落:")
            for segment in failed_segments:
                print(f"      段落{segment.id}: {segment.speaker} - {segment.error_message}")

if __name__ == "__main__":
    check_voice_profile() 