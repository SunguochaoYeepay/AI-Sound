#!/usr/bin/env python3
"""
测试修复后的环境音分析功能 - 1-3章完整测试
"""

import sys
import os
import requests
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_fixed_analysis():
    """测试修复后的环境音分析功能"""
    print("🔍 测试修复后的环境音分析功能")
    print("=" * 60)
    
    # API基础URL
    base_url = "http://localhost:8000"
    project_id = 76
    
    # 章节ID列表
    chapters = [
        {"id": 836, "name": "第一章：穿越"},
        {"id": 837, "name": "第二章：奇遇"},
        {"id": 838, "name": "第三章：机缘巧合"}
    ]
    
    total_results = {}
    
    for chapter in chapters:
        print(f"\n🎯 测试 {chapter['name']} (ID: {chapter['id']})")
        print("-" * 40)
        
        try:
            # 测试环境音分析API
            url = f"{base_url}/api/v1/environment-generation/chapters/analyze"
            
            # 构建测试请求
            test_request = {
                "chapter_ids": [chapter['id']],
                "analysis_options": {
                    "mode": "auto",
                    "environment_types": ["nature", "urban", "indoor", "action"],
                    "precision": "medium",
                    "existing_project_id": project_id,
                    "force_reanalyze": True  # 强制重新分析
                }
            }
            
            print(f"   请求URL: {url}")
            print(f"   章节ID: {chapter['id']}")
            
            response = requests.post(url, json=test_request, timeout=180)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and data.get('analysis_result'):
                    analysis_result = data['analysis_result']
                    tracks = analysis_result.get('environment_tracks', [])
                    
                    print(f"   ✅ 分析成功")
                    print(f"   📊 识别轨道数: {len(tracks)}")
                    
                    # 详细分析每个轨道
                    chapter_results = {
                        "chapter_name": chapter['name'],
                        "chapter_id": chapter['id'],
                        "tracks_count": len(tracks),
                        "tracks": []
                    }
                    
                    for i, track in enumerate(tracks, 1):
                        keywords = track.get('environment_keywords', [])
                        duration = track.get('duration', 0)
                        start_time = track.get('start_time', 0)
                        confidence = track.get('confidence', 0)
                        narration_text = track.get('narration_text', '')[:100] + '...'
                        
                        print(f"\n      轨道 {i}:")
                        print(f"        - 关键词: {keywords}")
                        print(f"        - 时长: {duration:.1f}秒")
                        print(f"        - 开始时间: {start_time:.1f}秒")
                        print(f"        - 置信度: {confidence:.2f}")
                        print(f"        - 旁白文本: {narration_text}")
                        
                        # 分析准确性
                        accuracy_score = analyze_track_accuracy(keywords, narration_text, duration)
                        print(f"        - 准确性评分: {accuracy_score}/10")
                        
                        # 提供改进建议
                        suggestions = get_accuracy_suggestions(keywords, narration_text, duration)
                        if suggestions:
                            print(f"        - 改进建议: {suggestions}")
                        
                        # 记录轨道信息
                        track_info = {
                            "track_id": i,
                            "keywords": keywords,
                            "duration": duration,
                            "start_time": start_time,
                            "confidence": confidence,
                            "accuracy_score": accuracy_score,
                            "suggestions": suggestions
                        }
                        chapter_results["tracks"].append(track_info)
                    
                    # 总体评价
                    if tracks:
                        avg_confidence = sum(track.get('confidence', 0) for track in tracks) / len(tracks)
                        avg_accuracy = sum(chapter_results["tracks"][i]["accuracy_score"] for i in range(len(tracks))) / len(tracks)
                        
                        print(f"\n     🏆 {chapter['name']}总体评价:")
                        print(f"       - 平均置信度: {avg_confidence:.2f}")
                        print(f"       - 平均准确性评分: {avg_accuracy:.1f}/10")
                        
                        # 置信度评价
                        if avg_confidence >= 0.8:
                            confidence_rating = "✅ 优秀"
                        elif avg_confidence >= 0.6:
                            confidence_rating = "⚠️ 良好"
                        else:
                            confidence_rating = "❌ 需要改进"
                        print(f"       - 置信度评价: {confidence_rating}")
                        
                        # 准确性评价
                        if avg_accuracy >= 8:
                            accuracy_rating = "✅ 优秀"
                        elif avg_accuracy >= 6:
                            accuracy_rating = "⚠️ 良好"
                        else:
                            accuracy_rating = "❌ 需要改进"
                        print(f"       - 准确性评价: {accuracy_rating}")
                        
                        # 时长合理性分析
                        duration_issues = []
                        for track in tracks:
                            keywords = track.get('environment_keywords', [])
                            duration = track.get('duration', 0)
                            
                            # 检查瞬间声音的时长
                            if any('叮' in kw or '砰' in kw or '响' in kw for kw in keywords):
                                if duration > 3.0:
                                    duration_issues.append(f"瞬间声音'{keywords}'时长过长({duration:.1f}秒)")
                        
                        if duration_issues:
                            print(f"       - 时长问题: {'; '.join(duration_issues)}")
                        else:
                            print(f"       - 时长分配: ✅ 合理")
                        
                        # 关键词质量分析
                        keyword_quality = analyze_keyword_quality(tracks)
                        print(f"       - 关键词质量: {keyword_quality}")
                        
                        # 记录总体评价
                        chapter_results["avg_confidence"] = avg_confidence
                        chapter_results["avg_accuracy"] = avg_accuracy
                        chapter_results["confidence_rating"] = confidence_rating
                        chapter_results["accuracy_rating"] = accuracy_rating
                        chapter_results["keyword_quality"] = keyword_quality
                        chapter_results["duration_issues"] = duration_issues
                    else:
                        print(f"\n     ⚠️ {chapter['name']}没有识别到环境音轨道")
                        chapter_results["avg_confidence"] = 0
                        chapter_results["avg_accuracy"] = 0
                        chapter_results["confidence_rating"] = "无数据"
                        chapter_results["accuracy_rating"] = "无数据"
                        chapter_results["keyword_quality"] = "无数据"
                        chapter_results["duration_issues"] = []
                else:
                    print(f"   ❌ 分析失败: {data.get('message', '未知错误')}")
                    chapter_results = {
                        "chapter_name": chapter['name'],
                        "chapter_id": chapter['id'],
                        "error": data.get('message', '未知错误')
                    }
            else:
                print(f"   ❌ API调用失败: {response.status_code}")
                print(f"   错误响应: {response.text}")
                chapter_results = {
                    "chapter_name": chapter['name'],
                    "chapter_id": chapter['id'],
                    "error": f"HTTP {response.status_code}"
                }
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ 无法连接到后端服务")
            chapter_results = {
                "chapter_name": chapter['name'],
                "chapter_id": chapter['id'],
                "error": "连接失败"
            }
        except Exception as e:
            print(f"   ❌ 测试过程中出现错误: {e}")
            chapter_results = {
                "chapter_name": chapter['name'],
                "chapter_id": chapter['id'],
                "error": str(e)
            }
        
        total_results[chapter['name']] = chapter_results
    
    # 总体总结
    print(f"\n" + "=" * 60)
    print(f"🏆 修复后环境音分析测试总结")
    print(f"=" * 60)
    
    successful_chapters = 0
    total_accuracy = 0
    total_confidence = 0
    
    for chapter_name, results in total_results.items():
        if "error" not in results:
            successful_chapters += 1
            total_accuracy += results.get("avg_accuracy", 0)
            total_confidence += results.get("avg_confidence", 0)
            
            print(f"\n📊 {chapter_name}:")
            print(f"   - 轨道数: {results.get('tracks_count', 0)}")
            print(f"   - 平均准确性: {results.get('avg_accuracy', 0):.1f}/10")
            print(f"   - 平均置信度: {results.get('avg_confidence', 0):.2f}")
            print(f"   - 关键词质量: {results.get('keyword_quality', 'N/A')}")
        else:
            print(f"\n❌ {chapter_name}: {results.get('error', '未知错误')}")
    
    if successful_chapters > 0:
        overall_accuracy = total_accuracy / successful_chapters
        overall_confidence = total_confidence / successful_chapters
        
        print(f"\n🎯 总体评价:")
        print(f"   - 成功分析章节数: {successful_chapters}/3")
        print(f"   - 总体平均准确性: {overall_accuracy:.1f}/10")
        print(f"   - 总体平均置信度: {overall_confidence:.2f}")
        
        # 修复效果评价
        if overall_accuracy >= 7:
            print(f"   - 修复效果: ✅ 优秀")
        elif overall_accuracy >= 5:
            print(f"   - 修复效果: ⚠️ 良好")
        else:
            print(f"   - 修复效果: ❌ 需要进一步改进")
    else:
        print(f"\n❌ 所有章节分析都失败了")
    
    print(f"\n✅ 测试完成")
    return total_results

def analyze_track_accuracy(keywords, narration_text, duration):
    """分析单个轨道的准确性"""
    score = 5  # 基础分
    
    # 检查关键词是否在文本中出现
    if keywords:
        for keyword in keywords:
            if keyword in narration_text:
                score += 2
            else:
                score -= 1
    
    # 检查时长合理性
    if any('叮' in kw or '砰' in kw or '响' in kw for kw in keywords):
        if duration <= 3.0:
            score += 2
        else:
            score -= 1
    
    # 检查置信度
    if duration > 0:
        score += 1
    
    return max(0, min(10, score))

def get_accuracy_suggestions(keywords, narration_text, duration):
    """获取准确性改进建议"""
    suggestions = []
    
    # 检查关键词是否在文本中
    if keywords:
        for keyword in keywords:
            if keyword not in narration_text:
                suggestions.append(f"关键词'{keyword}'在文本中未找到")
    
    # 检查瞬间声音时长
    if any('叮' in kw or '砰' in kw or '响' in kw for kw in keywords):
        if duration > 3.0:
            suggestions.append(f"瞬间声音时长过长({duration:.1f}秒)")
    
    return '; '.join(suggestions) if suggestions else None

def analyze_keyword_quality(environment_tracks):
    """分析关键词质量"""
    all_keywords = []
    for track in environment_tracks:
        all_keywords.extend(track.get('environment_keywords', []))
    
    if not all_keywords:
        return "❌ 无关键词"
    
    # 检查关键词多样性
    unique_keywords = set(all_keywords)
    diversity_ratio = len(unique_keywords) / len(all_keywords)
    
    # 检查关键词长度
    avg_length = sum(len(kw) for kw in all_keywords) / len(all_keywords)
    
    if diversity_ratio >= 0.8 and avg_length >= 2:
        return "✅ 优秀"
    elif diversity_ratio >= 0.6 and avg_length >= 1.5:
        return "⚠️ 良好"
    else:
        return "❌ 需要改进"

if __name__ == "__main__":
    test_fixed_analysis()
