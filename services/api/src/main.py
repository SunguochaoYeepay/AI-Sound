"""
MegaTTS3 API服务入口
"""

import os
import argparse
import uvicorn
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("main")

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='MegaTTS3 API服务')
    
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='API服务主机地址')
    parser.add_argument('--port', type=int, default=7929,
                        help='API服务端口')
    parser.add_argument('--reload', action='store_true',
                        help='是否启用热重载')
    parser.add_argument('--workers', type=int, default=1,
                        help='工作进程数量')
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    # 启动API服务
    logger.info(f"正在启动API服务，地址：{args.host}:{args.port}")
    
    # 从环境变量中读取配置
    host = os.environ.get('API_HOST', args.host)
    port = int(os.environ.get('API_PORT', args.port))
    reload = os.environ.get('API_RELOAD', '').lower() == 'true' or args.reload
    workers = int(os.environ.get('API_WORKERS', args.workers))
    
    # 启动服务
    uvicorn.run(
        "src.api.server:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers
    )

if __name__ == "__main__":
    main()