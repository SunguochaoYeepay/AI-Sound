#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的日志数据创建脚本
直接通过SQL插入，避免字段类型问题
"""

import sys
sys.path.append(".")

from app.database import engine
from sqlalchemy import text
import datetime
import json

def create_simple_logs():
    """创建简单的测试日志数据"""
    print("开始创建简单测试日志...")
    
    logs_data = [
        {
            'level': 'INFO',
            'module': 'SYSTEM',
            'message': '系统启动完成',
            'details': json.dumps({'startup_time': '2.3s', 'modules_loaded': 15}),
            'user_id': 1,
        },
        {
            'level': 'INFO',
            'module': 'API',
            'message': 'API服务启动成功',
            'details': json.dumps({'port': 8000, 'workers': 4}),
            'user_id': 1,
        },
        {
            'level': 'WARNING',
            'module': 'DATABASE',
            'message': '数据库连接池达到80%',
            'details': json.dumps({'pool_size': 20, 'active_connections': 16}),
            'user_id': None,
        },
        {
            'level': 'ERROR',
            'module': 'TTS',
            'message': 'TTS引擎连接失败',
            'details': json.dumps({'error': 'Connection timeout', 'retry_count': 3}),
            'user_id': 2,
        },
        {
            'level': 'INFO',
            'module': 'API',
            'message': 'GET /api/v1/characters - 200',
            'details': json.dumps({'method': 'GET', 'status': 200, 'response_time': 45.2}),
            'user_id': 3,
        },
        {
            'level': 'CRITICAL',
            'module': 'SYSTEM',
            'message': '磁盘空间不足',
            'details': json.dumps({'disk_usage': '95%', 'free_space': '2.1GB'}),
            'user_id': None,
        },
        {
            'level': 'DEBUG',
            'module': 'SYNTHESIS',
            'message': '语音合成任务开始',
            'details': json.dumps({'task_id': 'syn_123', 'text_length': 256, 'character': 'narrator'}),
            'user_id': 4,
        },
        {
            'level': 'INFO',
            'module': 'WEBSOCKET',
            'message': '客户端连接建立',
            'details': json.dumps({'client_ip': '192.168.1.100', 'session_id': 'ws_abc123'}),
            'user_id': 5,
        },
        {
            'level': 'WARNING',
            'module': 'FILE',
            'message': '上传文件大小超过建议值',
            'details': json.dumps({'file_size': '150MB', 'recommended_max': '100MB', 'filename': 'audio.wav'}),
            'user_id': 6,
        },
        {
            'level': 'ERROR',
            'module': 'AUTH',
            'message': '用户认证失败',
            'details': json.dumps({'username': 'test_user', 'reason': 'invalid_password', 'ip': '192.168.1.200'}),
            'user_id': None,
        }
    ]
    
    conn = engine.connect()
    
    try:
        for log in logs_data:
            sql = text("""
                INSERT INTO system_logs (level, module, message, details, user_id, created_at, updated_at)
                VALUES (:level, :module, :message, :details, :user_id, :created_at, :updated_at)
            """)
            
            conn.execute(sql, {
                'level': log['level'],
                'module': log['module'], 
                'message': log['message'],
                'details': log['details'],
                'user_id': log['user_id'],
                'created_at': datetime.datetime.now(),
                'updated_at': datetime.datetime.now()
            })
            
        conn.commit()
        print(f"✅ 成功创建了 {len(logs_data)} 条测试日志")
        
    except Exception as e:
        print(f"❌ 创建日志失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_simple_logs()