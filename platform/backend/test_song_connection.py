#!/usr/bin/env python3
"""
测试AI-Sound后端与SongGeneration服务的连接
"""

import asyncio
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_connection():
    """测试连接"""
    base_url = "http://localhost:7862"
    
    async with httpx.AsyncClient(timeout=10) as client:
        # 测试简单端点
        try:
            logger.info("测试根端点...")
            response = await client.get(f"{base_url}/")
            logger.info(f"根端点响应: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"根端点失败: {e}")
        
        # 测试ping端点
        try:
            logger.info("测试ping端点...")
            response = await client.get(f"{base_url}/ping")
            logger.info(f"ping端点响应: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"ping端点失败: {e}")
        
        # 测试健康检查端点
        try:
            logger.info("测试健康检查端点...")
            response = await client.get(f"{base_url}/health")
            logger.info(f"健康检查响应: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"健康检查数据: {data}")
                logger.info(f"状态: {data.get('status')}")
            else:
                logger.error(f"健康检查失败响应: {response.text}")
        except Exception as e:
            logger.error(f"健康检查异常: {e}")
        
        # 测试场景分析端点
        try:
            logger.info("测试场景分析端点...")
            response = await client.post(
                f"{base_url}/analyze-scene",
                json="测试文本内容"
            )
            logger.info(f"场景分析响应: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                logger.info(f"场景分析结果: {data}")
            else:
                logger.error(f"场景分析失败: {response.text}")
        except Exception as e:
            logger.error(f"场景分析异常: {e}")

if __name__ == "__main__":
    print("🔍 开始测试SongGeneration服务连接...")
    asyncio.run(test_connection())
    print("✅ 测试完成") 