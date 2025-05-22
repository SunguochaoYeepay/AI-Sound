#!/usr/bin/env python3
"""
测试TTS API
"""

import requests
import os
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_api")

# API地址
API_URL = "http://127.0.0.1:9942/api/tts"

def test_tts():
    """测试TTS接口"""
    payload = {
        "text": "这是一段测试文本",
        "voice_id": "范闲",
        "emotion_type": "neutral",
        "emotion_intensity": 0.5,
        "return_base64": False,
        "output_format": "wav"
    }
    
    print(f"发送请求到 {API_URL}...")
    print(f"请求参数: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        logger.info(f"发送请求头: {headers}")
        response = requests.post(API_URL, json=payload, headers=headers, timeout=60)
        logger.info(f"状态码: {response.status_code}")
        logger.debug(f"响应头: {response.headers}")

        # 尝试解析响应内容
        try:
            logger.debug(f"响应内容: {response.text[:500]}")
        except Exception:
            logger.debug("无法打印响应内容")
        
        if response.status_code == 200:
            # 保存音频文件
            output_file = "api_test_output.wav"
            with open(output_file, "wb") as f:
                f.write(response.content)
            print(f"保存音频文件到 {output_file}")
            print("测试成功!")
            return True
        else:
            print(f"请求失败: {response.text}")
            return False
    
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    test_tts() 