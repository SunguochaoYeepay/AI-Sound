#!/usr/bin/env python3
"""
完整的环境音工作流测试脚本
从新增项目、关联书籍、分析、生成、混音完整测试
"""

import sys
import os
import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models.environment_generation import EnvironmentProject
from app.models.novel_project import NovelProject
from app.models.environment_sound import EnvironmentSound
from app.services.tangoflux_environment_generator import TangoFluxEnvironmentGenerator
from app.services.environment_project_service import EnvironmentProjectService

class CompleteWorkflowTester:
    """完整工作流测试器"""
    
    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.novel_project_id = None  # 小说项目ID
        self.env_project_id = None    # 环境音项目ID
        self.chapter_id = "830"       # 测试章节ID
        
    async def test_step1_create_book_and_project(self) -> bool:
        """步骤1：创建书籍和小说项目"""
        print("📚 步骤1：创建书籍和小说项目")
        print("=" * 50)
        
        try:
            # 获取数据库会话
            db = next(get_db())
            
            # 导入Book模型
            from app.models.book import Book
            
            # 创建书籍
            book = Book(
                title="古玉情",
                author="测试作者",
                description="这是一个测试书籍，用于环境音工作流测试",
                content="这是一个测试书籍的内容，包含多个章节的环境音描述。",
                chapters_data=json.dumps({
                    "830": {
                        "title": "第一章",
                        "content": "这是一个测试章节，包含脚步声、马蹄声等环境音。"
                    },
                    "831": {
                        "title": "第二章", 
                        "content": "这是第二章，包含娇喝声、脚步声等环境音。"
                    },
                    "832": {
                        "title": "第三章",
                        "content": "这是第三章，包含脚步声等环境音。"
                    }
                }, ensure_ascii=False),
                status="published",
                word_count=1000,
                chapter_count=3
            )
            
            db.add(book)
            db.commit()
            db.refresh(book)
            
            print(f"✅ 创建书籍成功: ID {book.id}")
            print(f"📖 书籍标题: {book.title}")
            print(f"📊 书籍状态: {book.status}")
            print(f"📋 章节数量: {book.chapter_count}")
            
            # 创建小说项目
            novel_project = NovelProject(
                name="古玉情项目",
                book_id=book.id,
                status="completed",
                config={
                    "character_mapping": {},
                    "settings": {}
                }
            )
            
            db.add(novel_project)
            db.commit()
            db.refresh(novel_project)
            
            self.novel_project_id = novel_project.id
            print(f"✅ 创建小说项目成功: ID {self.novel_project_id}")
            print(f"📖 项目名称: {novel_project.name}")
            print(f"📊 项目状态: {novel_project.status}")
            print(f"📋 关联书籍: {novel_project.book_id}")
            
            db.close()
            return True
            
        except Exception as e:
            print(f"❌ 步骤1失败: {str(e)}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")
            return False
    
    async def test_step2_create_env_project(self) -> bool:
        """步骤2：创建环境音项目"""
        print("\n🎵 步骤2：创建环境音项目")
        print("=" * 50)
        
        try:
            # 获取数据库会话
            db = next(get_db())
            
            # 获取小说项目对应的书籍ID
            novel_project = db.query(NovelProject).filter(NovelProject.id == self.novel_project_id).first()
            if not novel_project:
                print("❌ 未找到小说项目")
                db.close()
                return False
            
            # 创建环境音项目
            env_project = EnvironmentProject(
                name="古玉情环境音项目",
                description="古玉情书籍的环境音生成项目",
                book_id=novel_project.book_id,  # 使用书籍ID
                status="created",
                analysis_result=None
            )
            
            db.add(env_project)
            db.commit()
            db.refresh(env_project)
            
            self.env_project_id = env_project.id
            print(f"✅ 创建环境音项目成功: ID {self.env_project_id}")
            print(f"📊 项目状态: {env_project.status}")
            print(f"📋 关联小说项目: {env_project.novel_project_id}")
            
            db.close()
            return True
            
        except Exception as e:
            print(f"❌ 步骤2失败: {str(e)}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")
            return False
    
    async def test_step3_analysis(self) -> bool:
        """步骤3：环境音分析"""
        print("\n🔍 步骤3：环境音分析")
        print("=" * 50)
        
        try:
            # 调用分析API
            async with aiohttp.ClientSession() as session:
                # 准备请求数据
                request_data = {
                    "project_id": self.env_project_id,
                    "synthesis_plan": [
                        {
                            "speaker": "旁白",
                            "character": "旁白",
                            "text": "这是一个测试章节，包含脚步声、马蹄声等环境音。"
                        },
                        {
                            "speaker": "旁白",
                            "character": "旁白", 
                            "text": "这是第二章，包含娇喝声、脚步声等环境音。"
                        },
                        {
                            "speaker": "旁白",
                            "character": "旁白",
                            "text": "这是第三章，包含脚步声等环境音。"
                        }
                    ],
                    "options": {}
                }
                
                print(f"🔄 调用分析API: POST {self.base_url}/api/v1/environment-generation/analyze")
                print(f"   请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
                
                # 发送分析请求
                async with session.post(
                    f"{self.base_url}/api/v1/environment-generation/analyze",
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    
                    print(f"📡 响应状态: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ 分析成功: {json.dumps(result, ensure_ascii=False, indent=2)}")
                        
                        if result.get('success'):
                            print("✅ 分析API返回成功")
                            
                            # 分析是同步完成的，直接检查结果
                            analysis_result = result.get('analysis_result')
                            if analysis_result:
                                tracks = analysis_result.get('environment_tracks', [])
                                print(f"✅ 分析完成，找到 {len(tracks)} 个环境音轨道")
                                
                                # 显示轨道信息
                                for i, track in enumerate(tracks):
                                    keywords = track.get('environment_keywords', [])
                                    print(f"   轨道{i}: {', '.join(keywords)}")
                                    print(f"       场景描述: {track.get('scene_description', '无描述')}")
                                    print(f"       时长: {track.get('duration', '未知')}秒")
                                
                                return True
                            else:
                                print("❌ 分析结果为空")
                                return False
                        else:
                            print(f"❌ 分析API返回失败: {result.get('error')}")
                            return False
                    else:
                        error_text = await response.text()
                        print(f"❌ 分析API错误: {response.status} - {error_text}")
                        return False
            
        except Exception as e:
            print(f"❌ 步骤3失败: {str(e)}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")
            return False
    
    async def check_analysis_result(self) -> Dict:
        """检查分析结果"""
        try:
            # 检查项目状态
            db = next(get_db())
            env_service = EnvironmentProjectService(db)
            env_project = env_service.get_by_project_id(self.env_project_id)
            
            if env_project and env_project.analysis_result:
                db.close()
                return env_project.analysis_result
            
            db.close()
            return None
            
        except Exception as e:
            print(f"❌ 检查分析结果失败: {str(e)}")
            return None
    
    async def test_step4_generation(self) -> bool:
        """步骤4：环境音生成"""
        print("\n🎵 步骤4：环境音生成")
        print("=" * 50)
        
        try:
            # 获取数据库会话
            db = next(get_db())
            
            # 获取项目
            env_service = EnvironmentProjectService(db)
            env_project = env_service.get_by_project_id(self.env_project_id)
            
            if not env_project:
                print("❌ 未找到环境音项目")
                db.close()
                return False
            
            # 获取需要生成的轨道
            # 检查分析结果格式
            print(f"🔍 分析结果类型: {type(env_project.analysis_result)}")
            print(f"🔍 分析结果内容: {env_project.analysis_result}")
            
            if isinstance(env_project.analysis_result, dict) and 'environment_tracks' in env_project.analysis_result:
                # 单章节格式
                tracks = env_project.analysis_result['environment_tracks']
                print(f"✅ 使用单章节格式，找到 {len(tracks)} 个轨道")
            elif isinstance(env_project.analysis_result, dict) and self.chapter_id in env_project.analysis_result:
                # 多章节格式
                chapter_data = env_project.analysis_result[self.chapter_id]
                tracks = chapter_data['environment_tracks']
                print(f"✅ 使用多章节格式，章节 {self.chapter_id}，找到 {len(tracks)} 个轨道")
            else:
                print("❌ 分析结果格式不支持")
                print(f"🔍 期望的章节ID: {self.chapter_id}")
                print(f"🔍 可用的键: {list(env_project.analysis_result.keys()) if isinstance(env_project.analysis_result, dict) else 'N/A'}")
                db.close()
                return False
            
            # 筛选未生成的轨道
            tracks_to_generate = []
            for i, track in enumerate(tracks):
                if not track.get('generated_file_path'):
                    tracks_to_generate.append((i, track))
            
            if not tracks_to_generate:
                print("✅ 所有轨道都已生成，跳过生成步骤")
                db.close()
                return True
            
            print(f"🔄 需要生成 {len(tracks_to_generate)} 个轨道")
            
            # 创建生成器
            generator = TangoFluxEnvironmentGenerator()
            
            # 检查服务健康状态
            if not await generator.check_service_health():
                print("❌ TangoFlux服务不可用")
                db.close()
                return False
            
            print("✅ TangoFlux服务正常")
            
            # 生成任务ID
            task_id = f"test_gen_{int(time.time())}"
            
            # 开始生成
            print("🔄 开始生成环境音...")
            result = await generator.generate_project_environment_sounds(
                project_id=self.env_project_id,
                tracks_to_generate=tracks_to_generate,
                task_id=task_id,
                chapter_id=self.chapter_id
            )
            
            if not result.get('success'):
                print(f"❌ 生成失败: {result.get('error')}")
                db.close()
                return False
            
            print(f"✅ 生成完成: {result.get('message')}")
            print(f"   成功轨道: {result.get('successful_tracks')}")
            print(f"   失败轨道: {result.get('failed_tracks')}")
            
            # 验证生成结果
            db.refresh(env_project)
            
            # 检查分析结果格式
            if isinstance(env_project.analysis_result, dict) and 'environment_tracks' in env_project.analysis_result:
                # 单章节格式
                tracks = env_project.analysis_result['environment_tracks']
            elif isinstance(env_project.analysis_result, dict) and self.chapter_id in env_project.analysis_result:
                # 多章节格式
                chapter_data = env_project.analysis_result[self.chapter_id]
                tracks = chapter_data['environment_tracks']
            else:
                print("❌ 分析结果格式不支持")
                db.close()
                return False
            
            generated_count = 0
            for i, track in enumerate(tracks):
                if track.get('generated_file_path'):
                    generated_count += 1
                    print(f"   轨道{i}: 生成路径 = {track.get('generated_file_path')}")
            
            print(f"✅ 验证完成: {generated_count} 个轨道已生成")
            
            db.close()
            return True
            
        except Exception as e:
            print(f"❌ 步骤4失败: {str(e)}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")
            return False
    
    async def test_step5_mixing(self) -> bool:
        """步骤5：混音功能"""
        print("\n🎧 步骤5：混音功能")
        print("=" * 50)
        
        try:
            # 调用混音API
            async with aiohttp.ClientSession() as session:
                # 准备请求数据
                request_data = {}
                
                print(f"🔄 调用混音API: POST {self.base_url}/api/v1/environment-generation/mix/{self.env_project_id}")
                print(f"   请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
                
                # 发送混音请求
                async with session.post(
                    f"{self.base_url}/api/v1/environment-generation/mix/{self.env_project_id}",
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    print(f"📡 响应状态: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ 混音成功: {json.dumps(result, ensure_ascii=False, indent=2)}")
                        
                        # 验证混音结果
                        if result.get('success'):
                            print("✅ 混音API返回成功")
                            
                            # 获取任务ID
                            task_id = result.get('data', {}).get('task_id')
                            if task_id:
                                print(f"✅ 混音任务ID: {task_id}")
                                
                                                                                                  # 等待混音任务完成
                                print("⏳ 等待混音任务完成...")
                                 
                                # 轮询检查混音状态，最多等待120秒
                                max_wait_time = 120  # 120秒
                                check_interval = 3   # 每3秒检查一次
                                waited_time = 0
                                 
                                while waited_time < max_wait_time:
                                    await asyncio.sleep(check_interval)
                                    waited_time += check_interval
                                    
                                    print(f"⏳ 已等待 {waited_time} 秒...")
                                    
                                    # 检查混音结果
                                    mixed_file_path = await self.check_mixing_result(task_id)
                                    if mixed_file_path:
                                        print(f"✅ 混音完成，文件路径: {mixed_file_path}")
                                        return True
                                
                                print(f"❌ 混音任务超时（{max_wait_time}秒）")
                                return False
                            else:
                                print("❌ 混音API未返回任务ID")
                                return False
                        else:
                            print(f"❌ 混音API返回失败: {result.get('error')}")
                            return False
                    else:
                        error_text = await response.text()
                        print(f"❌ 混音API错误: {response.status} - {error_text}")
                        return False
            
        except Exception as e:
            print(f"❌ 步骤5失败: {str(e)}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")
            return False
    
    async def check_mixing_result(self, task_id: str) -> str:
        """检查混音任务结果"""
        try:
            # 检查项目状态
            db = next(get_db())
            env_service = EnvironmentProjectService(db)
            env_project = env_service.get_by_project_id(self.env_project_id)
            
            if env_project and env_project.matching_result:
                mixed_file_path = env_project.matching_result.get('mixed_file_path')
                if mixed_file_path:
                    print(f"🔍 找到混音文件路径: {mixed_file_path}")
                    if os.path.exists(mixed_file_path):
                        file_size = os.path.getsize(mixed_file_path)
                        print(f"✅ 混音文件存在，大小: {file_size} 字节")
                        db.close()
                        return mixed_file_path
                    else:
                        print(f"❌ 混音文件不存在: {mixed_file_path}")
                else:
                    print("❌ 混音文件路径为空")
            else:
                print("❌ 项目或混音结果为空")
            
            db.close()
            return None
            
        except Exception as e:
            print(f"❌ 检查混音结果失败: {str(e)}")
            return None
    
    async def verify_persistence(self) -> bool:
        """验证持久化结果"""
        print("🔍 验证混音任务生成与混音结果的持久化保存")
        
        try:
            # 检查项目状态
            db = next(get_db())
            env_service = EnvironmentProjectService(db)
            env_project = env_service.get_by_project_id(self.env_project_id)
            
            if not env_project:
                print("❌ 环境音项目不存在")
                db.close()
                return False
            
            print(f"✅ 环境音项目存在: ID {env_project.id}")
            print(f"📊 项目状态: {env_project.status}")
            print(f"📋 项目名称: {env_project.name}")
            
            # 检查分析结果持久化
            if env_project.analysis_result:
                print("✅ 分析结果已持久化")
                if isinstance(env_project.analysis_result, dict):
                    if 'environment_tracks' in env_project.analysis_result:
                        tracks = env_project.analysis_result['environment_tracks']
                        print(f"📊 单章节格式: {len(tracks)} 个轨道")
                        generated_count = sum(1 for track in tracks if track.get('generated_file_path'))
                        print(f"🎵 已生成轨道: {generated_count}/{len(tracks)}")
                    else:
                        # 多章节格式
                        chapter_count = len(env_project.analysis_result)
                        print(f"📊 多章节格式: {chapter_count} 个章节")
                        total_tracks = 0
                        total_generated = 0
                        for chapter_id, chapter_data in env_project.analysis_result.items():
                            if isinstance(chapter_data, dict) and 'environment_tracks' in chapter_data:
                                tracks = chapter_data['environment_tracks']
                                total_tracks += len(tracks)
                                generated = sum(1 for track in tracks if track.get('generated_file_path'))
                                total_generated += generated
                                print(f"   章节 {chapter_id}: {generated}/{len(tracks)} 个轨道已生成")
                        print(f"🎵 总计: {total_generated}/{total_tracks} 个轨道已生成")
            else:
                print("❌ 分析结果未持久化")
                db.close()
                return False
            
            # 检查混音结果持久化
            if env_project.matching_result:
                print("✅ 混音结果已持久化")
                print(f"📋 混音结果内容: {env_project.matching_result}")
                
                mixed_file_path = env_project.matching_result.get('mixed_file_path')
                if mixed_file_path:
                    print(f"🎵 混音文件路径: {mixed_file_path}")
                    if os.path.exists(mixed_file_path):
                        file_size = os.path.getsize(mixed_file_path)
                        print(f"✅ 混音文件存在，大小: {file_size} 字节")
                        
                        # 检查其他混音信息
                        mixed_duration = env_project.matching_result.get('mixed_duration')
                        mixed_tracks_count = env_project.matching_result.get('mixed_tracks_count')
                        mixed_at = env_project.matching_result.get('mixed_at')
                        
                        print(f"⏱️ 混音时长: {mixed_duration} 秒")
                        print(f"🎵 混音轨道数: {mixed_tracks_count}")
                        print(f"🕐 混音时间: {mixed_at}")
                        
                        # 检查环境音数据库记录
                        from app.models.environment_sound import EnvironmentSound
                        env_sounds = db.query(EnvironmentSound).filter(
                            EnvironmentSound.environment_project_id == self.env_project_id
                        ).all()
                        
                        print(f"🎵 环境音数据库记录: {len(env_sounds)} 个")
                        for sound in env_sounds:
                            print(f"   环境音 {sound.id}: {sound.name}, 文件: {sound.file_path}")
                            if sound.file_path and os.path.exists(sound.file_path):
                                print(f"   ✅ 文件存在，大小: {os.path.getsize(sound.file_path)} 字节")
                            else:
                                print(f"   ❌ 文件不存在")
                        
                        db.close()
                        return True
                    else:
                        print(f"❌ 混音文件不存在: {mixed_file_path}")
                        db.close()
                        return False
                else:
                    print("❌ 混音文件路径为空")
                    db.close()
                    return False
            else:
                print("❌ 混音结果未持久化")
                db.close()
                return False
                
        except Exception as e:
            print(f"❌ 验证持久化失败: {str(e)}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")
            db.close()
            return False
    
    async def cleanup(self):
        """清理测试数据"""
        print("\n🧹 清理测试数据")
        print("=" * 50)
        
        try:
            # 获取数据库会话
            db = next(get_db())
            
            # 导入Book模型
            from app.models.book import Book
            
            # 删除环境音项目
            if self.env_project_id:
                env_project = db.query(EnvironmentProject).filter(EnvironmentProject.id == self.env_project_id).first()
                if env_project:
                    db.delete(env_project)
                    print(f"✅ 删除环境音项目: {self.env_project_id}")
            
            # 删除小说项目
            if self.novel_project_id:
                novel_project = db.query(NovelProject).filter(NovelProject.id == self.novel_project_id).first()
                if novel_project:
                    # 获取关联的书籍ID
                    book_id = novel_project.book_id
                    db.delete(novel_project)
                    print(f"✅ 删除小说项目: {self.novel_project_id}")
                    
                    # 删除关联的书籍
                    if book_id:
                        book = db.query(Book).filter(Book.id == book_id).first()
                        if book:
                            db.delete(book)
                            print(f"✅ 删除书籍: {book_id}")
            
            db.commit()
            db.close()
            
        except Exception as e:
            print(f"❌ 清理失败: {str(e)}")
    
    async def run_complete_test(self):
        """运行完整测试"""
        print("🧪 开始完整的环境音工作流测试")
        print("=" * 60)
        
        try:
            # 步骤1：创建书籍和小说项目
            step1_result = await self.test_step1_create_book_and_project()
            if not step1_result:
                print("❌ 步骤1失败，停止测试")
                return False
            
            # 步骤2：创建环境音项目
            step2_result = await self.test_step2_create_env_project()
            if not step2_result:
                print("❌ 步骤2失败，停止测试")
                return False
            
            # 步骤3：环境音分析
            step3_result = await self.test_step3_analysis()
            if not step3_result:
                print("❌ 步骤3失败，停止测试")
                return False
            
            # 步骤4：环境音生成
            step4_result = await self.test_step4_generation()
            if not step4_result:
                print("❌ 步骤4失败，停止测试")
                return False
            
            # 步骤5：混音
            step5_result = await self.test_step5_mixing()
            if not step5_result:
                print("❌ 步骤5失败，停止测试")
                return False
            
            # 步骤6：验证持久化结果
            print("\n🔍 步骤6：验证持久化结果")
            print("=" * 50)
            persistence_result = await self.verify_persistence()
            if not persistence_result:
                print("❌ 持久化验证失败")
                return False
            
            print("\n🎉 完整测试通过！")
            print("=" * 60)
            print("✅ 新增项目 -> 关联书籍 -> 分析 -> 生成 -> 混音 -> 持久化验证 全流程测试成功")
            return True
            
        except Exception as e:
            print(f"❌ 测试过程中发生异常: {str(e)}")
            return False
        finally:
            # 等待一段时间确保后台任务完成
            print("⏳ 等待后台任务完成...")
            await asyncio.sleep(5)
            # 注意：不在这里清理测试数据，让用户手动清理
            print("📝 测试数据保留，请手动清理")

async def main():
    """主函数"""
    tester = CompleteWorkflowTester()
    await tester.run_complete_test()

if __name__ == "__main__":
    asyncio.run(main())
