#!/usr/bin/env python3
"""
基于现有项目的环境音混合测试数据
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.models import NovelProject, Book, BookChapter, VoiceProfile, AnalysisResult

def update_project_for_environment_test(db, project_id=42):
    """更新现有项目以支持环境音测试"""
    
    project = db.get(NovelProject, project_id)
    if not project:
        print(f"❌ 项目 {project_id} 不存在")
        return None
    
    print(f"📝 更新项目 {project.id}: {project.name}")
    
    # 更新项目配置以包含环境音配置
    current_config = project.config or {}
    
    # 添加环境音设置
    current_config["environment_settings"] = {
        "enable_environment": True,
        "environment_volume": 0.3,
        "auto_scene_detection": True,
        "scene_transition_fade": 2.0
    }
    
    project.config = current_config
    project.description = f"{project.description or ''} [已配置环境音混合测试]"
    
    db.commit()
    print(f"✅ 项目设置已更新，支持环境音混合")
    return project

def create_test_analysis_for_project(db, project_id):
    """为现有项目创建测试分析结果"""
    
    project = db.get(NovelProject, project_id)
    if not project:
        return None
    
    # 检查是否已有分析结果
    existing_result = db.query(AnalysisResult).filter(
        AnalysisResult.project_id == project_id
    ).first()
    
    if existing_result:
        print(f"项目 {project_id} 已有分析结果，更新环境音配置...")
        
        # 更新现有结果的数据以包含环境音信息
        result_data = existing_result.result_data or {}
        
        # 确保有segments数据
        if "synthesis_plan" in result_data and "segments" in result_data["synthesis_plan"]:
            segments = result_data["synthesis_plan"]["segments"]
            
            # 为每个段落添加场景信息
            for i, segment in enumerate(segments):
                if "scene_info" not in segment:
                    # 根据内容推断场景
                    text = segment.get("text", "")
                    
                    if "雨" in text or "雷" in text or "闪电" in text:
                        segment["scene_info"] = {
                            "location": "室外",
                            "weather": "雨夜",
                            "time": "夜晚",
                            "atmosphere": "悬疑"
                        }
                    elif "森林" in text or "树" in text or "鸟" in text:
                        segment["scene_info"] = {
                            "location": "森林",
                            "weather": "晴朗",
                            "time": "白天",
                            "atmosphere": "自然"
                        }
                    elif "海" in text or "浪" in text or "海鸥" in text:
                        segment["scene_info"] = {
                            "location": "海边",
                            "weather": "晴朗",
                            "time": "黄昏",
                            "atmosphere": "浪漫"
                        }
                    else:
                        segment["scene_info"] = {
                            "location": "室内",
                            "weather": "正常",
                            "time": "白天",
                            "atmosphere": "平静"
                        }
        
        existing_result.result_data = result_data
        db.commit()
        print(f"✅ 已更新分析结果的环境音配置")
        return existing_result
    
    else:
        print(f"项目 {project_id} 暂无分析结果，请先进行智能准备")
        return None

def main():
    """主函数"""
    print("🚀 创建环境音混合测试配置...")
    
    db = next(get_db())
    
    try:
        # 选择现有项目进行测试 (项目42看起来是completed状态)
        test_project_id = 42
        
        print(f"\n🎬 配置项目 {test_project_id} 进行环境音测试...")
        project = update_project_for_environment_test(db, test_project_id)
        
        if project:
            print(f"\n🧠 配置分析结果...")
            analysis = create_test_analysis_for_project(db, test_project_id)
            
            print(f"\n✅ 环境音混合测试配置完成！")
            print(f"📊 测试信息:")
            print(f"   - 项目ID: {project.id}")
            print(f"   - 项目名称: {project.name}")
            print(f"   - 项目状态: {project.status}")
            print(f"   - 环境音已启用: ✅")
            
            print(f"\n🎯 测试步骤:")
            print(f"   1. 访问前端合成中心")
            print(f"   2. 选择项目 '{project.name}' (ID: {project.id})")
            print(f"   3. 在合成选项中查看 '🌍 环境音混合' 选项")
            print(f"   4. 设置环境音音量为 0.3 (30%)")
            print(f"   5. 开始合成测试")
            
            print(f"\n🎵 预期效果:")
            print(f"   - 系统会根据文本内容自动检测场景")
            print(f"   - 为不同场景添加对应的环境音")
            print(f"   - 雨夜场景: 雨声、雷声")
            print(f"   - 森林场景: 鸟叫、风声") 
            print(f"   - 海边场景: 海浪声、海鸥叫声")
            print(f"   - 室内场景: 轻微环境音")
            
            print(f"\n📝 注意事项:")
            print(f"   - 确保TangoFlux服务正常运行")
            print(f"   - 环境音会在每个语音段落后生成")
            print(f"   - 首次生成可能需要较长时间")
            
        else:
            print("❌ 项目配置失败")
            
    except Exception as e:
        print(f"❌ 配置失败: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main() 