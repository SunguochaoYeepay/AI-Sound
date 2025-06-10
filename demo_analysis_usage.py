#!/usr/bin/env python3
"""
AI-Sound 大模型解析功能演示脚本
展示如何通过API使用书籍智能分析功能
"""

import requests
import json
import time
import asyncio
import websocket
from typing import Dict, Any, Optional

class AIAnalysisDemo:
    """AI分析功能演示类"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        
    def upload_book(self, title: str, author: str, content: str) -> Dict[str, Any]:
        """
        步骤1: 上传书籍到系统
        """
        print(f"📚 正在上传书籍: 《{title}》")
        
        # 模拟文件上传
        files = {
            'file': ('book.txt', content, 'text/plain')
        }
        data = {
            'title': title,
            'author': author,
            'description': f'{author}的作品《{title}》',
            'auto_detect_chapters': True
        }
        
        response = requests.post(f"{self.api_base}/books/", files=files, data=data)
        
        if response.status_code == 200:
            book_data = response.json()
            print(f"✅ 书籍上传成功，ID: {book_data['id']}")
            return book_data
        else:
            print(f"❌ 书籍上传失败: {response.text}")
            return None
    
    def detect_chapters(self, book_id: int, force_reprocess: bool = False) -> Dict[str, Any]:
        """
        步骤2: 检测章节结构
        """
        print(f"🔍 正在检测书籍 {book_id} 的章节结构...")
        
        payload = {
            "force_reprocess": force_reprocess,
            "detection_config": {
                "method": "auto",
                "patterns": [
                    "^第[一二三四五六七八九十\\d]+[章回节]",
                    "^Chapter \\d+",
                    "^\\d+\\."
                ]
            }
        }
        
        response = requests.post(f"{self.api_base}/books/{book_id}/detect-chapters", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 章节检测完成: {result}")
            return result
        else:
            print(f"❌ 章节检测失败: {response.text}")
            return None
    
    def create_project(self, book_id: int, project_name: str) -> Dict[str, Any]:
        """
        步骤3: 创建分析项目
        """
        print(f"🎬 正在创建项目: {project_name}")
        
        payload = {
            "name": project_name,
            "book_id": book_id,
            "description": "基于大模型的智能角色分析项目"
        }
        
        response = requests.post(f"{self.api_base}/projects/", json=payload)
        
        if response.status_code == 200:
            project_data = response.json()
            print(f"✅ 项目创建成功，ID: {project_data['id']}")
            return project_data
        else:
            print(f"❌ 项目创建失败: {response.text}")
            return None
    
    def create_analysis_session(self, project_id: int, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        步骤4: 创建分析会话 (核心功能)
        """
        print(f"🧠 正在创建智能分析会话...")
        
        session_payload = {
            "project_id": project_id,
            "session_name": f"项目{project_id}智能分析",
            "description": "使用大模型进行角色和对话分析",
            "target_type": config.get("target_type", "full_book"),
            "target_config": config.get("target_config", {}),
            "llm_config": {
                "llm_provider": config.get("llm_provider", "dify"),
                "llm_model": config.get("llm_model", "gpt-4"),
                "llm_workflow_id": config.get("llm_workflow_id", "demo_workflow"),
                "temperature": 0.7,
                "max_tokens": 4000
            },
            "analysis_params": {
                "detect_characters": True,
                "analyze_emotions": True,
                "recommend_voices": True,
                "batch_size": 3,
                "max_retries": 3,
                "include_narrator": True,
                "character_threshold": 0.8
            }
        }
        
        response = requests.post(f"{self.api_base}/analysis/sessions", json=session_payload)
        
        if response.status_code == 200:
            session_data = response.json()
            print(f"✅ 分析会话创建成功，ID: {session_data['id']}")
            return session_data
        else:
            print(f"❌ 分析会话创建失败: {response.text}")
            return None
    
    def start_analysis(self, session_id: int, force_restart: bool = False) -> bool:
        """
        步骤5: 启动智能分析
        """
        print(f"🚀 正在启动分析会话 {session_id}...")
        
        payload = {
            "force_restart": force_restart
        }
        
        response = requests.post(f"{self.api_base}/analysis/sessions/{session_id}/start", json=payload)
        
        if response.status_code == 200:
            print(f"✅ 分析任务启动成功")
            return True
        else:
            print(f"❌ 分析任务启动失败: {response.text}")
            return False
    
    def monitor_progress(self, session_id: int, timeout: int = 300) -> Dict[str, Any]:
        """
        步骤6: 监控分析进度
        """
        print(f"⏱️ 监控分析进度 (最大等待 {timeout} 秒)...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = requests.get(f"{self.api_base}/analysis/sessions/{session_id}/progress")
            
            if response.status_code == 200:
                progress_data = response.json()
                status = progress_data.get('status')
                progress = progress_data.get('progress', 0)
                
                print(f"📊 状态: {status}, 进度: {progress}%")
                
                if status == 'completed':
                    print("🎉 分析完成！")
                    return progress_data
                elif status == 'failed':
                    print(f"❌ 分析失败: {progress_data.get('error_message')}")
                    return None
                
            time.sleep(5)  # 每5秒检查一次
        
        print("⏰ 监控超时")
        return None
    
    def get_analysis_results(self, session_id: int, include_raw: bool = False) -> Dict[str, Any]:
        """
        步骤7: 获取分析结果
        """
        print(f"📋 获取分析结果...")
        
        params = {
            "include_raw": include_raw,
            "limit": 50
        }
        
        response = requests.get(f"{self.api_base}/analysis/sessions/{session_id}/results", params=params)
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ 获取到 {len(results)} 个分析结果")
            return results
        else:
            print(f"❌ 获取分析结果失败: {response.text}")
            return None
    
    def display_results(self, results: Dict[str, Any]):
        """
        显示分析结果
        """
        print("\n" + "="*60)
        print("🎭 AI智能分析结果展示")
        print("="*60)
        
        for i, result in enumerate(results, 1):
            print(f"\n📖 章节 {i} 分析结果:")
            print(f"   章节ID: {result.get('chapter_id')}")
            print(f"   置信度: {result.get('confidence_score', 0)}%")
            print(f"   处理时间: {result.get('processing_time', 0)}ms")
            
            # 显示识别的角色
            characters = result.get('detected_characters', [])
            if characters:
                print(f"\n   🎭 识别到 {len(characters)} 个角色:")
                for char in characters:
                    print(f"      - {char.get('name')}: {char.get('type')} ({char.get('gender')}, {char.get('age_group')})")
                    print(f"        推荐声音: {char.get('recommended_voice')}")
                    print(f"        性格特征: {', '.join(char.get('personality', []))}")
            
            # 显示对话段落
            dialogues = result.get('dialogue_segments', [])
            if dialogues:
                print(f"\n   💬 对话段落 (前3个示例):")
                for dialogue in dialogues[:3]:
                    speaker = dialogue.get('speaker', '未知')
                    text = dialogue.get('text', '')[:50] + "..."
                    emotion = dialogue.get('emotion', '')
                    print(f"      {speaker} ({emotion}): {text}")
            
            # 显示合成计划
            synthesis_plan = result.get('synthesis_plan', {})
            if synthesis_plan:
                mapping = synthesis_plan.get('character_mapping', {})
                print(f"\n   🎵 声音映射配置:")
                for char_name, voice_config in mapping.items():
                    voice_name = voice_config.get('voice_name')
                    print(f"      {char_name} → {voice_name}")
        
        print("\n" + "="*60)
    
    def run_complete_demo(self):
        """
        运行完整的演示流程
        """
        print("🎬 开始 AI-Sound 大模型解析功能完整演示")
        print("="*60)
        
        # 示例书籍内容
        sample_content = '''第一回 灵根育孕源流出 心性修持大道生

诗曰：
混沌未分天地乱，茫茫渺渺无人见。
自从盘古破鸿蒙，开辟从兹清浊辨。

第二回 悟彻菩提真妙理 断魔归本合元神

话说美猴王得了姓名，怡然踊跃，对菩提前作礼启谢。

"悟空，你在这里学些什么道理？"祖师问道。

悟空道："弟子时常听讲，也颇知些。"

"既如此，你再上前来，我教你个长生之道如何？"

悟空闻言，叩头谢恩道："愿老爷传授。"'''
        
        try:
            # 步骤1: 上传书籍
            book_data = self.upload_book("西游记演示", "吴承恩", sample_content)
            if not book_data:
                return False
            
            book_id = book_data['id']
            
            # 步骤2: 检测章节
            chapter_result = self.detect_chapters(book_id)
            if not chapter_result:
                return False
            
            # 步骤3: 创建项目
            project_data = self.create_project(book_id, f"《西游记演示》智能分析项目")
            if not project_data:
                return False
            
            project_id = project_data['id']
            
            # 步骤4: 创建分析会话
            analysis_config = {
                "target_type": "full_book",
                "llm_provider": "dify",
                "llm_model": "gpt-4",
                "llm_workflow_id": "demo_workflow_id"
            }
            
            session_data = self.create_analysis_session(project_id, analysis_config)
            if not session_data:
                return False
            
            session_id = session_data['id']
            
            # 步骤5: 启动分析
            if not self.start_analysis(session_id):
                return False
            
            # 步骤6: 监控进度
            progress_result = self.monitor_progress(session_id, timeout=60)
            
            # 步骤7: 获取结果 (模拟)
            print("\n📋 模拟分析结果 (由于演示环境限制，显示预期结果格式):")
            
            # 模拟分析结果
            mock_results = [
                {
                    "chapter_id": 1,
                    "confidence_score": 95,
                    "processing_time": 8500,
                    "detected_characters": [
                        {
                            "name": "孙悟空",
                            "type": "main",
                            "gender": "male",
                            "age_group": "adult",
                            "personality": ["勇敢", "机智", "顽皮"],
                            "recommended_voice": "活泼男声"
                        },
                        {
                            "name": "菩提祖师",
                            "type": "supporting",
                            "gender": "male",
                            "age_group": "elder",
                            "personality": ["睿智", "严肃", "慈祥"],
                            "recommended_voice": "沉稳长者"
                        }
                    ],
                    "dialogue_segments": [
                        {
                            "order": 1,
                            "text": "悟空，你在这里学些什么道理？",
                            "speaker": "菩提祖师",
                            "type": "dialogue",
                            "emotion": "询问"
                        },
                        {
                            "order": 2,
                            "text": "弟子时常听讲，也颇知些。",
                            "speaker": "孙悟空",
                            "type": "dialogue", 
                            "emotion": "谦逊"
                        }
                    ],
                    "synthesis_plan": {
                        "character_mapping": {
                            "孙悟空": {
                                "voice_name": "活泼男声",
                                "parameters": {"speed": 1.0, "pitch": 1.1}
                            },
                            "菩提祖师": {
                                "voice_name": "沉稳长者",
                                "parameters": {"speed": 0.9, "pitch": 0.9}
                            },
                            "旁白": {
                                "voice_name": "温柔女声",
                                "parameters": {"speed": 1.0, "pitch": 1.0}
                            }
                        }
                    }
                }
            ]
            
            self.display_results(mock_results)
            
            print("\n🎉 演示完成！")
            print("\n💡 总结:")
            print("   ✅ 自动识别角色: 孙悟空、菩提祖师")  
            print("   ✅ 分析对话情感: 询问、谦逊等")
            print("   ✅ 推荐声音配置: 活泼男声、沉稳长者等")
            print("   ✅ 生成合成计划: 完整的JSON配置")
            print("\n📝 注意: 实际使用时需要配置有效的大模型API服务")
            
            return True
            
        except Exception as e:
            print(f"❌ 演示过程中发生错误: {str(e)}")
            return False

def main():
    """主函数"""
    print("🎭 AI-Sound 大模型解析功能演示")
    print("本演示将展示如何使用基于大模型的书籍智能解析功能\n")
    
    # 检查后端服务
    demo = AIAnalysisDemo()
    
    try:
        response = requests.get(f"{demo.base_url}/health", timeout=5)
        if response.status_code != 200:
            print("❌ 后端服务未启动，请先启动 AI-Sound 后端服务")
            print("   启动命令: cd platform/backend && python main.py")
            return
    except requests.exceptions.RequestException:
        print("❌ 无法连接到后端服务，请确保服务已启动")
        print("   启动命令: cd platform/backend && python main.py")
        return
    
    # 运行演示
    success = demo.run_complete_demo()
    
    if success:
        print("\n🚀 了解更多:")
        print("   📚 查看完整文档: AI-Sound大模型解析功能使用指南.md")
        print("   🌐 Web界面: http://localhost:3000")
        print("   📖 API文档: http://localhost:8000/docs")
    else:
        print("\n❌ 演示未能完全完成，可能需要配置实际的LLM服务")

if __name__ == "__main__":
    main() 