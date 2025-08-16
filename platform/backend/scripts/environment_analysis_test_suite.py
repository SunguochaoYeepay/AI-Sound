#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境音分析测试套件
包含所有有用的测试脚本，用于验证环境音分析功能
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.narration_environment_analyzer import NarrationEnvironmentAnalyzer
from app.services.chapter_environment_analyzer import ChapterEnvironmentAnalyzer

class EnvironmentAnalysisTestSuite:
    """环境音分析测试套件"""
    
    def __init__(self):
        self.narration_analyzer = NarrationEnvironmentAnalyzer()
        self.chapter_analyzer = ChapterEnvironmentAnalyzer()
        
        # 测试数据
        self.test_cases = {
            "古玉2第一章": {
                "description": "真实项目 - 古玉2第一章穿越",
                "synthesis_plan": [
                    {
                        "segment_id": 1,
                        "text": "博物馆的空调发出轻微嗡鸣，林渊盯着展柜里的汉代青铜剑，指腹无意识摩挲着口袋里的玉佩。那是他在老宅阁楼发现的古物，温润的羊脂玉上刻着不知名的符文。",
                        "speaker": "旁白",
                        "emotion": "neutral"
                    },
                    {
                        "segment_id": 2,
                        "text": "\"叮 ——\" 手机震动打断思绪，是导师发来的消息：\"新出土的文物需要你立即去现场。\"",
                        "speaker": "旁白",
                        "emotion": "urgent"
                    }
                ]
            },
            "雨夜古宅": {
                "description": "测试场景 - 雨夜古宅悬疑",
                "synthesis_plan": [
                    {
                        "segment_id": 1,
                        "text": "夜深人静，大雨如注。林雨推开古宅沉重的木门，门轴发出吱呀的声响。",
                        "speaker": "旁白",
                        "emotion": "neutral"
                    },
                    {
                        "segment_id": 2,
                        "text": "闪电划过天空，照亮了客厅里积满灰尘的家具。雷声轰鸣，让人心跳加速。",
                        "speaker": "旁白",
                        "emotion": "dramatic"
                    }
                ]
            }
        }
    
    async def test_narration_analyzer(self, test_name: str, synthesis_plan: List[Dict[str, Any]]):
        """测试旁白环境分析器"""
        print(f"🧪 测试 {test_name}")
        print(f"📝 描述: {self.test_cases[test_name]['description']}")
        print(f"📊 段落数量: {len(synthesis_plan)}")
        print()
        
        try:
            start_time = datetime.now()
            
            # 执行分析
            result = await self.narration_analyzer.extract_and_analyze_narration_batch(synthesis_plan)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"✅ 分析完成！耗时: {duration:.2f}秒")
            print()
            
            # 显示结果
            if isinstance(result, dict) and 'environment_tracks' in result:
                tracks = result['environment_tracks']
                print(f"🎵 识别到 {len(tracks)} 个环境音轨道:")
                print()
                
                for i, track in enumerate(tracks, 1):
                    print(f"轨道 {i}:")
                    print(f"  场景: {track.get('scene_description', 'N/A')}")
                    print(f"  关键词: {', '.join(track.get('environment_keywords', []))}")
                    print(f"  时长: {track.get('duration', 0)}秒")
                    print(f"  强度: {track.get('intensity', 'N/A')}")
                    print(f"  类型: {track.get('track_type', 'N/A')}")
                    print(f"  置信度: {track.get('confidence_score', 0)}")
                    print()
            else:
                print("❌ 没有识别到环境音轨道")
                print(f"返回结果类型: {type(result)}")
                if isinstance(result, dict):
                    print(f"返回结果键: {list(result.keys())}")
            
            return result
            
        except Exception as e:
            print(f"❌ 分析失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def test_chapter_analyzer(self, test_name: str, synthesis_plan: List[Dict[str, Any]]):
        """测试章节环境分析器"""
        print(f"🧪 测试章节分析器 - {test_name}")
        print(f"📝 描述: {self.test_cases[test_name]['description']}")
        print(f"📊 段落数量: {len(synthesis_plan)}")
        print()
        
        try:
            start_time = datetime.now()
            
            # 执行分析
            result = await self.chapter_analyzer.analyze_chapter_environment(synthesis_plan)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"✅ 章节分析完成！耗时: {duration:.2f}秒")
            print()
            
            # 显示结果
            if isinstance(result, dict):
                print(f"📊 分析统计:")
                print(f"   总时长: {result.get('total_duration', 0)}秒")
                print(f"   环境音轨道: {len(result.get('environment_tracks', []))}个")
                print(f"   分析状态: {result.get('analysis_status', 'N/A')}")
                print()
                
                tracks = result.get('environment_tracks', [])
                if tracks:
                    print(f"🎵 环境音轨道详情:")
                    for i, track in enumerate(tracks, 1):
                        print(f"   轨道 {i}: {track.get('scene_description', 'N/A')}")
                        print(f"     关键词: {', '.join(track.get('environment_keywords', []))}")
                        print(f"     时长: {track.get('duration', 0)}秒")
                        print()
            
            return result
            
        except Exception as e:
            print(f"❌ 章节分析失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 环境音分析测试套件")
        print("=" * 60)
        print()
        
        results = {}
        
        for test_name in self.test_cases:
            synthesis_plan = self.test_cases[test_name]['synthesis_plan']
            
            print(f"🔍 测试用例: {test_name}")
            print("-" * 40)
            
            # 测试旁白分析器
            narration_result = await self.test_narration_analyzer(test_name, synthesis_plan)
            results[f"{test_name}_narration"] = narration_result
            
            print()
            
            # 测试章节分析器
            chapter_result = await self.test_chapter_analyzer(test_name, synthesis_plan)
            results[f"{test_name}_chapter"] = chapter_result
            
            print("=" * 60)
            print()
        
        # 保存测试结果
        self.save_test_results(results)
        
        return results
    
    def save_test_results(self, results: Dict[str, Any]):
        """保存测试结果到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"environment_analysis_test_results_{timestamp}.json"
        
        # 转换结果格式，确保可序列化
        serializable_results = {}
        for key, value in results.items():
            if isinstance(value, dict):
                serializable_results[key] = value
            else:
                serializable_results[key] = str(value)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        
        print(f"💾 测试结果已保存到: {filename}")

async def main():
    """主函数"""
    test_suite = EnvironmentAnalysisTestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
