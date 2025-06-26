#!/usr/bin/env python3
"""
创建简单的环境音测试数据
生成短小精悍的对话内容，快速测试环境音效果
"""

import os
import sys
import json
import requests
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models import Book, Chapter, NovelProject

def create_simple_test_data():
    """创建简单测试数据"""
    print("🚀 创建简单环境音测试数据...")
    
    db = next(get_db())
    
    # 1. 创建测试书籍
    book = Book(
        title="环境音测试小说",
        author="AI助手",
        description="短小精悍的环境音效果测试",
        status="published",
        total_chapters=1
    )
    db.add(book)
    db.flush()
    
    print(f"✅ 创建书籍: {book.title} (ID: {book.id})")
    
    # 2. 创建测试章节 - 超短内容，重点突出环境音
    short_content = """第一章 雨夜邂逅

雨夜中，林雨轻声说道："这场雨下得真大啊。"

张明回答："是啊，我们快点找个地方避雨吧。"

突然，远处传来雷声。林雨紧张地说："听起来暴雨要来了。"

张明安慰道："别担心，前面就有个小亭子。"

他们跑向亭子，雨声渐渐变小。"""

    chapter = Chapter(
        book_id=book.id,
        chapter_number=1,
        title="雨夜邂逅",
        content=short_content,
        status="published",
        word_count=len(short_content)
    )
    db.add(chapter)
    db.flush()
    
    print(f"✅ 创建章节: {chapter.title} (ID: {chapter.id})")
    print(f"   内容长度: {len(short_content)} 字符")
    
    # 3. 创建项目
    project = NovelProject(
        name="环境音快速测试",
        description="短小精悍的环境音效果验证",
        book_id=book.id,
        status='pending'
    )
    
    # 设置环境音配置
    project_config = {
        "character_mapping": {
            "林雨": 21,  # 使用女声
            "张明": 26   # 使用男声
        },
        "segment_mode": "paragraph",
        "audio_quality": "high",
        "enable_smart_detection": True,
        "enable_bg_music": False,
        "environment_settings": {
            "enable_environment": True,
            "environment_volume": 0.4,  # 稍微提高音量便于测试
            "auto_scene_detection": True,
            "scene_transition_fade": 1.0,  # 短一点的淡入淡出
            "supported_scenes": [
                "雨夜",
                "雷雨",
                "室外",
                "亭子"
            ]
        }
    }
    
    project.config = project_config
    db.add(project)
    db.commit()
    
    print(f"✅ 创建项目: {project.name} (ID: {project.id})")
    print(f"   环境音配置: 启用，音量40%")
    
    return {
        "book_id": book.id,
        "chapter_id": chapter.id,
        "project_id": project.id
    }

def call_intelligent_preparation(project_id, chapter_id):
    """调用智能准备接口"""
    print(f"\n🧠 调用智能准备接口...")
    
    url = "http://localhost:8000/api/analysis/intelligent-preparation"
    data = {
        "project_id": project_id,
        "chapter_id": chapter_id,
        "enable_character_detection": True,
        "enable_scene_analysis": True
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 智能准备完成")
            print(f"   角色数量: {len(result.get('data', {}).get('characters', []))}")
            print(f"   段落数量: {len(result.get('data', {}).get('segments', []))}")
            return True
        else:
            print(f"❌ 智能准备失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 智能准备异常: {str(e)}")
        return False

def trigger_synthesis(project_id, chapter_id):
    """触发合成"""
    print(f"\n🎵 触发环境音合成...")
    
    url = f"http://localhost:8000/api/novel-reader/projects/{project_id}/chapters/{chapter_id}/start"
    data = {
        "parallel_tasks": 1,
        "enable_environment": True,
        "environment_volume": 0.4
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)
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
    
    url = f"http://localhost:8000/api/novel-reader/projects/{project_id}/progress"
    max_wait = 300  # 最多等5分钟
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                status = data.get('data', {}).get('status', 'unknown')
                progress = data.get('data', {}).get('progress', 0)
                
                print(f"   状态: {status}, 进度: {progress}%")
                
                if status == 'completed':
                    print(f"✅ 合成完成！")
                    return True
                elif status == 'failed':
                    print(f"❌ 合成失败")
                    return False
                
                time.sleep(3)
            else:
                print(f"❌ 进度查询失败: {response.status_code}")
                break
        except Exception as e:
            print(f"❌ 进度查询异常: {str(e)}")
            break
    
    print(f"⏰ 等待超时")
    return False

def check_result(project_id):
    """检查结果"""
    print(f"\n🔍 检查合成结果...")
    
    # 检查项目状态
    db = next(get_db())
    project = db.get(NovelProject, project_id)
    
    if project:
        print(f"   项目状态: {project.status}")
        print(f"   最终音频: {project.final_audio_path}")
        
        if project.final_audio_path and os.path.exists(project.final_audio_path):
            file_size = os.path.getsize(project.final_audio_path) / 1024 / 1024
            print(f"   文件大小: {file_size:.1f} MB")
            print(f"   完整路径: {os.path.abspath(project.final_audio_path)}")
            
            # 检查是否是混合音频
            if "mixed" in project.final_audio_path:
                print(f"✅ 包含环境音的混合音频文件")
            else:
                print(f"⚠️ 普通音频文件，可能没有环境音")
            
            return project.final_audio_path
        else:
            print(f"❌ 音频文件不存在")
    
    return None

def main():
    print("🎯 快速环境音测试 - 创建简短内容快速验证")
    
    # 检查后端服务
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ 后端服务异常，请先启动 python main.py")
            return
    except:
        print("❌ 后端服务未启动，请先启动 python main.py")
        return
    
    try:
        # 1. 创建测试数据
        result = create_simple_test_data()
        project_id = result['project_id']
        chapter_id = result['chapter_id']
        
        # 2. 智能准备
        if not call_intelligent_preparation(project_id, chapter_id):
            print("❌ 智能准备失败，终止测试")
            return
        
        # 3. 触发合成
        if not trigger_synthesis(project_id, chapter_id):
            print("❌ 合成启动失败，终止测试")
            return
        
        # 4. 等待完成
        if not wait_for_completion(project_id):
            print("❌ 合成未完成，请检查日志")
            return
        
        # 5. 检查结果
        audio_path = check_result(project_id)
        if audio_path:
            print(f"\n🎉 测试成功！")
            print(f"🎵 音频文件路径:")
            print(f"   {os.path.abspath(audio_path)}")
            print(f"\n💡 请播放这个文件，应该能听到:")
            print(f"   - 林雨和张明的对话")
            print(f"   - 雨夜环境音效")
            print(f"   - 雷声效果")
            print(f"   - 场景转换音效")
        else:
            print(f"❌ 测试失败，没有生成音频文件")
        
    except Exception as e:
        print(f"❌ 测试过程出错: {str(e)}")

if __name__ == "__main__":
    main() 