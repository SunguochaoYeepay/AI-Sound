#!/usr/bin/env python3
"""
测试角色声音映射功能
"""
import requests
import json

def test_voice_mapping():
    print("=== 测试角色声音映射 ===")
    
    # 1. 获取最新项目ID
    try:
        projects_response = requests.get("http://localhost:8000/api/novel-reader/projects?page_size=1")
        if projects_response.status_code == 200:
            projects_data = projects_response.json()
            if projects_data['data']:
                project_id = projects_data['data'][0]['id']
                project_name = projects_data['data'][0]['name']
                print(f"找到项目: ID={project_id}, 名称={project_name}")
            else:
                print("没有找到任何项目")
                return
        else:
            print(f"获取项目列表失败: {projects_response.status_code}")
            return
    except Exception as e:
        print(f"获取项目列表异常: {e}")
        return
    
    # 2. 获取项目详情，查看角色
    try:
        detail_response = requests.get(f"http://localhost:8000/api/novel-reader/projects/{project_id}")
        if detail_response.status_code == 200:
            detail_data = detail_response.json()
            segments = detail_data['data']['segments']
            
            print(f"\n项目段落:")
            speakers = set()
            for segment in segments:
                speaker = segment['detectedSpeaker']
                speakers.add(speaker)
                print(f"  段落 {segment['segmentOrder']}: {segment['textContent'][:30]}... (说话人: {speaker})")
            
            print(f"\n识别的角色: {list(speakers)}")
        else:
            print(f"获取项目详情失败: {detail_response.status_code}")
            return
    except Exception as e:
        print(f"获取项目详情异常: {e}")
        return
    
    # 3. 获取可用声音
    try:
        voices_response = requests.get("http://localhost:8000/api/characters/")
        if voices_response.status_code == 200:
            voices_data = voices_response.json()
            voices = voices_data['data']
            
            print(f"\n可用声音:")
            for voice in voices:
                voice_type = voice.get('voice_type') or voice.get('type', 'unknown')
                print(f"  ID={voice['id']}: {voice['name']} ({voice_type})")
        else:
            print(f"获取声音列表失败: {voices_response.status_code}")
            return
    except Exception as e:
        print(f"获取声音列表异常: {e}")
        return
    
    # 4. 设置角色映射
    try:
        # 为每个角色分配声音
        character_mapping = {}
        voice_index = 0
        
        for speaker in speakers:
            if voice_index < len(voices):
                character_mapping[speaker] = voices[voice_index]['id']
                print(f"分配: {speaker} -> {voices[voice_index]['name']}")
                voice_index += 1
        
        print(f"\n角色映射: {character_mapping}")
        
        # 更新项目
        update_data = {
            "name": project_name,
            "description": "测试项目 - 已设置角色映射",
            "character_mapping": json.dumps(character_mapping)
        }
        
        update_response = requests.put(f"http://localhost:8000/api/novel-reader/projects/{project_id}", data=update_data)
        
        if update_response.status_code == 200:
            print(f"✅ 角色映射设置成功")
            
            # 5. 测试开始生成
            print(f"\n=== 测试开始音频生成 ===")
            generation_data = {"parallel_tasks": 2}
            generation_response = requests.post(f"http://localhost:8000/api/novel-reader/projects/{project_id}/start-generation", data=generation_data)
            
            if generation_response.status_code == 200:
                print(f"✅ 音频生成已开始")
                result = generation_response.json()
                print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            else:
                print(f"❌ 开始生成失败: {generation_response.status_code}")
                print(f"错误响应: {generation_response.text}")
                
        else:
            print(f"❌ 设置角色映射失败: {update_response.status_code}")
            print(f"错误响应: {update_response.text}")
            
    except Exception as e:
        print(f"设置角色映射异常: {e}")

if __name__ == "__main__":
    test_voice_mapping() 