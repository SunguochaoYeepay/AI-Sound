#!/usr/bin/env python3
"""
AI-Sound简化部署脚本
只启动ESPnet服务，避免复杂的构建过程
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

class SimpleDeployer:
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
    
    def check_services(self):
        """检查现有服务状态"""
        self.log_step("检查现有服务状态...")
        
        # 检查MegaTTS3服务
        success, output = self.run_command(['docker', 'ps', '--filter', 'name=megatts3-service'])
        megatts3_running = success and len(output) > 1
        
        # 检查ESPnet服务
        success, output = self.run_command(['docker', 'ps', '--filter', 'name=ai-sound-espnet'])
        espnet_running = success and len(output) > 1
        
        self.log_step(f"MegaTTS3服务: {'✅ 运行中' if megatts3_running else '❌ 未运行'}")
        self.log_step(f"ESPnet服务: {'✅ 运行中' if espnet_running else '❌ 未运行'}")
        
        return megatts3_running, espnet_running
    
    def start_espnet_service(self):
        """启动ESPnet服务"""
        self.log_step("启动ESPnet TTS服务...")
        
        # 先停止可能存在的容器
        self.run_command(['docker', 'stop', 'ai-sound-espnet-simple'])
        self.run_command(['docker', 'rm', 'ai-sound-espnet-simple'])
        
        cmd = [
            'docker', 'run', '-d',
            '--name', 'ai-sound-espnet-simple',
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
    
    def test_services(self):
        """测试服务连通性"""
        self.log_step("测试服务连通性...")
        
        import requests
        
        services = [
            ("MegaTTS3", "http://localhost:7929"),
            ("ESPnet", "http://localhost:9001/health")
        ]
        
        for name, url in services:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    self.log_step(f"✅ {name}服务连通正常")
                else:
                    self.log_step(f"⚠️ {name}服务响应异常: {response.status_code}")
            except Exception as e:
                self.log_step(f"❌ {name}服务连接失败: {e}")
    
    def deploy(self):
        """执行简化部署"""
        self.log_step("开始AI-Sound简化部署...")
        
        try:
            # 1. 检查现有服务
            megatts3_running, espnet_running = self.check_services()
            
            if not megatts3_running:
                self.log_step("⚠️ MegaTTS3服务未运行，请先启动: docker start megatts3-service")
                return False
            
            # 2. 启动ESPnet服务（如果未运行）
            if not espnet_running:
                if not self.start_espnet_service():
                    return False
                
                # 等待服务启动
                self.log_step("等待ESPnet服务启动...")
                time.sleep(20)
            else:
                self.log_step("✅ ESPnet服务已在运行")
            
            # 3. 测试服务连通性
            self.test_services()
            
            self.log_step("🎉 简化部署完成！")
            self.log_step("服务访问地址:")
            self.log_step("  - MegaTTS3: http://localhost:7929")
            self.log_step("  - ESPnet: http://localhost:9001")
            self.log_step("  - ESPnet健康检查: http://localhost:9001/health")
            
            return True
            
        except Exception as e:
            logger.error(f"部署过程中出现错误: {e}")
            return False

def main():
    """主函数"""
    deployer = SimpleDeployer()
    
    try:
        success = deployer.deploy()
        if success:
            print("\n🎉 简化部署成功完成！")
            print("\n📝 下一步:")
            print("1. 测试MegaTTS3: curl http://localhost:7929")
            print("2. 测试ESPnet: curl http://localhost:9001/health")
            print("3. 如需API统一接口，请解决网络问题后运行完整部署")
            sys.exit(0)
        else:
            print("\n❌ 简化部署失败")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断部署")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 部署过程中出现未预期的错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 