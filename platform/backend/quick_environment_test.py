#!/usr/bin/env python3
"""
快速环境音测试 - 完全使用HTTP API调用
"""

import requests
import json
import time
import os

BASE_URL = "http://localhost:8000"

def test_backend_health():
    """测试后端健康状态"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务正常")
            return True
        else:
            print(f"❌ 后端服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 后端服务连接失败: {str(e)}")
        return False

def create_book():
    """创建测试书籍"""
    print("\n📚 创建测试书籍...")
    
    url = f"{BASE_URL}/api/books"
    data = {
        "title": "环境音快速测试",
        "author": "AI助手",
        "description": "短小精悍的环境音效果测试",
        "content": """第一章 雨夜邂逅

雨夜中，林雨轻声说道："这场雨下得真大啊。"

张明回答："是啊，我们快点找个地方避雨吧。"

突然，远处传来雷声。林雨紧张地说："听起来暴雨要来了。"

张明安慰道："别担心，前面就有个小亭子。"

他们跑向亭子，雨声渐渐变小。"""
    }
    
    try:
        response = requests.post(url, data=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            book_id = result['data']['id']
            print(f"✅ 书籍创建成功 (ID: {book_id})")
            return book_id
        else:
            print(f"❌ 书籍创建失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 书籍创建异常: {str(e)}")
        return None

def create_project(book_id):
    """创建项目"""
    print(f"\n🎯 创建项目...")
    
    url = f"{BASE_URL}/api/novel-reader/projects"
    
    # 角色映射和项目设置
    initial_characters = json.dumps([
        {"name": "林雨", "voice_id": 21},
        {"name": "张明", "voice_id": 26}
    ])
    
    project_settings = json.dumps({
        "segment_mode": "paragraph",
        "audio_quality": "high",
        "enable_smart_detection": True,
        "enable_bg_music": False,
        "environment_settings": {
            "enable_environment": True,
            "environment_volume": 0.4,
            "auto_scene_detection": True,
            "scene_transition_fade": 1.0,
            "supported_scenes": [
                "雨夜",
                "雷雨", 
                "室外",
                "亭子"
            ]
        }
    })
    
    data = {
        "name": "环境音快速测试",
        "description": "短小精悍的环境音效果验证",
        "book_id": book_id,
        "initial_characters": initial_characters,
        "settings": project_settings
    }
    
    try:
        response = requests.post(url, data=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            project_id = result['data']['id']
            print(f"✅ 项目创建成功 (ID: {project_id})")
            return project_id
        else:
            print(f"❌ 项目创建失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 项目创建异常: {str(e)}")
        return None

def intelligent_preparation(project_id, book_id):
    """智能准备"""
    print(f"\n🧠 执行智能准备...")
    
    url = f"{BASE_URL}/api/analysis/intelligent-preparation"
    data = {
        "project_id": project_id,
        "book_id": book_id,
        "enable_character_detection": True,
        "enable_scene_analysis": True
    }
    
    try:
        response = requests.post(url, json=data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 智能准备完成")
            
            # 显示分析结果
            data = result.get('data', {})
            characters = data.get('characters', [])
            segments = data.get('segments', [])
            
            print(f"   角色数量: {len(characters)}")
            print(f"   段落数量: {len(segments)}")
            
            if characters:
                print(f"   识别角色: {[c.get('name', 'Unknown') for c in characters]}")
            
            return True
        else:
            print(f"❌ 智能准备失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 智能准备异常: {str(e)}")
        return False

def start_synthesis(project_id):
    """开始合成"""
    print(f"\n🎵 开始环境音合成...")
    
    url = f"{BASE_URL}/api/novel-reader/projects/{project_id}/start"
    data = {
        "parallel_tasks": 1,
        "synthesis_mode": "smart_preparation",
        "enable_environment": True,
        "environment_volume": 0.4
    }
    
    try:
        response = requests.post(url, data=data, timeout=30)
        if response.status_code == 200:
            print(f"✅ 合成任务已启动")
            return True
        else:
            print(f"❌ 合成启动失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 合成启动异常: {str(e)}")
        return False

def wait_for_completion(project_id):
    """等待合成完成"""
    print(f"\n⏳ 等待合成完成...")
    
    url = f"{BASE_URL}/api/novel-reader/projects/{project_id}/progress"
    max_wait = 300  # 最多等5分钟
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                project_data = data.get('data', {})
                status = project_data.get('status', 'unknown')
                progress = project_data.get('progress', 0)
                
                print(f"   状态: {status}, 进度: {progress}%")
                
                if status == 'completed':
                    print(f"✅ 合成完成！")
                    return True
                elif status == 'failed':
                    print(f"❌ 合成失败")
                    return False
                
                time.sleep(5)
            else:
                print(f"❌ 进度查询失败: {response.status_code}")
                break
        except Exception as e:
            print(f"❌ 进度查询异常: {str(e)}")
            break
    
    print(f"⏰ 等待超时")
    return False

def get_final_result(project_id):
    """获取最终结果"""
    print(f"\n🔍 获取最终结果...")
    
    url = f"{BASE_URL}/api/novel-reader/projects/{project_id}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            project_data = data.get('data', {})
            
            status = project_data.get('status')
            final_audio_path = project_data.get('final_audio_path')
            audio_files = project_data.get('audio_files', [])
            
            print(f"   项目状态: {status}")
            print(f"   最终音频路径: {final_audio_path}")
            print(f"   音频文件数量: {len(audio_files)}")
            
            # 查找最新的混合音频文件
            mixed_files = [f for f in audio_files if 'mixed' in f.get('filename', '')]
            if mixed_files:
                latest_mixed = max(mixed_files, key=lambda x: x.get('created_at', ''))
                file_path = latest_mixed.get('file_path', '')
                if file_path:
                    full_path = os.path.abspath(file_path)
                    if os.path.exists(full_path):
                        file_size = os.path.getsize(full_path) / 1024 / 1024
                        print(f"✅ 找到环境音混合文件:")
                        print(f"   文件: {latest_mixed.get('filename')}")
                        print(f"   大小: {file_size:.1f} MB")
                        print(f"   完整路径: {full_path}")
                        return full_path
            
            # 查找普通最终音频文件
            if final_audio_path and os.path.exists(final_audio_path):
                full_path = os.path.abspath(final_audio_path)
                file_size = os.path.getsize(full_path) / 1024 / 1024
                print(f"⚠️ 找到普通音频文件（可能无环境音）:")
                print(f"   大小: {file_size:.1f} MB")
                print(f"   完整路径: {full_path}")
                return full_path
            
            print(f"❌ 没有找到可用的音频文件")
            return None
            
        else:
            print(f"❌ 获取项目信息失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 获取项目信息异常: {str(e)}")
        return None

def main():
    """主函数"""
    print("🎯 快速环境音测试开始")
    print("   内容：雨夜对话场景")
    print("   预期：短小精悍，有对话有环境音")
    
    # 1. 检查后端健康状态
    if not test_backend_health():
        print("❌ 后端服务不可用，请启动后端服务")
        return
    
    try:
        # 2. 创建书籍
        book_id = create_book()
        if not book_id:
            print("❌ 书籍创建失败，终止测试")
            return
        
        # 3. 创建项目
        project_id = create_project(book_id)
        if not project_id:
            print("❌ 项目创建失败，终止测试")
            return
        
        # 4. 智能准备
        if not intelligent_preparation(project_id, book_id):
            print("❌ 智能准备失败，终止测试")
            return
        
        # 5. 开始合成
        if not start_synthesis(project_id):
            print("❌ 合成启动失败，终止测试")
            return
        
        # 6. 等待完成
        if not wait_for_completion(project_id):
            print("❌ 合成未完成，请检查后端日志")
            return
        
        # 7. 获取最终结果
        audio_path = get_final_result(project_id)
        if audio_path:
            print(f"\n🎉 测试成功完成！")
            print(f"🎵 最终音频文件:")
            print(f"   {audio_path}")
            print(f"\n💡 请播放这个文件，应该能听到:")
            print(f"   📢 林雨（女声）和张明（男声）的对话")
            print(f"   🌧️ 雨夜背景音效")
            print(f"   ⚡ 雷声效果")
            print(f"   🏠 场景转换音效（从室外到亭子）")
            print(f"\n🔊 如果听不到环境音，文件大小应该比较小")
            print(f"   如果有环境音，文件会明显更大一些")
        else:
            print(f"❌ 测试失败，没有生成音频文件")
            
    except Exception as e:
        print(f"❌ 测试过程出现异常: {str(e)}")

if __name__ == "__main__":
    main() 