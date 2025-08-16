#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境音分析测试脚本
用于测试环境音分析功能的各种场景
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.narration_environment_analyzer import NarrationEnvironmentAnalyzer
from app.services.chapter_environment_analyzer import ChapterEnvironmentAnalyzer


class EnvironmentAnalysisTester:
    """环境音分析测试器"""
    
    def __init__(self):
        self.narration_analyzer = NarrationEnvironmentAnalyzer()
        self.chapter_analyzer = ChapterEnvironmentAnalyzer()
        
        # 测试数据
        self.test_cases = {
            "雨夜古宅": {
                "description": "悬疑小说场景 - 雨夜古宅",
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
                    },
                    {
                        "segment_id": 3,
                        "text": "突然，楼上传来脚步声。林雨紧张地握紧手电筒，'谁在那里？'",
                        "speaker": "旁白",
                        "emotion": "nervous"
                    },
                    {
                        "segment_id": 4,
                        "text": "是一位白发苍苍的老人，慢慢走下楼梯。每一步都让木板嘎吱作响。",
                        "speaker": "旁白",
                        "emotion": "contemplative"
                    },
                    {
                        "segment_id": 5,
                        "text": "窗外雨声渐急，偶尔夹杂着猫头鹰的叫声，为这个诡异的夜晚增添了更多的悬疑气氛。",
                        "speaker": "旁白",
                        "emotion": "mysterious"
                    }
                ]
            },
            "森林追逐": {
                "description": "动作场景 - 森林追逐",
                "synthesis_plan": [
                    {
                        "segment_id": 1,
                        "text": "清晨的阳光透过茂密的森林洒下斑驳的光影。鸟儿在枝头欢快地歌唱，溪水潺潺流淌。",
                        "speaker": "旁白",
                        "emotion": "peaceful"
                    },
                    {
                        "segment_id": 2,
                        "text": "陈剑骑着马在林间小径上疾驰，马蹄声在森林中回响。'驾！'他催促着胯下的战马。",
                        "speaker": "旁白",
                        "emotion": "excited"
                    },
                    {
                        "segment_id": 3,
                        "text": "身后传来野狼的嚎叫声，越来越近。风声呼啸，树叶簌簌作响。",
                        "speaker": "旁白",
                        "emotion": "tense"
                    },
                    {
                        "segment_id": 4,
                        "text": "他拉紧缰绳，战马嘶鸣一声，跃过一道小溪。水花四溅，激起阵阵涟漪。",
                        "speaker": "旁白",
                        "emotion": "action"
                    }
                ]
            },
            "海边重逢": {
                "description": "浪漫场景 - 海边重逢",
                "synthesis_plan": [
                    {
                        "segment_id": 1,
                        "text": "夕阳西下，海浪轻柔地拍打着沙滩。海鸥在空中盘旋，发出悠长的叫声。",
                        "speaker": "旁白",
                        "emotion": "peaceful"
                    },
                    {
                        "segment_id": 2,
                        "text": "林雨独自走在海边，海风轻抚着她的长发。远处传来渔船的汽笛声。",
                        "speaker": "旁白",
                        "emotion": "contemplative"
                    },
                    {
                        "segment_id": 3,
                        "text": "脚步声从身后传来，林雨回过头，看到了熟悉的身影。",
                        "speaker": "旁白",
                        "emotion": "surprised"
                    },
                    {
                        "segment_id": 4,
                        "text": "海浪声轻柔而有节奏，就像大自然的摇篮曲。两人并肩走在沙滩上，脚印留在湿润的沙子里。",
                        "speaker": "旁白",
                        "emotion": "romantic"
                    }
                ]
            },
            "城市街道": {
                "description": "都市场景 - 城市街道",
                "synthesis_plan": [
                    {
                        "segment_id": 1,
                        "text": "街道上车水马龙，汽车的喇叭声此起彼伏。行人匆匆走过，脚步声在水泥地面上回响。",
                        "speaker": "旁白",
                        "emotion": "busy"
                    },
                    {
                        "segment_id": 2,
                        "text": "地铁从地下呼啸而过，震动传遍整个街区。小贩的吆喝声在街角响起。",
                        "speaker": "旁白",
                        "emotion": "urban"
                    },
                    {
                        "segment_id": 3,
                        "text": "突然，远处传来警笛声，一辆救护车疾驰而过，打破了街区的喧嚣。",
                        "speaker": "旁白",
                        "emotion": "urgent"
                    }
                ]
            }
        }
    
    async def test_narration_analyzer(self, test_name: str, synthesis_plan: List[Dict]) -> Dict[str, Any]:
        """测试旁白环境分析器"""
        print(f"\n🔍 测试旁白环境分析器: {test_name}")
        print("=" * 60)
        
        try:
            start_time = datetime.now()
            
            # 执行分析
            result = await self.narration_analyzer.extract_and_analyze_narration(synthesis_plan)
            
            end_time = datetime.now()
            analysis_duration = (end_time - start_time).total_seconds()
            
            # 构建测试结果
            test_result = {
                "test_name": test_name,
                "analyzer_type": "NarrationEnvironmentAnalyzer",
                "analysis_duration": analysis_duration,
                "input_segments": len(synthesis_plan),
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
            # 输出结果摘要
            self._print_analysis_summary(test_result)
            
            return test_result
            
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            return {
                "test_name": test_name,
                "analyzer_type": "NarrationEnvironmentAnalyzer",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_chapter_analyzer(self, test_name: str, synthesis_plan: List[Dict]) -> Dict[str, Any]:
        """测试章节环境分析器"""
        print(f"\n🔍 测试章节环境分析器: {test_name}")
        print("=" * 60)
        
        try:
            start_time = datetime.now()
            
            # 模拟章节内容
            chapter_content = "\n".join([seg["text"] for seg in synthesis_plan])
            
            # 执行分析
            result = await self.chapter_analyzer.analyze_chapter_environment(
                chapter_content=chapter_content,
                synthesis_plan=synthesis_plan,
                options={"test_mode": True}
            )
            
            end_time = datetime.now()
            analysis_duration = (end_time - start_time).total_seconds()
            
            # 构建测试结果
            test_result = {
                "test_name": test_name,
                "analyzer_type": "ChapterEnvironmentAnalyzer",
                "analysis_duration": analysis_duration,
                "input_segments": len(synthesis_plan),
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
            # 输出结果摘要
            self._print_analysis_summary(test_result)
            
            return test_result
            
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            return {
                "test_name": test_name,
                "analyzer_type": "ChapterEnvironmentAnalyzer",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _print_analysis_summary(self, test_result: Dict[str, Any]):
        """打印分析结果摘要"""
        if "error" in test_result:
            print(f"❌ 错误: {test_result['error']}")
            return
        
        result = test_result["result"]
        duration = test_result["analysis_duration"]
        
        print(f"⏱️  分析耗时: {duration:.2f}秒")
        
        if "environment_tracks" in result:
            tracks = result["environment_tracks"]
            print(f"🎵 识别环境音轨道: {len(tracks)}个")
            
            for i, track in enumerate(tracks, 1):
                print(f"  {i}. {track.get('scene_description', '未知场景')}")
                print(f"     关键词: {', '.join(track.get('environment_keywords', []))}")
                print(f"     时长: {track.get('duration', 0):.1f}s")
                print(f"     强度: {track.get('intensity', 'unknown')}")
                print(f"     类型: {track.get('continuity_type', 'unknown')}")
        
        if "analysis_summary" in result:
            summary = result["analysis_summary"]
            print(f"📊 分析统计:")
            print(f"   总时长: {summary.get('total_duration', 0):.1f}秒")
            print(f"   旁白段落: {summary.get('narration_segments', 0)}个")
            print(f"   环境轨道: {summary.get('environment_tracks_detected', 0)}个")
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("🚀 开始环境音分析测试")
        print("=" * 80)
        
        all_results = {
            "test_session": datetime.now().isoformat(),
            "total_tests": 0,
            "successful_tests": 0,
            "failed_tests": 0,
            "results": []
        }
        
        for test_name, test_data in self.test_cases.items():
            print(f"\n📝 测试场景: {test_name}")
            print(f"📖 描述: {test_data['description']}")
            
            synthesis_plan = test_data["synthesis_plan"]
            
            # 测试旁白分析器
            narration_result = await self.test_narration_analyzer(test_name, synthesis_plan)
            all_results["results"].append(narration_result)
            all_results["total_tests"] += 1
            
            if "error" not in narration_result:
                all_results["successful_tests"] += 1
            else:
                all_results["failed_tests"] += 1
            
            # 测试章节分析器
            chapter_result = await self.test_chapter_analyzer(test_name, synthesis_plan)
            all_results["results"].append(chapter_result)
            all_results["total_tests"] += 1
            
            if "error" not in chapter_result:
                all_results["successful_tests"] += 1
            else:
                all_results["failed_tests"] += 1
        
        # 输出测试总结
        self._print_test_summary(all_results)
        
        return all_results
    
    def _print_test_summary(self, all_results: Dict[str, Any]):
        """打印测试总结"""
        print("\n" + "=" * 80)
        print("📊 测试总结")
        print("=" * 80)
        print(f"总测试数: {all_results['total_tests']}")
        print(f"成功: {all_results['successful_tests']}")
        print(f"失败: {all_results['failed_tests']}")
        print(f"成功率: {all_results['successful_tests']/all_results['total_tests']*100:.1f}%")
        
        # 计算平均分析时间
        successful_results = [r for r in all_results["results"] if "error" not in r]
        if successful_results:
            avg_duration = sum(r["analysis_duration"] for r in successful_results) / len(successful_results)
            print(f"平均分析时间: {avg_duration:.2f}秒")
    
    def save_results(self, results: Dict[str, Any], filename: str = None):
        """保存测试结果到文件"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"environment_analysis_test_results_{timestamp}.json"
        
        filepath = os.path.join(os.path.dirname(__file__), "test_results", filename)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 测试结果已保存到: {filepath}")
        return filepath


async def main():
    """主函数"""
    tester = EnvironmentAnalysisTester()
    
    # 运行所有测试
    results = await tester.run_all_tests()
    
    # 保存结果
    tester.save_results(results)
    
    print("\n✅ 测试完成！")


if __name__ == "__main__":
    asyncio.run(main())
