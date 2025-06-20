#!/usr/bin/env python3
"""
最终环境音混合测试配置
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.models import NovelProject, Book, BookChapter, VoiceProfile

def main():
    """主函数"""
    print("🚀 最终环境音混合测试配置...")
    
    db = next(get_db())
    
    try:
        # 使用现有项目42
        project_id = 42
        project = db.get(NovelProject, project_id)
        
        if not project:
            print(f"❌ 项目 {project_id} 不存在")
            return
        
        print(f"📝 配置项目 {project.id}: {project.name}")
        
        # 更新项目配置以支持环境音
        if not project.config:
            project.config = {}
        
        # 添加环境音混合配置
        project.config["environment_settings"] = {
            "enable_environment": True,
            "environment_volume": 0.3,
            "auto_scene_detection": True,
            "scene_transition_fade": 2.0,
            "supported_scenes": [
                "雨夜", "森林", "海边", "室内", "街道", "山谷", "城市"
            ]
        }
        
        # 标记JSON字段已修改
        from sqlalchemy.orm import attributes
        attributes.flag_modified(project, 'config')
        
        # 更新描述
        if not project.description:
            project.description = ""
        if "[环境音测试]" not in project.description:
            project.description += " [环境音测试已配置]"
        
        db.commit()
        
        print(f"✅ 环境音混合测试配置完成！")
        print(f"\n📊 测试信息:")
        print(f"   - 项目ID: {project.id}")
        print(f"   - 项目名称: {project.name}")
        print(f"   - 项目状态: {project.status}")
        print(f"   - 环境音配置: ✅ 已启用")
        print(f"   - 环境音音量: 30%")
        
        print(f"\n🎯 测试步骤:")
        print(f"   1. 确保后端服务运行: python main.py")
        print(f"   2. 确保TangoFlux服务运行 (端口7930)")
        print(f"   3. 访问前端: http://localhost:3000")
        print(f"   4. 进入 '合成中心' 页面")
        print(f"   5. 选择项目 '{project.name}' (ID: {project.id})")
        print(f"   6. 查看 '🌍 环境音混合' 选项")
        print(f"   7. 开始合成测试")
        
        print(f"\n🎵 环境音功能说明:")
        print(f"   - 系统会自动分析文本内容")
        print(f"   - 根据场景描述生成对应环境音")
        print(f"   - 与语音内容智能混合")
        print(f"   - 支持场景转换淡入淡出")
        
        print(f"\n⚠️  注意事项:")
        print(f"   - 首次使用需要下载TangoFlux模型")
        print(f"   - 环境音生成可能需要较长时间")
        print(f"   - 建议在GPU环境下运行")
        print(f"   - 环境音文件会保存在outputs目录")
        
        # 检查现有声音档案
        voices = db.query(VoiceProfile).limit(5).all()
        print(f"\n🎤 可用声音档案:")
        for voice in voices:
            print(f"   - {voice.name} ({voice.type})")
        
        print(f"\n🔧 技术架构:")
        print(f"   - TTS: MegaTTS3 (语音合成)")
        print(f"   - 环境音: TangoFlux (文本到音频)")
        print(f"   - 混合: 顺序生成协调器")
        print(f"   - 时间轴: 智能时间轴生成器")
        
    except Exception as e:
        print(f"❌ 配置失败: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main() 