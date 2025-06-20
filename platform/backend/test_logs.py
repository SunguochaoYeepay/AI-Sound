#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试日志记录脚本
手动创建一些测试日志来验证功能
"""

import sys
sys.path.append(".")

from app.utils import log_system_event, log_api_request, log_tts_operation
import time
import random

def create_test_logs():
    """创建测试日志"""
    print("开始创建测试日志...")
    
    # 系统日志
    log_system_event("系统启动完成", "info")
    log_system_event("配置文件加载成功", "info")
    log_system_event("数据库连接建立", "info")
    
    # 模拟一些警告
    log_system_event("内存使用率较高", "warning")
    log_system_event("磁盘空间不足", "warning")
    
    # 模拟一些错误
    log_system_event("TTS服务连接失败", "error", details={"service": "TTS", "retry_count": 3})
    log_system_event("文件上传失败", "error", details={"file": "test.mp3", "size": 1024000})
    
    # 模拟API请求日志
    for i in range(10):
        status_codes = [200, 200, 200, 200, 404, 500]  # 大部分成功，少量错误
        status = random.choice(status_codes)
        response_time = random.uniform(50, 500)
        
        log_api_request(
            method="GET",
            path=f"/api/v1/test/endpoint/{i}",
            status_code=status,
            response_time=response_time,
            user_id=f"user_{random.randint(1, 10)}",
            ip_address="127.0.0.1"
        )
    
    # 模拟TTS操作日志  
    tts_operations = ["synthesis", "voice_clone", "analysis"]
    statuses = ["success", "success", "success", "failed"]
    
    for i in range(5):
        operation = random.choice(tts_operations)
        status = random.choice(statuses)
        duration = random.uniform(1, 10) if status == "success" else None
        
        log_tts_operation(
            operation=operation,
            status=status,
            duration=duration,
            text_length=random.randint(50, 500),
            voice_model="standard_model_v1",
            error_message="网络连接超时" if status == "failed" else None
        )
    
    print("测试日志创建完成！")

if __name__ == "__main__":
    create_test_logs()