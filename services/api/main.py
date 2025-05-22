#!/usr/bin/env python3
"""
MegaTTS API服务启动脚本
"""

import os
import sys
import importlib
import uvicorn
import argparse
import logging
from typing import Dict, Any
from pathlib import Path

# 设置项目路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(f"项目根目录: {ROOT_DIR}")

# 添加关键路径
sys.path.insert(0, os.path.join(ROOT_DIR, "services", "api", "src"))
sys.path.insert(0, os.path.join(ROOT_DIR, "services", "api"))

# 确保MegaTTS3在路径中
megatts_path = os.path.join(ROOT_DIR, "MegaTTS3")
if megatts_path not in sys.path:
    sys.path.insert(0, megatts_path)  # 优先加载，确保覆盖任何可能的冲突
    print(f"添加MegaTTS3到Python路径: {megatts_path}")

# 模型路径 - 修改为用户提供的正确路径
MODEL_PATH = os.path.join("D:\\AI-Sound", "data", "checkpoints", "megatts3_base.pth")
print(f"模型路径: {MODEL_PATH}")
# 设置为环境变量以便其他模块使用
os.environ["MODEL_PATH"] = MODEL_PATH

# 输出目录
OUTPUT_DIR = os.path.join(ROOT_DIR, "services", "api", "output")
print(f"输出目录: {OUTPUT_DIR}")
os.environ["OUTPUT_DIR"] = OUTPUT_DIR

# 打印Python路径以便调试
print(f"Python路径: {sys.path}")

# 导入应用
try:
    # 导入本地API应用
    from api.server import app
    print("成功导入API应用")
except ImportError as e:
    print(f"导入API应用失败: {e}")
    sys.exit(1)

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="MegaTTS API服务")
    
    # 添加参数
    parser.add_argument("--host", type=str, default="127.0.0.1", help="主机地址")
    parser.add_argument("--port", type=int, default=9930, help="端口号")
    parser.add_argument("--reload", action="store_true", help="是否启用热重载")
    parser.add_argument("--debug", action="store_true", help="是否启用调试日志级别")
    parser.add_argument("--workers", type=int, default=1, help="工作进程数")
    
    return parser.parse_args()

def main():
    """主函数"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 解析命令行参数
    args = parse_arguments()
    
    # 启动服务器
    logging.info(f"正在启动API服务 - http://{args.host}:{args.port}")
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="debug" if args.debug else "info",
        workers=args.workers if not args.reload else 1  # 热重载模式下只能使用单进程
    )

if __name__ == "__main__":
    main()