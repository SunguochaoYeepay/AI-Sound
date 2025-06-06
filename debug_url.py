#!/usr/bin/env python3
"""
调试脚本：检查MegaTTS3 URL配置
"""
import os
import sys
sys.path.append('platform/backend/app')

from tts_client import get_tts_client

print("=== MegaTTS3 URL 调试信息 ===")
print(f"环境变量 MEGATTS3_URL: {os.getenv('MEGATTS3_URL', '未设置')}")
print(f"环境变量 MEGATTS3_API_URL: {os.getenv('MEGATTS3_API_URL', '未设置')}")
print(f"环境变量 MEGATTS3_HOST: {os.getenv('MEGATTS3_HOST', '未设置')}")
print(f"环境变量 MEGATTS3_PORT: {os.getenv('MEGATTS3_PORT', '未设置')}")

# 检查TTS客户端
try:
    client = get_tts_client()
    print(f"TTS客户端 base_url: {client.base_url}")
    print(f"TTS客户端实例ID: {id(client)}")
except Exception as e:
    print(f"获取TTS客户端失败: {e}")

print("=== 调试信息结束 ===") 