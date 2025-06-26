#!/usr/bin/env python3
"""
测试角色分析功能 - 包括MCP等多种方式
"""

import sys
import os
import asyncio
import json
import logging
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.abspath('.'))

try:
    from app.database import SessionLocal
    from app.models import BookChapter
    from app.detectors import OllamaCharacterDetector, AdvancedCharacterDetector, ProgrammaticCharacterDetector
    print("✅ 导入成功")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_character_analysis():
    """测试角色分析功能"""
    db = SessionLocal()
    
    try:
        print("🔍 查找测试章节...")
        
        # 获取书籍ID为11的第一章进行测试
        chapter = db.query(BookChapter).filter(
            BookChapter.book_id == 11,
            BookChapter.chapter_number == 1
        ).first()
        
        if not chapter:
            print("❌ 未找到测试章节")
            return
            
        print(f"✅ 找到测试章节: {chapter.chapter_title}")
        print(f"📄 内容长度: {len(chapter.content)} 字符")
        
        # 取一小段内容进行测试
        test_content = chapter.content[:500] if chapter.content else "孙悟空说道：\"师父，我们走吧。\"唐僧点了点头。"
        print(f"🧪 测试内容: {test_content[:100]}...")
        
        chapter_info = {
            'chapter_id': chapter.id,
            'chapter_title': chapter.chapter_title,
            'chapter_number': chapter.chapter_number
        }
        
        # 测试1: Ollama检测器
        print("\n🤖 测试1: Ollama AI检测器")
        try:
            ollama_detector = OllamaCharacterDetector()
            print(f"   模型: {ollama_detector.model_name}")
            print(f"   URL: {ollama_detector.ollama_url}")
            
            result = await ollama_detector.analyze_text(test_content, chapter_info)
            
            print(f"   ✅ Ollama分析成功")
            print(f"   📊 识别角色数: {len(result.get('detected_characters', []))}")
            print(f"   📝 分段数: {len(result.get('segments', []))}")
            print(f"   🔍 分析方法: {result.get('processing_stats', {}).get('analysis_method', 'unknown')}")
            
            # 显示识别的角色
            characters = result.get('detected_characters', [])
            if characters:
                print("   🎭 识别的角色:")
                for char in characters[:5]:  # 只显示前5个
                    name = char.get('name', '未知')
                    freq = char.get('frequency', 0)
                    gender = char.get('recommended_config', {}).get('gender', 'unknown')
                    print(f"      - {name} (频次: {freq}, 性别: {gender})")
            
        except Exception as e:
            print(f"   ❌ Ollama检测器失败: {str(e)}")
        
        # 测试2: 高级检测器
        print("\n🧠 测试2: 高级规则检测器")
        try:
            advanced_detector = AdvancedCharacterDetector()
            result = advanced_detector.analyze_text(test_content, chapter_info)
            
            print(f"   ✅ 高级检测器分析成功")
            print(f"   📊 识别角色数: {len(result.get('detected_characters', []))}")
            print(f"   📝 分段数: {len(result.get('segments', []))}")
            
            # 显示识别的角色
            characters = result.get('detected_characters', [])
            if characters:
                print("   🎭 识别的角色:")
                for char in characters[:3]:
                    name = char.get('name', '未知')
                    freq = char.get('frequency', 0)
                    print(f"      - {name} (频次: {freq})")
                    
        except Exception as e:
            print(f"   ❌ 高级检测器失败: {str(e)}")
        
        # 测试3: 基础检测器
        print("\n📝 测试3: 基础程序化检测器")
        try:
            basic_detector = ProgrammaticCharacterDetector()
            result = basic_detector.analyze_text(test_content, chapter_info)
            
            print(f"   ✅ 基础检测器分析成功")
            print(f"   📊 识别角色数: {len(result.get('detected_characters', []))}")
            
        except Exception as e:
            print(f"   ❌ 基础检测器失败: {str(e)}")
        
        # 测试4: 检查网络连接
        print("\n🌐 测试4: 检查Ollama服务连接")
        try:
            import requests
            response = requests.get("http://localhost:11434/api/version", timeout=5)
            if response.status_code == 200:
                print("   ✅ Ollama服务正常运行")
                version_info = response.json()
                print(f"   📋 版本信息: {version_info}")
            else:
                print(f"   ⚠️ Ollama服务响应异常: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("   ❌ 无法连接到Ollama服务 (http://localhost:11434)")
            print("   💡 建议: 请启动Ollama服务")
        except Exception as e:
            print(f"   ❌ 网络测试失败: {str(e)}")
        
        # 测试5: 检查MCP可用性
        print("\n🔌 测试5: 检查MCP可用性")
        try:
            # 这里可以添加MCP相关的测试
            print("   ℹ️ MCP测试功能待实现")
        except Exception as e:
            print(f"   ❌ MCP测试失败: {str(e)}")
            
    except Exception as e:
        print(f"❌ 测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def test_simple_analysis():
    """测试简单分析功能"""
    print("\n🔧 测试简单文本分析")
    
    test_text = """
    孙悟空说道："师父，前面有妖精！"
    唐僧惊道："悟空，你可看清楚了？"
    猪八戒在旁边说："大师兄，我们快逃吧！"
    孙悟空冷笑一声："呆子，我们是去除妖的！"
    """
    
    # 简单的角色提取
    import re
    
    # 提取说话的角色
    speakers = re.findall(r'(\w+)(?:说道|惊道|冷笑|说)：', test_text)
    characters = list(set(speakers))
    
    print(f"   📝 测试文本: {test_text.strip()}")
    print(f"   🎭 提取的角色: {characters}")
    
    # 简单分段
    sentences = [s.strip() for s in re.split(r'[。！？]', test_text) if s.strip()]
    print(f"   📄 分段数: {len(sentences)}")
    
    for i, sentence in enumerate(sentences[:3]):
        print(f"      {i+1}. {sentence}")

if __name__ == "__main__":
    print("🚀 开始角色分析测试...")
    
    # 先测试简单分析
    test_simple_analysis()
    
    # 再测试完整分析
    asyncio.run(test_character_analysis())
    
    print("\n✨ 测试完成！") 