#!/bin/bash

# AI-Sound Docker化部署脚本
# 渐进式Docker化部署工具

set -e

echo "🚀 AI-Sound Docker化部署开始..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查前置条件
check_prerequisites() {
    log_info "检查前置条件..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装"
        exit 1
    fi
    
    # 检查.env文件
    if [ ! -f ".env" ]; then
        log_warn ".env文件不存在，创建模板..."
        create_env_template
    fi
    
    log_info "前置条件检查完成"
}

# 创建环境变量模板
create_env_template() {
    cat > .env << 'EOF'
# AI-Sound Docker Environment Configuration
COMPOSE_PROJECT_NAME=ai-sound
NODE_ENV=production
DEBUG=false

# 服务端口配置
FRONTEND_PORT=3000
BACKEND_PORT=8000
NGINX_PORT=80
POSTGRES_PORT=5432

# 数据库配置
POSTGRES_DB=ai_sound
POSTGRES_USER=ai_sound_user
POSTGRES_PASSWORD=ai_sound_secure_password_2024

# MegaTTS3引擎配置
MEGATTS3_URL=http://megatts3:9000
MEGATTS3_PORT=9000

# 文件路径配置
AUDIO_DIR=/app/storage/audio
UPLOADS_DIR=/app/storage/uploads
VOICE_PROFILES_DIR=/app/storage/voice_profiles

# 安全配置
SECRET_KEY=your_super_secret_key_change_in_production
CORS_ORIGINS=http://localhost:3000,http://localhost
EOF
    
    log_info "已创建.env模板文件，请根据需要修改配置"
}

# 准备存储目录
prepare_storage() {
    log_info "准备存储目录..."
    
    # 创建storage子目录
    mkdir -p storage/{audio,uploads,voice_profiles,projects,database,logs,config,backups,redis}
    
    # 设置权限（Linux/Mac）
    if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "win32" ]]; then
        chmod -R 755 storage
    fi
    
    log_info "存储目录准备完成"
}

# 构建Docker镜像
build_images() {
    log_info "构建Docker镜像..."
    
    # 构建后端镜像
    log_info "构建后端镜像..."
    docker build -f docker/backend/Dockerfile -t ai-sound-backend .
    
    # 构建前端镜像
    log_info "构建前端镜像..."
    docker build -f docker/frontend/Dockerfile -t ai-sound-frontend .
    
    log_info "镜像构建完成"
}

# 启动基础服务
start_infrastructure() {
    log_info "启动基础设施服务..."
    
    # 启动数据库和Redis
    docker-compose -f docker/docker-compose.full.yml up -d database redis
    
    # 等待数据库启动
    log_info "等待数据库启动..."
    sleep 15
    
    log_info "基础设施启动完成"
}

# 启动应用服务
start_application() {
    log_info "启动应用服务..."
    
    # 启动后端服务
    docker-compose -f docker/docker-compose.full.yml up -d backend
    
    # 等待后端启动
    log_info "等待后端服务启动..."
    sleep 10
    
    # 启动前端服务
    docker-compose -f docker/docker-compose.full.yml up -d frontend
    
    # 启动Nginx网关
    docker-compose -f docker/docker-compose.full.yml up -d nginx
    
    log_info "应用服务启动完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 检查服务状态
    docker-compose -f docker/docker-compose.full.yml ps
    
    # 检查端口
    local services=("frontend:3000" "backend:8000" "nginx:80")
    
    for service in "${services[@]}"; do
        local name=${service%:*}
        local port=${service#*:}
        
        if nc -z localhost $port 2>/dev/null; then
            log_info "✅ $name 服务正常 (端口:$port)"
        else
            log_warn "⚠️  $name 服务可能未就绪 (端口:$port)"
        fi
    done
}

# 显示访问信息
show_access_info() {
    echo ""
    echo "🎉 AI-Sound Docker部署完成！"
    echo ""
    echo "访问地址："
    echo "  - 前端界面: http://localhost:3000"
    echo "  - 后端API: http://localhost:8000"
    echo "  - API文档: http://localhost:8000/docs"
    echo "  - Nginx网关: http://localhost"
    echo ""
    echo "管理命令："
    echo "  - 查看日志: docker-compose -f docker/docker-compose.full.yml logs -f"
    echo "  - 停止服务: docker-compose -f docker/docker-compose.full.yml down"
    echo "  - 重启服务: docker-compose -f docker/docker-compose.full.yml restart"
    echo ""
}

# 主函数
main() {
    case "${1:-full}" in
        "check")
            check_prerequisites
            ;;
        "build")
            check_prerequisites
            build_images
            ;;
        "infra")
            check_prerequisites
            prepare_storage
            start_infrastructure
            ;;
        "app")
            start_application
            health_check
            show_access_info
            ;;
        "full")
            check_prerequisites
            prepare_storage
            build_images
            start_infrastructure
            start_application
            health_check
            show_access_info
            ;;
        *)
            echo "用法: $0 [check|build|infra|app|full]"
            echo "  check - 检查前置条件"
            echo "  build - 构建Docker镜像"
            echo "  infra - 启动基础设施"
            echo "  app   - 启动应用服务"
            echo "  full  - 完整部署（默认）"
            exit 1
            ;;
    esac
}

main "$@" 