#!/usr/bin/env python3
"""
查询智能准备结果示例
展示如何从数据库中获取和使用智能准备的结果
"""

import requests
import json
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000/api/v1"
CONTENT_PREP_URL = "http://localhost:8000/api/v1/content-preparation"

def get_preparation_results(chapter_id):
    """获取章节的智能准备结果"""
    
    print(f"🔍 查询章节 {chapter_id} 的智能准备结果")
    print("=" * 50)
    
    # 1. 检查准备状态
    print("1️⃣ 检查准备状态")
    try:
        response = requests.get(f"{CONTENT_PREP_URL}/preparation-status/{chapter_id}")
        if response.status_code == 200:
            status_data = response.json()["data"]
            print(f"✅ 准备状态: {'已完成' if status_data['preparation_complete'] else '未完成'}")
            print(f"   分析状态: {status_data['analysis_status']}")
            print(f"   合成状态: {status_data['synthesis_status']}")
            print(f"   最后更新: {status_data['last_updated']}")
            
            if not status_data['preparation_complete']:
                print("⚠️  章节尚未完成智能准备，请先执行智能准备")
                return None
        else:
            print(f"❌ 获取状态失败: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
        return None
    
    # 2. 获取内容统计
    print("\n2️⃣ 获取内容统计")
    try:
        response = requests.get(f"{CONTENT_PREP_URL}/content-stats/{chapter_id}")
        if response.status_code == 200:
            stats_data = response.json()["data"]
            print(f"✅ 内容统计:")
            print(f"   字数: {stats_data['word_count']}")
            print(f"   分块数: {stats_data['chunk_count']}")
            print(f"   推荐模式: {stats_data['processing_recommendation']}")
            print(f"   预估时间: {stats_data['estimated_processing_time']} 秒")
    except Exception as e:
        print(f"⚠️  获取内容统计失败: {str(e)}")
    
    # 3. 获取合成预览
    print("\n3️⃣ 获取合成预览")
    try:
        response = requests.get(f"{CONTENT_PREP_URL}/synthesis-preview/{chapter_id}")
        if response.status_code == 200:
            preview_data = response.json()["data"]
            print(f"✅ 合成预览:")
            print(f"   预估角色: {preview_data['estimated_characters']} 个")
            print(f"   对话数量: {preview_data['dialogue_count']}")
            print(f"   处理复杂度: {preview_data['processing_complexity']}")
    except Exception as e:
        print(f"⚠️  获取合成预览失败: {str(e)}")
    
    # 4. 获取完整的智能准备结果
    print("\n4️⃣ 获取完整智能准备结果")
    try:
        response = requests.post(f"{CONTENT_PREP_URL}/prepare-synthesis/{chapter_id}")
        if response.status_code == 200:
            result_data = response.json()["data"]
            synthesis_json = result_data["synthesis_json"]
            processing_info = result_data["processing_info"]
            
            print(f"✅ 智能准备结果:")
            print(f"   处理模式: {processing_info['mode']}")
            print(f"   生成片段: {processing_info['total_segments']} 个")
            print(f"   检测角色: {processing_info['characters_found']} 个")
            print(f"   数据库存储: {processing_info.get('saved_to_database', 'Unknown')}")
            print(f"   存储ID: {processing_info.get('preparation_id', 'Unknown')}")
            
            return {
                "synthesis_json": synthesis_json,
                "processing_info": processing_info
            }
    except Exception as e:
        print(f"❌ 获取智能准备结果失败: {str(e)}")
        return None

def use_preparation_results(results):
    """使用智能准备结果的示例"""
    
    if not results:
        print("❌ 没有可用的准备结果")
        return
    
    print("\n🎯 使用智能准备结果")
    print("=" * 50)
    
    synthesis_json = results["synthesis_json"]
    processing_info = results["processing_info"]
    
    # 1. 分析合成计划
    print("1️⃣ 分析合成计划")
    synthesis_plan = synthesis_json.get("synthesis_plan", [])
    print(f"   总共 {len(synthesis_plan)} 个语音片段:")
    
    for i, segment in enumerate(synthesis_plan[:5]):  # 只显示前5个
        print(f"   片段 {i+1}: {segment.get('speaker', '未知')} - {segment.get('text', '')[:30]}...")
    
    if len(synthesis_plan) > 5:
        print(f"   ... 还有 {len(synthesis_plan) - 5} 个片段")
    
    # 2. 分析角色配置
    print("\n2️⃣ 分析角色配置")
    characters = synthesis_json.get("characters", [])
    print(f"   检测到 {len(characters)} 个角色:")
    
    for char in characters:
        print(f"   - {char.get('name', '未知角色')}: 语音ID {char.get('voice_id', '未分配')}")
    
    # 3. 语音映射
    print("\n3️⃣ 语音映射")
    voice_mapping = processing_info.get("voice_mapping", {})
    print(f"   角色语音映射:")
    for char_name, voice_id in voice_mapping.items():
        print(f"   - {char_name} → 语音 {voice_id}")
    
    # 4. 生成使用示例
    print("\n4️⃣ 使用示例")
    print("   可以将此结果用于:")
    print("   📢 语音合成系统 - 直接使用 synthesis_json")
    print("   🎭 角色管理系统 - 使用 characters 配置")
    print("   📊 进度跟踪系统 - 使用 processing_info")
    print("   💾 数据分析系统 - 查询数据库存储的结果")
    
    # 5. 保存到文件示例
    print("\n5️⃣ 保存结果到文件")
    filename = f"preparation_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"✅ 结果已保存到: {filename}")
    except Exception as e:
        print(f"❌ 保存失败: {str(e)}")

def main():
    """主函数"""
    print("🎯 智能准备结果查询和使用示例")
    print(f"⏰ 查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 获取测试章节ID
    try:
        # 获取书籍列表
        response = requests.get(f"{BASE_URL}/books")
        if response.status_code == 200:
            books = response.json()["data"]
            if books:
                test_book = books[0]
                print(f"📖 使用测试书籍: {test_book['title']} (ID: {test_book['id']})")
                
                # 获取章节列表
                response = requests.get(f"{BASE_URL}/books/{test_book['id']}/chapters")
                if response.status_code == 200:
                    chapters = response.json()["data"]
                    if chapters:
                        test_chapter = chapters[0]
                        chapter_id = test_chapter['id']
                        chapter_title = test_chapter.get('title') or test_chapter.get('chapter_title', '未知章节')
                        print(f"📄 使用测试章节: {chapter_title} (ID: {chapter_id})")
                        
                        # 查询和使用结果
                        results = get_preparation_results(chapter_id)
                        use_preparation_results(results)
                        
                        print("\n🎉 查询和使用示例完成!")
                        print("\n💡 提示:")
                        print("   - 你可以修改 chapter_id 来查询其他章节")
                        print("   - 结果可以直接用于语音合成系统")
                        print("   - 数据已持久化存储，随时可以查询")
                        
                    else:
                        print("❌ 没有找到测试章节")
                else:
                    print(f"❌ 获取章节失败: {response.text}")
            else:
                print("❌ 没有找到测试书籍")
        else:
            print(f"❌ 获取书籍失败: {response.text}")
            
    except Exception as e:
        print(f"💥 查询过程中发生错误: {str(e)}")

if __name__ == "__main__":
    main() 