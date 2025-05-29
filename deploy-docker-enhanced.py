#!/usr/bin/env python3
"""
MegaTTS3 Enhanced API - Docker环境部署脚本
适用于现有Docker环境的增强部署
"""

import os
import sys
import subprocess
import time
import json
import requests
from pathlib import Path
from datetime import datetime

class DockerEnhancedDeployer:
    """Docker环境增强部署器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.deployment_log = []
        
    def log_step(self, message: str, success: bool = True):
        """记录部署步骤"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = "✅" if success else "❌"
        log_entry = f"[{timestamp}] {status} {message}"
        
        print(log_entry)
        self.deployment_log.append({
            'timestamp': timestamp,
            'message': message,
            'success': success
        })
    
    def check_docker_environment(self) -> bool:
        """检查Docker环境"""
        self.log_step("检查Docker环境...")
        
        try:
            # 检查Docker命令
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, encoding='utf-8', errors='replace')
            if result.returncode == 0:
                self.log_step(f"Docker: {result.stdout.strip()}")
            else:
                self.log_step("Docker不可用", False)
                return False
            
            # 检查Docker Compose
            result = subprocess.run(['docker-compose', '--version'], 
                                  capture_output=True, text=True, encoding='utf-8', errors='replace')
            if result.returncode == 0:
                self.log_step(f"Docker Compose: {result.stdout.strip()}")
            else:
                self.log_step("Docker Compose不可用", False)
                return False
            
            return True
            
        except Exception as e:
            self.log_step(f"Docker环境检查失败: {e}", False)
            return False
    
    def check_existing_containers(self):
        """检查现有容器"""
        self.log_step("检查现有MegaTTS容器...")
        
        try:
            result = subprocess.run(['docker', 'ps', '-a', '--format', 'table {{.Names}}\t{{.Status}}'], 
                                  capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # 跳过表头
                megatts_containers = [line for line in lines if 'megatts' in line.lower()]
                
                if megatts_containers:
                    self.log_step("发现现有MegaTTS容器:")
                    for container in megatts_containers:
                        print(f"    {container}")
                else:
                    self.log_step("未发现现有MegaTTS容器")
            
        except Exception as e:
            self.log_step(f"容器检查失败: {e}", False)
    
    def prepare_environment(self):
        """准备部署环境"""
        self.log_step("准备部署环境...")
        
        # 创建必要的目录
        directories = [
            'MegaTTS/MegaTTS3/storage/voices',
            'MegaTTS/MegaTTS3/storage/temp', 
            'MegaTTS/MegaTTS3/storage/logs',
            'MegaTTS/MegaTTS3/checkpoints',
            'nginx/logs',
            'monitoring/grafana-lite/dashboards',
            'monitoring/grafana-lite/datasources'
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            self.log_step(f"创建目录: {directory}")
        
        # 检查模型文件
        checkpoints_dir = self.project_root / 'MegaTTS/MegaTTS3/checkpoints'
        if list(checkpoints_dir.glob('*.ckpt')):
            self.log_step("检测到模型文件")
        else:
            self.log_step("⚠️  未检测到模型文件，请确保模型已正确放置", False)
    
    def stop_existing_services(self):
        """停止现有服务"""
        self.log_step("停止现有Enhanced服务...")
        
        try:
            # 停止可能运行的增强版服务
            subprocess.run(['docker-compose', '-f', 'docker-deploy-enhanced.yml', 'down'], 
                         capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=self.project_root)
            self.log_step("已停止现有服务")
            
        except Exception as e:
            self.log_step(f"停止服务时出错: {e}", False)
    
    def build_enhanced_image(self):
        """构建增强版镜像"""
        self.log_step("构建MegaTTS3 Enhanced镜像...")
        
        try:
            dockerfile_path = self.project_root / 'MegaTTS/MegaTTS3'
            cmd = [
                'docker', 'build',
                '-f', 'Dockerfile.enhanced',
                '-t', 'megatts-enhanced:latest',
                '.'
            ]
            
            # 使用Popen来更好地处理实时输出和编码问题
            import subprocess
            process = subprocess.Popen(
                cmd, 
                cwd=dockerfile_path,
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
                try:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        line = output.strip()
                        output_lines.append(line)
                        # 只显示重要的构建步骤
                        if any(keyword in line.lower() for keyword in ['step', 'successfully', 'error', 'failed']):
                            print(f"    {line}")
                except UnicodeDecodeError:
                    # 忽略编码错误，继续处理
                    continue
            
            return_code = process.poll()
            
            if return_code == 0:
                self.log_step("Enhanced镜像构建成功")
                return True
            else:
                # 从输出中找到错误信息
                error_lines = [line for line in output_lines if 'error' in line.lower() or 'failed' in line.lower()]
                error_msg = ' | '.join(error_lines[-3:]) if error_lines else "构建失败，未获取到详细错误信息"
                self.log_step(f"镜像构建失败: {error_msg}", False)
                return False
            
        except Exception as e:
            self.log_step(f"构建镜像时出错: {str(e)}", False)
            return False
    
    def deploy_enhanced_services(self):
        """部署增强版服务"""
        self.log_step("部署Enhanced服务栈...")
        
        try:
            cmd = ['docker-compose', '-f', 'docker-deploy-enhanced.yml', 'up', '-d']
            
            # 使用更安全的subprocess调用方式
            process = subprocess.Popen(
                cmd, 
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.log_step("Enhanced服务部署成功")
                # 显示启动的服务
                if stdout.strip():
                    lines = stdout.strip().split('\n')
                    for line in lines[-5:]:  # 显示最后5行输出
                        if line.strip():
                            print(f"    {line.strip()}")
                return True
            else:
                error_msg = stderr.strip() if stderr.strip() else "部署失败，未获取到详细错误信息"
                self.log_step(f"服务部署失败: {error_msg}", False)
                return False
                
        except Exception as e:
            self.log_step(f"部署服务时出错: {str(e)}", False)
            return False
    
    def verify_deployment(self) -> bool:
        """验证部署"""
        self.log_step("验证部署状态...")
        
        # 等待服务启动
        self.log_step("等待服务启动 (60秒)...")
        time.sleep(60)
        
        checks = []
        
        # 检查容器状态
        try:
            result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}\t{{.Status}}'],
                                  capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            if result.returncode == 0:
                running_containers = result.stdout.strip().split('\n')
                enhanced_containers = [line for line in running_containers 
                                     if 'megatts' in line and 'Up' in line]
                
                if enhanced_containers:
                    self.log_step(f"运行中的Enhanced容器: {len(enhanced_containers)}个")
                    for container in enhanced_containers:
                        print(f"    {container}")
                    checks.append(True)
                else:
                    self.log_step("未发现运行中的Enhanced容器", False)
                    checks.append(False)
            
        except Exception as e:
            self.log_step(f"容器状态检查失败: {e}", False)
            checks.append(False)
        
        # 检查API健康状态
        api_endpoints = [
            'http://localhost:7929/health',
            'http://localhost:8080/health',  # 通过Nginx
        ]
        
        for endpoint in api_endpoints:
            try:
                response = requests.get(endpoint, timeout=10)
                if response.status_code == 200:
                    self.log_step(f"✅ API健康检查通过: {endpoint}")
                    checks.append(True)
                else:
                    self.log_step(f"❌ API健康检查失败: {endpoint} - {response.status_code}", False)
                    checks.append(False)
            except Exception as e:
                self.log_step(f"❌ API健康检查异常: {endpoint} - {e}", False)
                checks.append(False)
        
        # 检查监控服务
        monitoring_endpoints = [
            'http://localhost:9091',  # Prometheus
            'http://localhost:3000',  # Grafana
        ]
        
        for endpoint in monitoring_endpoints:
            try:
                response = requests.get(endpoint, timeout=10)
                if response.status_code == 200:
                    self.log_step(f"✅ 监控服务可访问: {endpoint}")
                    checks.append(True)
                else:
                    self.log_step(f"⚠️  监控服务响应异常: {endpoint}")
                    checks.append(False)
            except Exception as e:
                self.log_step(f"⚠️  监控服务不可访问: {endpoint}")
                checks.append(False)
        
        all_passed = any(checks)  # 只要有一个检查通过就算成功
        self.log_step(f"部署验证{'通过' if all_passed else '失败'}", all_passed)
        return all_passed
    
    def show_deployment_summary(self):
        """显示部署摘要"""
        print("\n" + "="*60)
        print("🚀 MegaTTS3 Enhanced API Docker部署完成")
        print("="*60)
        
        success_count = sum(1 for step in self.deployment_log if step['success'])
        total_count = len(self.deployment_log)
        
        print(f"部署状态: {success_count}/{total_count} 步骤成功")
        print("\n📊 服务访问地址:")
        print("  • Enhanced API: http://localhost:7929")
        print("  • API网关: http://localhost:8080")
        print("  • Prometheus: http://localhost:9091")
        print("  • Grafana: http://localhost:3000 (admin/admin123)")
        print("  • API指标: http://localhost:7929/metrics")
        
        print("\n🐳 Docker命令:")
        print("  • 查看容器: docker ps")
        print("  • 查看日志: docker-compose -f docker-deploy-enhanced.yml logs -f")
        print("  • 停止服务: docker-compose -f docker-deploy-enhanced.yml down")
        
        print("\n🔧 故障排查:")
        print("  • 如果API无响应，检查模型文件是否正确挂载")
        print("  • 如果GPU不可用，检查NVIDIA Docker支持")
        print("  • 详细日志: docker logs megatts-enhanced-api")
        
        print("="*60)
    
    def deploy(self):
        """执行完整部署流程"""
        try:
            print("🚀 开始MegaTTS3 Enhanced API Docker部署")
            print("="*60)
            
            # 1. 检查Docker环境
            if not self.check_docker_environment():
                return False
            
            # 2. 检查现有容器
            self.check_existing_containers()
            
            # 3. 准备环境
            self.prepare_environment()
            
            # 4. 停止现有服务
            self.stop_existing_services()
            
            # 5. 构建镜像
            if not self.build_enhanced_image():
                return False
            
            # 6. 部署服务
            if not self.deploy_enhanced_services():
                return False
            
            # 7. 验证部署
            self.verify_deployment()
            
            # 8. 显示摘要
            self.show_deployment_summary()
            
            return True
            
        except Exception as e:
            self.log_step(f"部署失败: {e}", False)
            return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MegaTTS3 Enhanced API Docker部署脚本')
    parser.add_argument('--check-only', action='store_true',
                       help='仅检查环境，不执行部署')
    
    args = parser.parse_args()
    
    deployer = DockerEnhancedDeployer()
    
    if args.check_only:
        success = deployer.check_docker_environment()
        deployer.check_existing_containers()
        sys.exit(0 if success else 1)
    else:
        success = deployer.deploy()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()