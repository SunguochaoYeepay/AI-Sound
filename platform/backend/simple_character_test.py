#!/usr/bin/env python3
"""
简单角色分析测试
"""

import re
import json
import requests
from typing import List, Dict

def test_ollama_connection():
    """测试Ollama连接"""
    try:
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama服务正常")
            return True
        else:
            print(f"⚠️ Ollama服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接Ollama: {e}")
        return False

def simple_character_extraction(text: str) -> Dict:
    """简单的角色提取"""
    print("🔍 开始简单角色提取...")
    
    # 西游记角色模式
    character_patterns = [
        r'(孙悟空|悟空|大圣|行者)(?=说|道|问|答|叫|喊|笑|哭)',
        r'(唐僧|三藏|师父)(?=说|道|问|答|叫|喊|笑|哭)',
        r'(猪八戒|八戒|呆子)(?=说|道|问|答|叫|喊|笑|哭)',
        r'(沙僧|沙和尚|沙师弟)(?=说|道|问|答|叫|喊|笑|哭)',
        r'(白骨精|妖精|女妖)(?=说|道|问|答|叫|喊|笑|哭)'
    ]
    
    characters = {}
    
    # 统计角色出现
    for pattern in character_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            name = match
            if name not in characters:
                characters[name] = {'name': name, 'frequency': 0}
            characters[name]['frequency'] += 1
    
    # 添加旁白
    characters['旁白'] = {'name': '旁白', 'frequency': 10}
    
    # 转换为列表格式
    character_list = []
    for char_data in characters.values():
        character_list.append({
            'name': char_data['name'],
            'frequency': char_data['frequency'],
            'recommended_config': {
                'gender': 'male' if char_data['name'] in ['孙悟空', '唐僧', '猪八戒', '沙僧'] else 'female' if '精' in char_data['name'] else 'neutral',
                'personality': 'brave' if char_data['name'] == '孙悟空' else 'gentle',
                'description': f"{char_data['name']}角色"
            }
        })
    
    return {
        'detected_characters': character_list,
        'processing_stats': {
            'characters_found': len(character_list),
            'analysis_method': 'simple_regex'
        }
    }

def test_ollama_analysis(text: str) -> Dict:
    """测试Ollama分析"""
    print("🤖 测试Ollama角色分析...")
    
    try:
        prompt = f"""请分析以下文本中的角色，并按JSON格式返回：

文本：{text[:300]}

返回格式：
{{
  "characters": [
    {{"name": "角色名", "frequency": 出现次数, "gender": "male/female/neutral", "personality": "brave/gentle/calm"}}
  ]
}}"""

        payload = {
            "model": "qwen3:30b",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "max_tokens": 1000
            }
        }
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('response', '')
            print(f"🤖 AI响应: {ai_response[:200]}...")
            
            # 尝试提取JSON
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = ai_response[json_start:json_end]
                data = json.loads(json_str)
                
                return {
                    'detected_characters': data.get('characters', []),
                    'processing_stats': {
                        'characters_found': len(data.get('characters', [])),
                        'analysis_method': 'ollama_ai'
                    }
                }
            else:
                print("❌ 无法从AI响应中提取JSON")
                return None
        else:
            print(f"❌ Ollama API调用失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Ollama分析失败: {e}")
        return None

def main():
    print("🚀 开始角色分析测试\n")
    
    # 测试文本
    test_text = """
    孙悟空对唐僧说道："师父，前面山中有妖气，必定有妖精作怪。"
    唐僧听了，心中惊慌，连忙说道："悟空，那我们该如何是好？"
    猪八戒在旁说道："师父莫慌，让老猪去探个究竟。"
    沙僧也说道："二师兄说得对，我们一起去看看。"
    只见白骨精在山洞中修炼，忽然感到有人接近，便说道："何方妖怪，敢来我的地盘？"
    """
    
    print(f"📝 测试文本: {test_text.strip()}\n")
    
    # 测试1: Ollama连接
    ollama_available = test_ollama_connection()
    
    # 测试2: 简单角色提取
    print("\n" + "="*50)
    simple_result = simple_character_extraction(test_text)
    print("✅ 简单分析结果:")
    print(json.dumps(simple_result, ensure_ascii=False, indent=2))
    
    # 测试3: Ollama分析 (如果可用)
    if ollama_available:
        print("\n" + "="*50)
        ollama_result = test_ollama_analysis(test_text)
        if ollama_result:
            print("✅ Ollama分析结果:")
            print(json.dumps(ollama_result, ensure_ascii=False, indent=2))
        else:
            print("❌ Ollama分析失败")
    
    print("\n✨ 测试完成!")
    
    # 诊断结论
    print("\n📋 诊断结论:")
    if ollama_available:
        print("✅ Ollama服务正常，应该可以使用AI分析")
    else:
        print("❌ Ollama服务不可用，会回退到简单规则分析")
        print("💡 建议启动Ollama服务: ollama serve")

if __name__ == "__main__":
    main() 