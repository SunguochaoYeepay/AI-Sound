"""
声纹特征提取测试脚本
"""

import os
import sys
import requests
import argparse
from pathlib import Path

def test_extract_voice_feature(audio_path, api_url="http://127.0.0.1:9930"):
    """测试声纹特征提取API"""
    print(f"\n===== 测试声纹特征提取API =====")
    print(f"音频文件: {audio_path}")
    
    if not os.path.exists(audio_path):
        print(f"❌ 音频文件不存在: {audio_path}")
        return
    
    # 准备表单数据
    name = os.path.splitext(os.path.basename(audio_path))[0]
    metadata = {
        "name": name,
        "description": f"测试提取的声纹特征 - {name}",
        "tags": "test,voice,custom",
        "gender": "male"  # 可以根据需要修改
    }
    
    files = {
        "voice_file": (os.path.basename(audio_path), open(audio_path, "rb"), "audio/wav")
    }
    
    try:
        # 发送请求
        response = requests.post(
            f"{api_url}/api/voices/extract",
            files=files,
            data=metadata,
            timeout=60
        )
        
        # 检查响应
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✅ 声纹特征提取成功:")
                voice_id = result.get("voice_id")
                name = result.get("name")
                preview_url = result.get("preview_url")
                feature_url = result.get("feature_url")
                
                print(f"  声音ID: {voice_id}")
                print(f"  名称: {name}")
                print(f"  预览URL: {preview_url}")
                print(f"  特征URL: {feature_url}")
                
                # 获取声音详细信息
                detail_response = requests.get(f"{api_url}/api/voices/{voice_id}", timeout=30)
                if detail_response.status_code == 200:
                    detail = detail_response.json()
                    if detail.get("success"):
                        voice = detail.get("voice", {})
                        print("\n声音详细信息:")
                        print(f"  描述: {voice.get('description')}")
                        print(f"  标签: {', '.join(voice.get('tags', []))}")
                        print(f"  特征形状: {voice.get('feature_shape')}")
                        print(f"  属性: {voice.get('attributes')}")
                
                return voice_id
            else:
                print(f"❌ 声纹特征提取返回错误: {result}")
        else:
            print(f"❌ 声纹特征提取请求失败: HTTP {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ 声纹特征提取请求异常: {str(e)}")
    finally:
        # 关闭文件
        files["voice_file"][1].close()
    
    return None

def test_list_voices(api_url="http://127.0.0.1:9930"):
    """测试声音API接口"""
    print("\n===== 测试获取声音列表API =====")
    
    try:
        # 获取声音列表
        response = requests.get(f"{api_url}/api/voices/list", timeout=30)
        assert response.status_code == 200, f"获取声音列表失败: {response.text}"
        
        result = response.json()
        assert result["success"], f"API返回错误: {result}"
        print(f"自定义声纹特征数量: {result.get('count', 0)}")
        
        # 获取声音标签
        response = requests.get(f"{api_url}/api/voices/tags", timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"声音标签数量: {len(result.get('tags', []))}")
            else:
                print(f"获取声音标签返回错误: {result}")
        
        return True
    except Exception as e:
        print(f"❌ 获取声音列表失败: {str(e)}")
        return False

def test_tags(api_url="http://127.0.0.1:9930"):
    """测试获取标签API"""
    print(f"\n===== 测试获取声音标签API =====")
    
    try:
        response = requests.get(f"{api_url}/api/voices/tags", timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                tags = result.get("tags", [])
                print(f"找到 {len(tags)} 个标签:")
                for tag in tags:
                    print(f"  {tag.get('name')}: {tag.get('count')} 个声音")
                
                attributes = result.get("attributes", {})
                print("\n属性统计:")
                for attr_name, attr_values in attributes.items():
                    print(f"  {attr_name}:")
                    for value in attr_values:
                        print(f"    {value.get('name')}: {value.get('count')} 个声音")
            else:
                print(f"❌ 获取标签返回错误: {result}")
        else:
            print(f"❌ 获取标签请求失败: HTTP {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ 获取标签请求异常: {str(e)}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试声纹特征API")
    parser.add_argument("--audio", help="用于提取声纹特征的音频文件路径")
    parser.add_argument("--url", default="http://127.0.0.1:9930", help="API服务地址")
    parser.add_argument("--list", action="store_true", help="列出所有声音")
    parser.add_argument("--tags", action="store_true", help="获取标签统计")
    args = parser.parse_args()
    
    # 解析参数
    api_url = args.url
    
    # 执行测试
    if args.list or args.tags:
        if args.list:
            test_list_voices(api_url)
        if args.tags:
            test_tags(api_url)
    elif args.audio:
        # 提取声纹特征并测试相关功能
        voice_id = test_extract_voice_feature(args.audio, api_url)
        if voice_id:
            # 展示所有声音
            test_list_voices(api_url)
            # 展示标签
            test_tags(api_url)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 