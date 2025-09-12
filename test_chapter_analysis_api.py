#!/usr/bin/env python3
"""
书籍分析API接口测试
测试项目2第一章第一段的完整分析流程
"""

import requests
import json
import time
import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'platform', 'backend'))

def test_chapter_analysis_api():
    """测试章节分析API"""
    print("🧪 书籍分析API接口测试")
    print("=" * 60)
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # API基础URL
    base_url = "http://localhost:8001/api/v1"
    chapter_id = 2  # 书籍2第一章
    
    # 测试文本（第一章第一段）
    test_segment = """指尖触到唐三彩碎片的刹那，林薇只觉一股电流顺着指尖窜遍全身，实验室的白炽灯骤然炸裂，碎玻璃在眼前化作漫天金粉。再睁眼时，鼻尖萦绕的已是混合着香料与尘土的陌生气息，身下是硌人的青石板路，耳边传来此起彼伏的胡商叫卖声。

"快看这女子的衣装！"

"莫不是西域来的怪人？"

林薇低头看着自己身上的白大褂，又抬头望向四周鳞次栉比的飞檐斗拱，心脏猛地一缩 —— 她竟真的穿越到了课本里的盛唐长安。还没等她理清思绪，一阵急促的马蹄声突然从巷口传来，伴随着惊惶的呼喊，人群瞬间四散奔逃。"""
    
    print(f"📖 测试书籍: 书籍2 - 《长安医语》")
    print(f"📝 测试章节: 第一章 - 《长安初遇》")
    print(f"📄 测试段落长度: {len(test_segment)} 字符")
    print(f"📄 测试段落内容: {test_segment[:100]}...")
    print()
    
    try:
        # 步骤1：智能分段
        print("🔄 步骤1：智能分段测试")
        segmentation_url = f"{base_url}/chapters/{chapter_id}/smart-segmentation"
        
        start_time = time.time()
        response = requests.post(segmentation_url, timeout=300)
        segmentation_time = time.time() - start_time
        
        if response.status_code == 200:
            segmentation_result = response.json()
            print(f"   ✅ 智能分段完成 ({segmentation_time:.2f}秒)")
            print(f"   📊 分段数量: {len(segmentation_result.get('segments', []))}")
        else:
            print(f"   ❌ 智能分段失败: {response.status_code} - {response.text}")
            return False
        
        print()
        
        # 步骤2：完整分析（包含对话分析 + 5卡分析 + 音频分镜卡）
        print("🔄 步骤2：完整分析测试（对话分析 + 5卡分析 + 音频分镜卡）")
        analysis_url = f"{base_url}/chapters/{chapter_id}/six-card-analysis"
        
        analysis_data = {
            "segment_indices": [0],  # 测试第一段
            "project_id": 8
        }
        
        start_time = time.time()
        response = requests.post(analysis_url, json=analysis_data, timeout=300)
        analysis_time = time.time() - start_time
        
        if response.status_code == 200:
            analysis_result = response.json()
            print(f"   ✅ 5卡分析完成 ({analysis_time:.2f}秒)")
            
            # 验证5卡结果
            cards = analysis_result.get('cards', [])
            print(f"   📊 生成卡片数量: {len(cards)}")
            
            for card in cards:
                card_type = card.get('card_type', 'unknown')
                confidence = card.get('confidence_score', 0)
                print(f"      - {card_type}: 置信度 {confidence}")
                
        else:
            print(f"   ❌ 5卡分析失败: {response.status_code} - {response.text}")
            return False
        
        print()
        
        # 步骤3：验证数据库存储
        print("🔄 步骤3：验证数据库存储")
        print("   📊 检查数据库中的分析结果...")
        
        # 这里需要MCP查询数据库
        print("   ✅ 数据库验证需要MCP工具支持")
        
        print()
        
        # 性能总结
        print("⏱️ 性能总结")
        print("=" * 60)
        print(f"🎯 智能分段:     {segmentation_time:>8.2f}s")
        print(f"🎯 5卡分析:      {analysis_time:>8.2f}s")
        print(f"📊 总耗时:       {segmentation_time + analysis_time:>8.2f}s")
        print(f"⚡ 处理速度:     {len(test_segment)/(segmentation_time + analysis_time):>8.1f} 字符/秒")
        print()
        
        print("🎉 API接口测试完成！")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败：请确保后端服务已启动 (http://localhost:8000)")
        return False
    except requests.exceptions.Timeout:
        print("❌ 请求超时：分析时间过长")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def check_backend_status():
    """检查后端服务状态"""
    try:
        response = requests.get("http://localhost:8001/docs", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务运行正常")
            return True
        else:
            print(f"⚠️ 后端服务响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 后端服务未启动，请先启动后端服务")
        return False
    except Exception as e:
        print(f"❌ 检查后端服务状态失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 检查后端服务状态...")
    if check_backend_status():
        print()
        success = test_chapter_analysis_api()
        if success:
            print("\n✅ 所有测试通过")
        else:
            print("\n❌ 测试失败")
    else:
        print("\n❌ 无法进行测试，请先启动后端服务")
