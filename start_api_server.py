#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API服务启动脚本
跨平台启动TTS API服务
"""

import os
import sys
import subprocess
import logging
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("api_starter")

def start_api_server():
    """启动API服务器"""
    # 获取项目根目录
    root_dir = os.path.dirname(os.path.abspath(__file__))
    api_dir = os.path.join(root_dir, "services", "api")
    api_app = os.path.join(api_dir, "src", "app.py")
    
    if not os.path.exists(api_app):
        logger.error(f"API应用程序不存在: {api_app}")
        return False
    
    # 切换到API目录
    os.chdir(api_dir)
    logger.info(f"切换到目录: {api_dir}")
    
    # 启动API服务器
    try:
        logger.info("正在启动API服务器...")
        
        # 使用Python解释器启动app.py
        python_cmd = sys.executable  # 获取当前Python解释器路径
        cmd = [python_cmd, "src/app.py"]
        
        # 在Windows上使用不同的方式启动进程
        if os.name == 'nt':  # Windows
            process = subprocess.Popen(
                cmd, 
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:  # Linux/Mac
            process = subprocess.Popen(cmd)
        
        logger.info(f"API服务器启动成功，进程ID: {process.pid}")
        
        # 等待几秒钟让服务器启动
        time.sleep(2)
        
        # 检查进程是否仍在运行
        if process.poll() is None:
            logger.info("API服务器正在运行")
            
            # 打印访问URL
            logger.info("API服务器地址: http://127.0.0.1:9970")
            logger.info("测试TTS功能: http://127.0.0.1:9970/api/tts/text")
            
            return True
        else:
            # 进程已退出
            return_code = process.returncode
            logger.error(f"API服务器启动失败，退出码: {return_code}")
            return False
            
    except Exception as e:
        logger.error(f"启动API服务器时出错: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("=== TTS API服务启动器 ===")
    
    try:
        success = start_api_server()
        if success:
            logger.info("服务器已启动，请保持此窗口打开")
            logger.info("按Ctrl+C停止服务器")
            
            # 保持脚本运行，直到用户按Ctrl+C
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("收到停止信号，正在关闭...")
        else:
            logger.error("服务器启动失败")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("操作被用户取消")
    except Exception as e:
        logger.error(f"发生未预期的错误: {str(e)}")
        sys.exit(1) 