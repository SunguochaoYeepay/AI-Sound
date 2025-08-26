#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MegaTTS3 标准化启动脚本
AI-Sound项目 - 语音合成引擎

使用方法:
    python start_megatts3.py [--port 7929] [--host 0.0.0.0]

参数:
    --port: 服务端口，默认7929
    --host: 服务地址，默认0.0.0.0
"""

import os
import sys
import argparse
import signal
import time

def signal_handler(signum, frame):
    """信号处理器，优雅关闭服务"""
    print("\n🛑 收到关闭信号，正在优雅关闭MegaTTS3服务...")
    sys.exit(0)

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='MegaTTS3 语音合成服务启动脚本')
    parser.add_argument('--port', type=int, default=7929, help='服务端口 (默认: 7929)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='服务地址 (默认: 0.0.0.0)')
    args = parser.parse_args()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🎤 MegaTTS3 语音合成服务启动中...")
    print(f"📍 服务地址: {args.host}:{args.port}")
    print("⏳ 正在初始化...")
    
    # 设置环境变量
    os.environ['API_PORT'] = str(args.port)
    os.environ['API_HOST'] = args.host
    
    try:
        # 导入并启动MegaTTS3 API服务
        from megatts3_api_server import app, init_model
        
        # 初始化模型
        if not init_model():
            print("❌ 模型初始化失败")
            sys.exit(1)
        
        print("✅ 模型初始化成功")
        print("🚀 启动Flask服务...")
        
        # 启动Flask服务
        app.run(
            host=args.host, 
            port=args.port, 
            debug=False,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        print("\n🛑 服务被用户中断")
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
