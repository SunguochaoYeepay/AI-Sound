#!/usr/bin/env python3
"""
AI-Sound API服务启动脚本
适用于开发和Docker环境
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# 设置环境变量
os.environ.setdefault("PYTHONPATH", str(src_dir))

if __name__ == "__main__":
    import uvicorn
    from api.app import app
    
    # 从环境变量获取配置
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8001"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    print(f"🚀 启动AI-Sound API服务...")
    print(f"📍 地址: http://{host}:{port}")
    print(f"🔧 调试模式: {debug}")
    print(f"📁 Python路径: {src_dir}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=debug,
        log_level="debug" if debug else "info"
    )