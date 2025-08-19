#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
import os
import json
import re

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'platform', 'backend'))

from app.services.narration_environment_analyzer import NarrationEnvironmentAnalyzer

async def debug_llm_parsing():
    print("=== 调试LLM解析过程 ===")
    
    analyzer = NarrationEnvironmentAnalyzer()
    
    # 模拟段落内容
    test_content = "打雷了！！都打的雨点打到了地上，形成一条滚滚大河。"
    
    print(f"测试内容: {test_content}")
    
    # 1. 测试LLM直接调用
    print("\n1. 测试LLM直接调用...")
    prompt = f"""
请分析以下旁白中的环境音效关键词：

旁白内容：{test_content}

请从中提取环境音效关键词，返回JSON格式：
{{
    "keywords": ["关键词1", "关键词2"]
}}

注意：只返回纯JSON，不要其他文字。
"""
    
    print(f"提示词: {prompt}")
    
    try:
        # 直接调用LLM
        llm_response = await analyzer._call_llm_directly(prompt)
        print(f"\nLLM原始响应: {llm_response}")
        print(f"响应类型: {type(llm_response)}")
        
        if hasattr(llm_response, 'raw_response'):
            raw_text = llm_response.raw_response
            print(f"\n原始文本: {raw_text}")
            
            # 2. 测试JSON提取
            print("\n2. 测试JSON提取...")
            
            # 尝试提取JSON
            json_match = re.search(r'\{[^}]*"keywords"[^}]*\}', raw_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                print(f"提取的JSON字符串: {json_str}")
                
                try:
                    parsed_json = json.loads(json_str)
                    print(f"解析成功: {parsed_json}")
                    keywords = parsed_json.get('keywords', [])
                    print(f"提取的关键词: {keywords}")
                except json.JSONDecodeError as e:
                    print(f"JSON解析失败: {e}")
            else:
                print("未找到JSON格式")
                
            # 3. 测试markdown代码块提取
            print("\n3. 测试markdown代码块提取...")
            markdown_match = re.search(r'```json\s*(\{[^}]*"keywords"[^}]*\})\s*```', raw_text, re.DOTALL)
            if markdown_match:
                json_str = markdown_match.group(1)
                print(f"从markdown提取的JSON: {json_str}")
                
                try:
                    parsed_json = json.loads(json_str)
                    print(f"解析成功: {parsed_json}")
                    keywords = parsed_json.get('keywords', [])
                    print(f"提取的关键词: {keywords}")
                except json.JSONDecodeError as e:
                    print(f"JSON解析失败: {e}")
            else:
                print("未找到markdown代码块")
                
            # 4. 测试关键词直接提取
            print("\n4. 测试关键词直接提取...")
            # 查找可能的关键词
            keywords_pattern = r'"keywords":\s*\[(.*?)\]'
            keywords_match = re.search(keywords_pattern, raw_text, re.DOTALL)
            if keywords_match:
                keywords_str = keywords_match.group(1)
                print(f"关键词字符串: {keywords_str}")
                
                # 提取引号内的内容
                keyword_items = re.findall(r'"([^"]+)"', keywords_str)
                print(f"提取的关键词列表: {keyword_items}")
            else:
                print("未找到关键词模式")
        
        # 5. 测试完整的解析方法
        print("\n5. 测试完整的解析方法...")
        synthesis_plan = [
            {"segment_id": 6, "content": test_content, "character": "旁白"}
        ]
        
        result = await analyzer.extract_and_analyze_narration(synthesis_plan)
        print(f"完整分析结果: {result}")
        
    except Exception as e:
        print(f"调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_llm_parsing())
