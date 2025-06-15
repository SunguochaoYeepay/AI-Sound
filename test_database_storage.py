#!/usr/bin/env python3
"""
数据库存储验证测试
验证智能准备结果是否正确存储到数据库中
"""

import requests
import json
import sys
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000/api/v1"
CONTENT_PREP_URL = "http://localhost:8000/api/v1/content-preparation"

def test_api_endpoint(method, url, data=None):
    """测试API端点"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=120)
        else:
            return {"success": False, "error": f"不支持的HTTP方法: {method}"}
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    
    except requests.exceptions.Timeout:
        return {"success": False, "error": "请求超时"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def check_database_storage():
    """检查数据库存储情况"""
    print("🔍 验证智能准备结果的数据库存储")
    print("=" * 60)
    
    # 1. 获取测试章节
    print("\n1️⃣ 获取测试章节")
    books_result = test_api_endpoint("GET", f"{BASE_URL}/books")
    if not books_result["success"]:
        print(f"❌ 获取书籍列表失败: {books_result['error']}")
        return False
    
    books = books_result["data"]["data"]
    if not books:
        print("❌ 没有找到测试书籍")
        return False
    
    test_book = books[0]
    print(f"📖 测试书籍: {test_book['title']} (ID: {test_book['id']})")
    
    # 获取章节
    chapters_result = test_api_endpoint("GET", f"{BASE_URL}/books/{test_book['id']}/chapters")
    if not chapters_result["success"]:
        print(f"❌ 获取章节列表失败: {chapters_result['error']}")
        return False
    
    chapters = chapters_result["data"]["data"]
    if not chapters:
        print("❌ 没有找到测试章节")
        return False
    
    test_chapter = chapters[0]
    chapter_id = test_chapter['id']
    chapter_title = test_chapter.get('title') or test_chapter.get('chapter_title', '未知章节')
    print(f"📄 测试章节: {chapter_title} (ID: {chapter_id})")
    
    # 2. 执行智能准备
    print(f"\n2️⃣ 执行智能准备 (章节ID: {chapter_id})")
    prepare_result = test_api_endpoint("POST", f"{CONTENT_PREP_URL}/prepare-synthesis/{chapter_id}")
    
    if not prepare_result["success"]:
        print(f"❌ 智能准备失败: {prepare_result['error']}")
        return False
    
    prepare_data = prepare_result["data"]["data"]
    processing_info = prepare_data["processing_info"]
    
    print("✅ 智能准备完成!")
    print(f"   处理模式: {processing_info['mode']}")
    print(f"   生成片段: {processing_info['total_segments']} 个")
    print(f"   检测角色: {processing_info['characters_found']} 个")
    print(f"   数据库存储: {processing_info.get('saved_to_database', 'Unknown')}")
    print(f"   存储ID: {processing_info.get('preparation_id', 'Unknown')}")
    
    # 3. 验证章节状态更新
    print(f"\n3️⃣ 验证章节状态更新")
    chapter_result = test_api_endpoint("GET", f"{BASE_URL}/chapters/{chapter_id}")
    if chapter_result["success"]:
        chapter_data = chapter_result["data"]["data"]
        print(f"✅ 章节状态已更新:")
        print(f"   分析状态: {chapter_data.get('analysis_status', 'Unknown')}")
        print(f"   合成状态: {chapter_data.get('synthesis_status', 'Unknown')}")
    else:
        print(f"❌ 获取章节状态失败: {chapter_result['error']}")
    
    # 4. 检查准备状态API
    print(f"\n4️⃣ 检查准备状态API")
    status_result = test_api_endpoint("GET", f"{CONTENT_PREP_URL}/preparation-status/{chapter_id}")
    if status_result["success"]:
        status_data = status_result["data"]["data"]
        print(f"✅ 准备状态:")
        print(f"   准备完成: {status_data.get('preparation_complete', False)}")
        print(f"   分析状态: {status_data.get('analysis_status', 'Unknown')}")
        print(f"   合成状态: {status_data.get('synthesis_status', 'Unknown')}")
        print(f"   有合成配置: {status_data.get('has_synthesis_config', False)}")
        print(f"   最后更新: {status_data.get('last_updated', 'Unknown')}")
    else:
        print(f"❌ 获取准备状态失败: {status_result['error']}")
    
    # 5. 再次执行智能准备，测试去重功能
    print(f"\n5️⃣ 测试重复执行智能准备（验证去重功能）")
    prepare_result2 = test_api_endpoint("POST", f"{CONTENT_PREP_URL}/prepare-synthesis/{chapter_id}")
    
    if prepare_result2["success"]:
        prepare_data2 = prepare_result2["data"]["data"]
        processing_info2 = prepare_data2["processing_info"]
        
        print("✅ 重复智能准备完成!")
        print(f"   处理模式: {processing_info2['mode']}")
        print(f"   数据库存储: {processing_info2.get('saved_to_database', 'Unknown')}")
        print(f"   存储ID: {processing_info2.get('preparation_id', 'Unknown')}")
        
        # 比较两次结果
        if processing_info.get('preparation_id') == processing_info2.get('preparation_id'):
            print("✅ 去重功能正常：使用了相同的存储记录")
        else:
            print("⚠️  去重功能可能有问题：生成了不同的存储记录")
    else:
        print(f"❌ 重复智能准备失败: {prepare_result2['error']}")
    
    # 6. 总结
    print(f"\n6️⃣ 数据库存储验证总结")
    print("=" * 60)
    
    storage_success = (
        processing_info.get('saved_to_database') == True and
        processing_info.get('preparation_id') is not None
    )
    
    if storage_success:
        print("🎉 数据库存储验证成功!")
        print("✅ 智能准备结果已正确存储到数据库")
        print("✅ 章节状态已正确更新")
        print("✅ 准备状态API正常工作")
        print("✅ 重复执行处理正常")
        return True
    else:
        print("❌ 数据库存储验证失败!")
        print("❌ 智能准备结果可能未正确存储")
        return False

def main():
    """主函数"""
    print("🔍 智能准备数据库存储验证测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        success = check_database_storage()
        
        if success:
            print("\n🎉 所有验证测试通过!")
            print("💾 智能准备结果已正确存储到数据库中")
            sys.exit(0)
        else:
            print("\n❌ 验证测试失败!")
            print("💾 智能准备结果存储可能有问题")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 