#!/usr/bin/env python3
"""
诊断项目角色识别问题
"""
import requests
import json

def diagnose_project(project_id):
    print(f"🔍 === 诊断项目 {project_id} ===")
    
    try:
        # 获取项目详情
        response = requests.get(f'http://localhost:8000/api/novel-reader/projects/{project_id}')
        
        if response.status_code != 200:
            print(f"❌ 获取项目失败: {response.status_code}")
            return
        
        data = response.json()
        if not data.get('success'):
            print(f"❌ API错误: {data.get('message')}")
            return
        
        project = data['data']
        segments = project.get('segments', [])
        
        print(f"📋 项目信息:")
        print(f"  名称: {project.get('name')}")
        print(f"  状态: {project.get('status')}")
        print(f"  原始文本长度: {len(project.get('originalText', ''))}")
        print(f"  段落数量: {len(segments)}")
        
        if not segments:
            print("❌ 没有段落数据，可能是分段失败")
            return
        
        print(f"\n📝 段落分析:")
        speakers = {}
        
        for segment in segments:
            # 兼容不同的字段名
            segment_order = segment.get('segmentOrder') or segment.get('segment_order', '?')
            text_content = segment.get('textContent') or segment.get('text_content', '')
            detected_speaker = (segment.get('detectedSpeaker') or 
                              segment.get('detected_speaker') or 
                              segment.get('speaker', '未知'))
            
            speakers[detected_speaker] = speakers.get(detected_speaker, 0) + 1
            
            print(f"  段落 {segment_order}: \"{text_content[:30]}{'...' if len(text_content) > 30 else ''}\" -> {detected_speaker}")
        
        print(f"\n🎭 角色统计:")
        total_speakers = len(speakers)
        for speaker, count in speakers.items():
            print(f"  {speaker}: {count}个段落")
        
        print(f"\n💡 诊断结果:")
        
        if total_speakers == 0:
            print("❌ 严重问题：没有检测到任何说话人")
        elif total_speakers == 1 and '旁白' in speakers:
            print("⚠️  问题：只检测到旁白，没有角色对话")
            print("   建议：使用包含明确对话的文本，例如：")
            print('   • 小明说："你好世界！"')
            print('   • "真不错！"张老师笑着说')
            print('   • 李华：同学们，大家好')
        elif total_speakers == 1:
            speaker_name = list(speakers.keys())[0]
            print(f"⚠️  问题：只检测到一个角色 '{speaker_name}'")
            print("   建议：添加更多角色的对话")
        else:
            non_narrator = [s for s in speakers.keys() if s not in ['旁白', 'narrator']]
            if len(non_narrator) > 0:
                print(f"✅ 良好：检测到 {len(non_narrator)} 个角色对话")
                print(f"   角色列表: {', '.join(non_narrator)}")
            else:
                print("⚠️  问题：只有旁白，没有角色对话")
        
        # 检查文本格式
        original_text = project.get('originalText', '')
        if original_text:
            print(f"\n📊 文本格式分析:")
            print(f"  文本长度: {len(original_text)}字符")
            
            # 检查对话标记
            has_quotes = any(quote in original_text for quote in ['"', '"', '"', '「', '」', '『', '』'])
            has_colon = '：' in original_text or ':' in original_text
            has_dialogue_verbs = any(verb in original_text for verb in ['说', '道', '讲', '叫', '喊', '问', '答', '回复'])
            
            print(f"  包含引号: {'✅' if has_quotes else '❌'}")
            print(f"  包含冒号: {'✅' if has_colon else '❌'}")
            print(f"  包含对话动词: {'✅' if has_dialogue_verbs else '❌'}")
            
            if not any([has_quotes, has_colon, has_dialogue_verbs]):
                print("  ⚠️  文本缺少明显的对话标记")
        
    except Exception as e:
        print(f"❌ 诊断失败: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        project_id = int(sys.argv[1])
        diagnose_project(project_id)
    else:
        print("用法: python diagnose_project.py <project_id>")
        print("例如: python diagnose_project.py 4") 