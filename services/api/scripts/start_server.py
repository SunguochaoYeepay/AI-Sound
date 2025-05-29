#!/usr/bin/env python3
"""
MegaTTS API服务统一启动脚本
支持从任何目录启动服务
"""

import os
import sys
import argparse
import subprocess
import time
import json
import logging
from pathlib import Path
import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("start_server")

def find_project_root():
    """
    查找项目根目录
    
    Returns:
        Path: 项目根目录
    """
    # 当前脚本所在目录
    current_dir = Path(__file__).resolve().parent
    
    # 检查是否在容器环境中
    docker_path = Path("/app")
    if docker_path.exists():
        logger.info("检测到Docker容器环境，使用/app作为项目根目录")
        return docker_path
    
    # 尝试不同的方式找到根目录
    candidates = [
        current_dir,  # 当前目录
        current_dir.parent.parent,  # 向上两级目录
        Path("D:/AI-Sound")  # 固定路径
    ]
    
    for path in candidates:
        if (path / "MegaTTS3").exists():
            return path
    
    # 如果都找不到，使用当前目录
    logger.warning("无法确定项目根目录，使用当前目录")
    return current_dir

def check_server_status(host, port, max_retries=5):
    """
    检查服务器状态
    
    Args:
        host: 主机地址
        port: 端口号
        max_retries: 最大重试次数
        
    Returns:
        bool: 服务器是否已启动
    """
    url = f"http://{host}:{port}/health"
    
    for i in range(max_retries):
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"服务器已启动，版本: {data.get('version')}")
                return True
        except Exception:
            logger.debug(f"服务器未响应 ({i+1}/{max_retries})")
        
        # 等待一段时间再重试
        time.sleep(1)
    
    return False

def start_server(args):
    """
    启动API服务器
    
    Args:
        args: 命令行参数
    """
    # 查找项目根目录
    root_dir = find_project_root()
    api_dir = root_dir / "services" / "api"
    
    if not api_dir.exists():
        logger.error(f"API目录不存在: {api_dir}")
        sys.exit(1)
    
    # 构建命令
    main_script = api_dir / "main.py"
    
    if not main_script.exists():
        logger.error(f"主脚本不存在: {main_script}")
        sys.exit(1)
    
    command = [
        sys.executable,
        str(main_script),
        "--host", args.host,
        "--port", str(args.port)
    ]
    
    if args.reload:
        command.append("--reload")
    
    if args.debug:
        command.append("--debug")
    
    if args.workers > 1:
        command.extend(["--workers", str(args.workers)])
    
    # 设置环境变量
    env = os.environ.copy()
    
    # 在Docker环境中使用固定路径
    if root_dir == Path("/app"):
        env["MODEL_PATH"] = "/app/data/checkpoints/megatts3_base.pth"
        logger.info(f"Docker环境中使用模型路径: {env['MODEL_PATH']}")
        # 确保模型文件目录存在
        os.makedirs("/app/data/checkpoints", exist_ok=True)
        
        # 检查模型文件是否存在
        if not Path(env["MODEL_PATH"]).exists():
            logger.warning(f"模型文件不存在: {env['MODEL_PATH']}")
            # 尝试从其他可能的位置复制模型文件
            possible_paths = [
                "/app/checkpoints/megatts3_base.pth",
                "/app/MegaTTS3/checkpoints/megatts3_base.pth"
            ]
            for path in possible_paths:
                if Path(path).exists():
                    logger.info(f"找到模型文件: {path}，复制到目标位置")
                    os.system(f"cp {path} {env['MODEL_PATH']}")
                    break
    else:
        env["MODEL_PATH"] = str(root_dir / "data" / "checkpoints" / "megatts3_base.pth")
        
    env["OUTPUT_DIR"] = str(api_dir / "output")
    env["VOICE_FEATURES_DIR"] = str(root_dir / "data" / "voice_features")
    
    try:
        # 输出启动信息
        logger.info(f"项目根目录: {root_dir}")
        logger.info(f"API目录: {api_dir}")
        logger.info(f"正在启动API服务 - http://{args.host}:{args.port}")
        
        # 创建必要的目录
        os.makedirs(str(root_dir / "data" / "voice_features"), exist_ok=True)
        os.makedirs(str(root_dir / "data" / "checkpoints"), exist_ok=True)
        os.makedirs(str(api_dir / "output"), exist_ok=True)
        os.makedirs(str(api_dir / "output" / "single"), exist_ok=True)
        os.makedirs(str(api_dir / "output" / "novels"), exist_ok=True)
        os.makedirs(str(api_dir / "output" / "previews"), exist_ok=True)
        
        # 使用 subprocess 运行
        process = subprocess.Popen(
            command,
            cwd=str(api_dir),
            env=env,
            stdout=subprocess.PIPE if not args.verbose else None,
            stderr=subprocess.PIPE if not args.verbose else None,
        )
        
        # 检查服务器是否启动成功
        if check_server_status(args.host, args.port):
            logger.info(f"API服务已成功启动: http://{args.host}:{args.port}")
            logger.info(f"健康检查URL: http://{args.host}:{args.port}/health")
            logger.info(f"管理命令: --stop 停止服务")
            
            if not args.verbose:
                logger.info("服务在后台运行中 (使用 --verbose 参数查看详细日志)")
                
                # 保存进程PID
                pid_file = api_dir / ".server_pid"
                with open(pid_file, "w") as f:
                    json.dump({
                        "pid": process.pid,
                        "host": args.host,
                        "port": args.port,
                        "started_at": time.time()
                    }, f)
                
                return
            
            # 如果使用 verbose 模式，将输出重定向到终端
            while True:
                if process.poll() is not None:
                    break
                    
                if args.verbose and process.stdout:
                    output = process.stdout.readline()
                    if output:
                        sys.stdout.write(output.decode())
                        sys.stdout.flush()
                else:
                    # 如果没有启用verbose或者stdout为None，就等待进程结束
                    time.sleep(1)
        else:
            logger.error(f"API服务启动失败，请检查日志")
            process.terminate()
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"启动服务失败: {str(e)}")
        sys.exit(1)

def stop_server(args):
    """
    停止API服务器
    
    Args:
        args: 命令行参数
    """
    # 查找项目根目录
    root_dir = find_project_root()
    api_dir = root_dir / "services" / "api"
    pid_file = api_dir / ".server_pid"
    
    if not pid_file.exists():
        logger.error("找不到服务PID文件，服务可能未运行")
        
        # 尝试直接检查端口
        if args.port and check_server_status("127.0.0.1", args.port, max_retries=1):
            logger.info(f"服务在端口 {args.port} 上运行，但无法自动停止，请手动关闭进程")
        
        return
    
    try:
        with open(pid_file, "r") as f:
            data = json.load(f)
            
        pid = data.get("pid")
        host = data.get("host", "127.0.0.1")
        port = data.get("port", 9930)
        
        if not pid:
            logger.error("PID文件格式错误")
            return
        
        logger.info(f"正在停止服务 (PID: {pid}, http://{host}:{port})")
        
        # 在Windows上使用taskkill，在Unix上使用kill
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=False)
        else:
            subprocess.run(["kill", "-9", str(pid)], check=False)
        
        # 删除PID文件
        pid_file.unlink()
        
        logger.info("服务已停止")
        
    except Exception as e:
        logger.error(f"停止服务失败: {str(e)}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="MegaTTS API服务控制脚本")
    
    # 命令选择
    parser.add_argument("--stop", action="store_true", help="停止API服务")
    
    # 服务配置
    parser.add_argument("--host", type=str, default="127.0.0.1", help="主机地址")
    parser.add_argument("--port", type=int, default=9930, help="端口号")
    parser.add_argument("--reload", action="store_true", help="是否启用热重载")
    parser.add_argument("--debug", action="store_true", help="是否启用调试日志级别")
    parser.add_argument("--workers", type=int, default=1, help="工作进程数")
    parser.add_argument("--verbose", action="store_true", help="打印详细日志")
    
    args = parser.parse_args()
    
    # 根据命令执行不同操作
    if args.stop:
        stop_server(args)
    else:
        start_server(args)

if __name__ == "__main__":
    main() 