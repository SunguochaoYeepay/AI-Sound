#!/usr/bin/env python3
"""
MegaTTS3 Enhanced API - 现有容器增强部署脚本
利用现有的megatts3-service容器，添加Enhanced API功能
"""

import os
import sys
import subprocess
import time
import json
import requests
from pathlib import Path
from datetime import datetime

class ExistingContainerEnhancer:
    """现有容器增强器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.deployment_log = []
        self.existing_container = "megatts3-service"
        
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
    
    def check_existing_container(self) -> bool:
        """检查现有容器"""
        self.log_step("检查现有MegaTTS3容器...")
        
        try:
            result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}\t{{.Status}}'],
                                  capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            if result.returncode == 0:
                containers = result.stdout.strip().split('\n')
                for container_line in containers:
                    if self.existing_container in container_line and 'Up' in container_line:
                        self.log_step(f"发现运行中的容器: {self.existing_container}")
                        return True
                
                self.log_step(f"容器 {self.existing_container} 未运行", False)
                return False
            
        except Exception as e:
            self.log_step(f"容器检查失败: {e}", False)
            return False
    
    def inspect_existing_container(self):
        """检查现有容器内部结构"""
        self.log_step("分析现有容器内部结构...")
        
        try:
            # 检查工作目录
            result = subprocess.run(['docker', 'exec', self.existing_container, 'pwd'],
                                  capture_output=True, text=True, encoding='utf-8', errors='replace')
            if result.returncode == 0:
                workdir = result.stdout.strip()
                self.log_step(f"容器工作目录: {workdir}")
            
            # 检查MegaTTS3目录
            result = subprocess.run(['docker', 'exec', self.existing_container, 'ls', '-la', '/workspace/'],
                                  capture_output=True, text=True, encoding='utf-8', errors='replace')
            if result.returncode == 0:
                self.log_step("容器/workspace目录内容:")
                for line in result.stdout.strip().split('\n')[:10]:  # 显示前10行
                    print(f"    {line}")
            
            # 检查Python环境
            result = subprocess.run(['docker', 'exec', self.existing_container, 'python', '--version'],
                                  capture_output=True, text=True, encoding='utf-8', errors='replace')
            if result.returncode == 0:
                self.log_step(f"Python版本: {result.stdout.strip()}")
            
            # 检查GPU可用性
            result = subprocess.run(['docker', 'exec', self.existing_container, 'nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
                                  capture_output=True, text=True, encoding='utf-8', errors='replace')
            if result.returncode == 0:
                gpu_info = result.stdout.strip()
                if gpu_info:
                    self.log_step(f"GPU信息: {gpu_info}")
                else:
                    self.log_step("未检测到GPU或nvidia-smi不可用")
            
        except Exception as e:
            self.log_step(f"容器检查异常: {e}", False)
    
    def copy_enhanced_api_to_container(self):
        """将Enhanced API代码复制到现有容器"""
        self.log_step("复制Enhanced API代码到容器...")
        
        try:
            # 创建目标目录
            subprocess.run(['docker', 'exec', self.existing_container, 'mkdir', '-p', '/workspace/enhanced_api'],
                         capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            # 复制核心文件
            files_to_copy = [
                'MegaTTS/MegaTTS3/api_server_v2.py',
                'MegaTTS/MegaTTS3/core/',
                'MegaTTS/MegaTTS3/api/',
                'MegaTTS/MegaTTS3/models/',
                'MegaTTS/MegaTTS3/requirements.txt'
            ]
            
            for file_path in files_to_copy:
                src_path = self.project_root / file_path
                if src_path.exists():
                    if src_path.is_file():
                        subprocess.run(['docker', 'cp', str(src_path), f'{self.existing_container}:/workspace/enhanced_api/'],
                                     capture_output=True, text=True, encoding='utf-8', errors='replace')
                        self.log_step(f"复制文件: {file_path}")
                    else:
                        # 复制目录
                        subprocess.run(['docker', 'cp', str(src_path), f'{self.existing_container}:/workspace/enhanced_api/'],
                                     capture_output=True, text=True, encoding='utf-8', errors='replace')
                        self.log_step(f"复制目录: {file_path}")
                else:
                    self.log_step(f"文件不存在: {file_path}", False)
            
            return True
            
        except Exception as e:
            self.log_step(f"复制文件失败: {e}", False)
            return False
    
    def install_enhanced_dependencies(self):
        """在现有容器中安装Enhanced API依赖"""
        self.log_step("安装Enhanced API依赖...")
        
        try:
            # 安装Python依赖
            cmd = ['docker', 'exec', self.existing_container, 'pip', 'install', 
                   'fastapi', 'uvicorn', 'pydantic', 'prometheus-client', 'psutil']
            
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            if result.returncode == 0:
                self.log_step("Enhanced API依赖安装成功")
                return True
            else:
                self.log_step(f"依赖安装失败: {result.stderr}", False)
                return False
                
        except Exception as e:
            self.log_step(f"安装依赖异常: {e}", False)
            return False
    
    def create_startup_script(self):
        """创建Enhanced API启动脚本"""
        self.log_step("创建Enhanced API启动脚本...")
        
        startup_script = '''#!/bin/bash
# MegaTTS3 Enhanced API 启动脚本

cd /workspace/enhanced_api

echo "🚀 启动MegaTTS3 Enhanced API..."
echo "工作目录: $(pwd)"
echo "Python版本: $(python --version)"

# 检查模型文件
if [ -d "/workspace/MegaTTS3" ]; then
    echo "✅ 发现MegaTTS3模型目录"
    ln -sf /workspace/MegaTTS3 /workspace/enhanced_api/MegaTTS3
else
    echo "⚠️  未找到MegaTTS3模型目录"
fi

# 创建必要目录
mkdir -p storage/voices storage/temp storage/logs

# 设置环境变量
export PYTHONPATH=/workspace/enhanced_api:/workspace:$PYTHONPATH
export API_HOST=0.0.0.0
export API_PORT=7929
export LOG_LEVEL=info
export ENABLE_METRICS=true

# 启动Enhanced API
echo "🎉 启动Enhanced API服务..."
python api_server_v2.py --host 0.0.0.0 --port 7929
'''
        
        try:
            # 写入启动脚本到临时文件
            script_path = self.project_root / 'start_enhanced_api.sh'
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(startup_script)
            
            # 复制到容器并设置权限
            subprocess.run(['docker', 'cp', str(script_path), f'{self.existing_container}:/workspace/start_enhanced_api.sh'],
                         capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            subprocess.run(['docker', 'exec', self.existing_container, 'chmod', '+x', '/workspace/start_enhanced_api.sh'],
                         capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            # 清理临时文件
            script_path.unlink()
            
            self.log_step("启动脚本创建成功")
            return True
            
        except Exception as e:
            self.log_step(f"创建启动脚本失败: {e}", False)
            return False
    
    def start_enhanced_api_in_container(self):
        """在现有容器中启动Enhanced API"""
        self.log_step("在现有容器中启动Enhanced API...")
        
        try:
            # 在后台启动Enhanced API
            cmd = ['docker', 'exec', '-d', self.existing_container, '/workspace/start_enhanced_api.sh']
            
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            if result.returncode == 0:
                self.log_step("Enhanced API启动命令已执行")
                return True
            else:
                self.log_step(f"启动失败: {result.stderr}", False)
                return False
                
        except Exception as e:
            self.log_step(f"启动异常: {e}", False)
            return False
    
    def deploy_monitoring_services(self):
        """部署轻量级监控服务"""
        self.log_step("部署监控服务...")
        
        monitoring_compose = '''version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: megatts-prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=7d'
    volumes:
      - ./monitoring/prometheus-simple.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    ports:
      - "9091:9090"
    restart: unless-stopped
    networks:
      - default

  grafana:
    image: grafana/grafana:latest
    container_name: megatts-grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    ports:
      - "3000:3000"
    restart: unless-stopped
    networks:
      - default

volumes:
  prometheus-data:

networks:
  default:
    external: true
    name: bridge
'''
        
        try:
            # 创建简化的监控配置
            monitoring_dir = self.project_root / 'monitoring'
            monitoring_dir.mkdir(exist_ok=True)
            
            # 创建Prometheus配置
            prometheus_config = '''global:
  scrape_interval: 30s

scrape_configs:
  - job_name: 'megatts-enhanced'
    scrape_interval: 15s
    static_configs:
      - targets: ['host.docker.internal:7929']
    metrics_path: '/metrics'
'''
            
            with open(monitoring_dir / 'prometheus-simple.yml', 'w', encoding='utf-8') as f:
                f.write(prometheus_config)
            
            # 创建Docker Compose文件
            with open(self.project_root / 'monitoring-compose.yml', 'w', encoding='utf-8') as f:
                f.write(monitoring_compose)
            
            # 启动监控服务
            cmd = ['docker-compose', '-f', 'monitoring-compose.yml', 'up', '-d']
            result = subprocess.run(cmd, cwd=self.project_root,
                                  capture_output=True, text=True, encoding='utf-8', errors='replace')
            
            if result.returncode == 0:
                self.log_step("监控服务部署成功")
                return True
            else:
                self.log_step(f"监控服务部署失败: {result.stderr}", False)
                return False
                
        except Exception as e:
            self.log_step(f"部署监控服务异常: {e}", False)
            return False
    
    def verify_enhanced_api(self):
        """验证Enhanced API"""
        self.log_step("验证Enhanced API...")
        
        # 等待API启动
        self.log_step("等待API启动 (30秒)...")
        time.sleep(30)
        
        # 检查API健康状态
        try:
            response = requests.get('http://localhost:7929/health', timeout=10)
            if response.status_code == 200:
                self.log_step("✅ Enhanced API健康检查通过")
                return True
            else:
                self.log_step(f"❌ API健康检查失败: {response.status_code}", False)
                return False
        except Exception as e:
            self.log_step(f"❌ API健康检查异常: {e}", False)
            return False
    
    def show_deployment_summary(self):
        """显示部署摘要"""
        print("\n" + "="*60)
        print("🚀 MegaTTS3 Enhanced API 现有容器增强完成")
        print("="*60)
        
        print(f"基础容器: {self.existing_container}")
        print("\n📊 服务访问地址:")
        print("  • Enhanced API: http://localhost:7929")
        print("  • API健康检查: http://localhost:7929/health")
        print("  • API文档: http://localhost:7929/docs")
        print("  • API指标: http://localhost:7929/metrics")
        print("  • Prometheus: http://localhost:9091")
        print("  • Grafana: http://localhost:3000 (admin/admin123)")
        
        print("\n🔧 管理命令:")
        print(f"  • 查看Enhanced API日志: docker exec {self.existing_container} tail -f /workspace/enhanced_api/storage/logs/app*.log")
        print(f"  • 进入容器: docker exec -it {self.existing_container} /bin/bash")
        print(f"  • 重启Enhanced API: docker exec {self.existing_container} pkill -f api_server_v2 && docker exec -d {self.existing_container} /workspace/start_enhanced_api.sh")
        
        print("\n🎯 测试API:")
        print("  curl http://localhost:7929/health")
        print("  curl http://localhost:7929/info")
        print("  curl http://localhost:7929/metrics")
        
        print("="*60)
    
    def enhance_existing_container(self):
        """增强现有容器"""
        try:
            print("🚀 开始增强现有MegaTTS3容器")
            print("="*60)
            
            # 1. 检查现有容器
            if not self.check_existing_container():
                return False
            
            # 2. 分析容器内部结构
            self.inspect_existing_container()
            
            # 3. 复制Enhanced API代码
            if not self.copy_enhanced_api_to_container():
                return False
            
            # 4. 安装依赖
            if not self.install_enhanced_dependencies():
                return False
            
            # 5. 创建启动脚本
            if not self.create_startup_script():
                return False
            
            # 6. 启动Enhanced API
            if not self.start_enhanced_api_in_container():
                return False
            
            # 7. 部署监控服务
            self.deploy_monitoring_services()
            
            # 8. 验证API
            self.verify_enhanced_api()
            
            # 9. 显示摘要
            self.show_deployment_summary()
            
            return True
            
        except Exception as e:
            self.log_step(f"增强失败: {e}", False)
            return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MegaTTS3 现有容器增强脚本')
    parser.add_argument('--check-only', action='store_true',
                       help='仅检查现有容器状态')
    
    args = parser.parse_args()
    
    enhancer = ExistingContainerEnhancer()
    
    if args.check_only:
        success = enhancer.check_existing_container()
        if success:
            enhancer.inspect_existing_container()
        sys.exit(0 if success else 1)
    else:
        success = enhancer.enhance_existing_container()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()