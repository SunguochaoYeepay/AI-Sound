#!/usr/bin/env python3
"""
AI-Sound增量部署脚本
复用现有MegaTTS3服务，只启动新增的ESPnet和API服务
"""

import subprocess
import sys
import time
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IncrementalDeployer:
    def __init__(self):
        self.project_root = Path(__file__).parent
        
    def log_step(self, message):
        """记录步骤"""
        logger.info(f"🚀 {message}")
        print(f"\n{'='*60}")
        print(f"🚀 {message}")
        print(f"{'='*60}")
    
    def run_command(self, cmd, cwd=None):
        """执行命令"""
        try:
            process = subprocess.Popen(
                cmd, 
                cwd=cwd or self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )
            
            # 实时读取输出
            output_lines = []
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    print(line.rstrip())
                    output_lines.append(line.rstrip())
            
            return_code = process.wait()
            
            if return_code == 0:
                logger.info("命令执行成功")
                return True, output_lines
            else:
                logger.error(f"命令执行失败，返回码: {return_code}")
                return False, output_lines
                
        except Exception as e:
            logger.error(f"执行命令时出错: {e}")
            return False, [str(e)]
    
    def check_existing_services(self):
        """检查现有服务状态"""
        self.log_step("检查现有服务状态...")
        
        # 检查MegaTTS3服务
        success, output = self.run_command(['docker', 'ps', '--filter', 'name=megatts3-service'])
        if success and len(output) > 1:
            self.log_step("✅ 发现现有MegaTTS3服务正在运行")
            return True
        else:
            self.log_step("❌ 未发现运行中的MegaTTS3服务")
            return False
    
    def start_espnet_service(self):
        """启动ESPnet服务"""
        self.log_step("启动ESPnet TTS服务...")
        
        cmd = [
            'docker', 'run', '-d',
            '--name', 'ai-sound-espnet-incremental',
            '--network', 'ai-sound-network',
            '-p', '9001:9001',
            '-v', f'{self.project_root}/MegaTTS/espnet:/workspace',
            '-e', 'CUDA_VISIBLE_DEVICES=0',
            '-e', 'PYTHONPATH=/workspace',
            '--restart', 'unless-stopped',
            '--gpus', 'all',
            'my-espnet-gradio:latest',
            '/bin/bash', '-c', 'cd /workspace && python espnet_server.py'
        ]
        
        success, output = self.run_command(cmd)
        if success:
            self.log_step("✅ ESPnet服务启动成功")
            return True
        else:
            self.log_step("❌ ESPnet服务启动失败")
            return False
    
    def start_api_service(self):
        """启动API服务"""
        self.log_step("启动API统一服务...")
        
        # 首先构建API服务镜像
        build_cmd = [
            'docker', 'build',
            '-f', 'services/api/Dockerfile.local',
            '-t', 'ai-sound-api:incremental',
            '.'
        ]
        
        success, output = self.run_command(build_cmd)
        if not success:
            self.log_step("❌ API服务镜像构建失败")
            return False
        
        # 启动API服务
        run_cmd = [
            'docker', 'run', '-d',
            '--name', 'ai-sound-api-incremental',
            '--network', 'ai-sound-network',
            '-p', '9930:9930',
            '-v', f'{self.project_root}/data/output:/app/output',
            '-v', f'{self.project_root}/data/temp:/app/data',
            '-e', 'OUTPUT_DIR=/app/output',
            '-e', 'API_HOST=0.0.0.0',
            '-e', 'API_PORT=9930',
            '-e', 'MEGATTS3_URL=http://host.docker.internal:7929',
            '-e', 'ESPNET_URL=http://ai-sound-espnet-incremental:9001',
            '-e', 'DB_HOST=ai-sound-mongodb',
            '-e', 'DB_PORT=27017',
            '-e', 'DB_DATABASE=ai_sound',
            '--add-host', 'host.docker.internal:host-gateway',
            '--restart', 'unless-stopped',
            'ai-sound-api:incremental'
        ]
        
        success, output = self.run_command(run_cmd)
        if success:
            self.log_step("✅ API服务启动成功")
            return True
        else:
            self.log_step("❌ API服务启动失败")
            return False
    
    def create_network(self):
        """创建Docker网络"""
        self.log_step("创建Docker网络...")
        
        # 检查网络是否存在
        check_cmd = ['docker', 'network', 'ls', '--filter', 'name=ai-sound-network']
        success, output = self.run_command(check_cmd)
        
        if success and any('ai-sound-network' in line for line in output):
            self.log_step("✅ Docker网络已存在")
            return True
        
        # 创建网络
        create_cmd = ['docker', 'network', 'create', 'ai-sound-network']
        success, output = self.run_command(create_cmd)
        
        if success:
            self.log_step("✅ Docker网络创建成功")
            return True
        else:
            self.log_step("❌ Docker网络创建失败")
            return False
    
    def cleanup_existing_containers(self):
        """清理可能存在的同名容器"""
        self.log_step("清理现有容器...")
        
        containers = [
            'ai-sound-espnet-incremental',
            'ai-sound-api-incremental'
        ]
        
        for container in containers:
            # 停止容器
            self.run_command(['docker', 'stop', container])
            # 删除容器
            self.run_command(['docker', 'rm', container])
        
        self.log_step("✅ 容器清理完成")
    
    def check_services_health(self):
        """检查服务健康状态"""
        self.log_step("检查服务健康状态...")
        
        import requests
        import time
        
        services = [
            ("ESPnet", "http://localhost:9001/health"),
            ("API", "http://localhost:9930/health")
        ]
        
        for name, url in services:
            for attempt in range(5):
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        self.log_step(f"✅ {name}服务健康检查通过")
                        break
                    else:
                        self.log_step(f"⚠️ {name}服务响应异常: {response.status_code}")
                except Exception as e:
                    self.log_step(f"⚠️ {name}服务健康检查失败 (尝试 {attempt+1}/5): {e}")
                    if attempt < 4:
                        time.sleep(10)
    
    def deploy(self):
        """执行增量部署"""
        self.log_step("开始AI-Sound增量部署...")
        
        try:
            # 1. 检查现有服务
            if not self.check_existing_services():
                self.log_step("⚠️ 警告: 未发现现有MegaTTS3服务，但继续部署")
            
            # 2. 创建网络
            if not self.create_network():
                return False
            
            # 3. 清理现有容器
            self.cleanup_existing_containers()
            
            # 4. 启动ESPnet服务
            if not self.start_espnet_service():
                return False
            
            # 5. 启动API服务
            if not self.start_api_service():
                return False
            
            # 6. 等待服务启动
            self.log_step("等待服务启动...")
            time.sleep(30)
            
            # 7. 健康检查
            self.check_services_health()
            
            self.log_step("🎉 增量部署完成！")
            self.log_step("服务访问地址:")
            self.log_step("  - MegaTTS3: http://localhost:7929 (现有)")
            self.log_step("  - ESPnet: http://localhost:9001")
            self.log_step("  - API统一接口: http://localhost:9930")
            
            return True
            
        except Exception as e:
            logger.error(f"部署过程中出现错误: {e}")
            return False

def main():
    """主函数"""
    deployer = IncrementalDeployer()
    
    try:
        success = deployer.deploy()
        if success:
            print("\n🎉 增量部署成功完成！")
            sys.exit(0)
        else:
            print("\n❌ 增量部署失败")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断部署")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 部署过程中出现未预期的错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 