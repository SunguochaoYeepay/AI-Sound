#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MegaTTS3 API 服务启动脚本
该脚本用于在容器环境中启动TTS服务
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import time
import importlib
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 确保当前目录在python路径中
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
current_dir = Path(__file__).resolve().parent

# 安装必要的依赖
def install_dependencies():
    print("安装必要的依赖...")
    dependencies = [
        "uvicorn",
        "fastapi",
        "pydantic",
        "python-multipart",
        "psutil"
    ]
    
    for dep in dependencies:
        print(f"安装 {dep}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", dep])
        except Exception as e:
            print(f"安装 {dep} 时出错: {str(e)}")
            # 继续安装其他依赖

def check_model_file():
    """检查模型文件是否存在，如果不存在则尝试从其他位置复制"""
    print("检查模型文件...")
    model_path = Path("/app/data/checkpoints/megatts3_base.pth")
    
    if model_path.exists():
        print(f"模型文件已存在: {model_path}")
        return True
        
    # 创建目录
    os.makedirs(model_path.parent, exist_ok=True)
    
    # 尝试从其他可能的位置查找
    possible_paths = [
        Path("/app/checkpoints/megatts3_base.pth"),
        Path("/app/MegaTTS3/checkpoints/megatts3_base.pth"),
        Path("D:/AI-Sound/data/checkpoints/megatts3_base.pth")
    ]
    
    for path in possible_paths:
        if path.exists():
            print(f"找到模型文件: {path}，复制到 {model_path}")
            shutil.copy(str(path), str(model_path))
            return True
    
    print("未找到模型文件，需要手动复制到 /app/data/checkpoints/megatts3_base.pth")
    return False

def check_voice_samples():
    """检查声音样本文件"""
    voice_samples_dir = Path("/app/checkpoints/voice_samples")
    
    if voice_samples_dir.exists() and any(voice_samples_dir.iterdir()):
        wav_files = list(voice_samples_dir.glob("*.wav"))
        print(f"声音样本目录: {voice_samples_dir}")
        print(f"可用声音样本数量: {len(wav_files)}")
        for wav in wav_files:
            print(f"  - {wav.name}")
        return True
    
    print("声音样本目录不存在或为空")
    return False

def check_api_structure():
    """检查API模块结构，确保关键文件存在"""
    print("检查API模块结构...")
    
    # 检查src目录
    src_dir = current_dir / "src"
    if not src_dir.exists():
        print(f"警告: src目录不存在: {src_dir}")
        # 尝试查找替代目录
        if (current_dir / "api").exists():
            print(f"找到替代API目录: {current_dir / 'api'}")
            return current_dir / "api"
        else:
            print("无法找到API源码目录，将使用默认路径")
            return src_dir
    
    # 检查server.py文件
    server_file = src_dir / "api" / "server.py"
    if not server_file.exists():
        print(f"警告: API服务器文件不存在: {server_file}")
        # 尝试其他可能的位置
        alternative_paths = [
            current_dir / "api" / "server.py",
            current_dir / "server.py",
            current_dir / "app.py"
        ]
        
        for path in alternative_paths:
            if path.exists():
                print(f"找到替代API服务器文件: {path}")
                return path.parent
    else:
        print(f"找到API服务器文件: {server_file}")
    
    return src_dir

def start_fastapi_service():
    """直接使用uvicorn启动FastAPI服务"""
    print("导入必要模块...")
    
    # 设置环境变量
    os.environ["MODEL_PATH"] = "/app/data/checkpoints/megatts3_base.pth"
    os.environ["OUTPUT_DIR"] = "/app/services/api/output"
    os.environ["VOICE_FEATURES_DIR"] = "/app/data/voice_features" 
    
    # 确保输出目录存在
    os.makedirs(os.environ["OUTPUT_DIR"], exist_ok=True)
    os.makedirs(os.path.join(os.environ["OUTPUT_DIR"], "single"), exist_ok=True)
    os.makedirs(os.path.join(os.environ["OUTPUT_DIR"], "novels"), exist_ok=True)
    os.makedirs(os.path.join(os.environ["OUTPUT_DIR"], "previews"), exist_ok=True)
    
    # 启动API服务
    print("开始启动API服务...")
    print(f"API地址: http://0.0.0.0:9930")
    
    # 直接使用uvicorn启动
    import uvicorn
    
    # 检查API结构并获取正确的源码路径
    api_src_dir = check_api_structure()
    
    # 设置Python路径
    sys.path.insert(0, str(api_src_dir))
    print(f"添加API源码路径: {api_src_dir}")
    print(f"项目根目录: {os.environ.get('MODEL_PATH', '未设置').split('/data/')[0]}")
    print(f"模型路径: {os.environ.get('MODEL_PATH', '未设置')}")
    print(f"输出目录: {os.environ.get('OUTPUT_DIR', '未设置')}")
    print(f"Python路径: {sys.path}")
    
    try:
        # 尝试确定正确的模块路径
        module_path = "api.server:app"
        if api_src_dir.name != "src":
            # 如果不是标准的src目录，可能需要调整模块路径
            if (api_src_dir / "server.py").exists():
                module_path = "server:app"
            elif (api_src_dir / "app.py").exists():
                module_path = "app:app"
        
        # 尝试直接导入应用以验证导入路径是否正确
        try:
            if module_path == "api.server:app":
                from api.server import app
            elif module_path == "server:app":
                from server import app
            elif module_path == "app:app":
                from app import app
            print("成功导入API应用")
        except ImportError as e:
            print(f"警告: 无法导入API应用: {str(e)}")
            print("将尝试使用uvicorn直接启动")
        
        uvicorn.run(
            module_path,
            host="0.0.0.0",
            port=9930,
            reload=False,
            workers=1,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"启动API服务失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    return True

if __name__ == "__main__":
    print("=== 启动 MegaTTS3 API 服务 ===")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"Python路径: {sys.path}")
    
    # 安装依赖
    install_dependencies()
    
    # 检查模型文件
    check_model_file()
    
    # 检查声音样本
    check_voice_samples()
    
    # 启动API服务
    start_fastapi_service()