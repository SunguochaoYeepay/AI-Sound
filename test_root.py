#!/usr/bin/env python3
"""
测试API根路径
"""

import requests
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_root")

# API地址
API_URL = "http://127.0.0.1:9939"

def test_root():
    """测试API根路径"""
    try:
        response = requests.get(API_URL)
        logger.info(f"状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    test_root() 