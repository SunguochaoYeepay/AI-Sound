"""
AI-Sound TTS系统API服务入口
基于新架构的统一入口文件
"""

import os
import argparse
import uvicorn
import logging

# 配置基础日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("main")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='AI-Sound TTS API服务')
    
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='API服务主机地址')
    parser.add_argument('--port', type=int, default=9930,
                        help='API服务端口')
    parser.add_argument('--reload', action='store_true',
                        help='是否启用热重载')
    parser.add_argument('--workers', type=int, default=1,
                        help='工作进程数量')
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 从环境变量中读取配置
    host = os.environ.get('API_HOST', args.host)
    port = int(os.environ.get('API_PORT', args.port))
    reload = os.environ.get('API_RELOAD', '').lower() == 'true' or args.reload
    workers = int(os.environ.get('API_WORKERS', args.workers))
    
    logger.info(f"正在启动AI-Sound TTS API服务")
    logger.info(f"配置: host={host}, port={port}, reload={reload}, workers={workers}")
    
    # 启动服务 - 使用新架构的应用
    try:
        uvicorn.run(
            "src.api.app:app",  # 使用新架构的应用入口
            host=host,
            port=port,
            reload=reload,
            workers=workers if not reload else 1,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"启动API服务失败: {e}")
        raise


if __name__ == "__main__":
    main()