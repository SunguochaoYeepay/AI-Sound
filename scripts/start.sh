#!/bin/bash

# AI-Sound Platform 一键启动脚本
# 作者: AI-Sound Team
# 版本: 1.0.0

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查必要的命令
check_requirements() {
    log_step "检查系统要求..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    # 检查Docker是否运行
    if ! docker info &> /dev/null; then
        log_error "Docker 服务未运行，请启动 Docker 服务"
        exit 1
    fi
    
    log_info "系统要求检查完成 ✓"
}

# 检查端口占用
check_ports() {
    log_step "检查端口占用..."
    
    ports=(80 443 8000 5432 6379)
    occupied_ports=()
    
    for port in "${ports[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            occupied_ports+=($port)
        fi
    done
    
    if [ ${#occupied_ports[@]} -gt 0 ]; then
        log_warn "以下端口被占用: ${occupied_ports[*]}"
        log_warn "可能会影响服务启动，建议先释放这些端口"
        read -p "是否继续？(y/N): " continue_choice
        if [[ ! $continue_choice =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log_info "端口检查完成 ✓"
    fi
}

# 创建必要的目录
create_directories() {
    log_step "创建数据目录..."
    
    directories=(
        "data/audio"
        "data/database"
        "data/logs/nginx"
        "data/logs/backend"
        "data/logs/frontend"
        "data/uploads"
        "data/voice_profiles"
        "data/cache"
        "data/config"
        "data/backups"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        log_info "创建目录: $dir"
    done
    
    # 设置权限
    chmod -R 755 data/
    log_info "目录创建完成 ✓"
}

# 配置环境变量
setup_environment() {
    log_step "配置环境变量..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_info "已创建 .env 文件，请根据需要修改配置"
        else
            log_warn "未找到 .env.example 文件，使用默认配置"
            cat > .env << EOF
# AI-Sound Platform 基本配置
COMPOSE_PROJECT_NAME=ai-sound
NODE_ENV=production
DEBUG=false

# 数据库配置
DATABASE_TYPE=postgres
POSTGRES_DB=ai_sound
POSTGRES_USER=ai_sound_user
POSTGRES_PASSWORD=ai_sound_password_$(date +%s)

# MegaTTS3配置
MEGATTS3_URL=http://host.docker.internal:9000

# 安全配置
SECRET_KEY=secret_key_$(openssl rand -hex 32)
CORS_ORIGINS=http://localhost,https://localhost

# 端口配置
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443
BACKEND_PORT=8000
REDIS_PORT=6379
EOF
        fi
    else
        log_info "环境变量文件已存在"
    fi
    
    log_info "环境变量配置完成 ✓"
}

# 拉取和构建镜像
build_images() {
    log_step "构建Docker镜像..."
    
    # 拉取基础镜像
    log_info "拉取基础镜像..."
    docker-compose pull postgres redis nginx || true
    
    # 构建应用镜像
    log_info "构建前端镜像..."
    docker-compose build frontend
    
    log_info "构建后端镜像..."
    docker-compose build backend
    
    log_info "镜像构建完成 ✓"
}

# 启动服务
start_services() {
    log_step "启动服务..."
    
    # 先启动数据库和缓存
    log_info "启动数据库和缓存服务..."
    docker-compose up -d database redis
    
    # 等待数据库启动
    log_info "等待数据库启动..."
    sleep 10
    
    # 检查数据库连接
    max_attempts=30
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose exec -T database pg_isready -U ai_sound_user -d ai_sound &> /dev/null; then
            log_info "数据库连接成功 ✓"
            break
        fi
        
        attempt=$((attempt + 1))
        log_info "等待数据库连接... ($attempt/$max_attempts)"
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_error "数据库连接超时"
        exit 1
    fi
    
    # 启动后端服务
    log_info "启动后端服务..."
    docker-compose up -d backend
    
    # 等待后端启动
    log_info "等待后端服务启动..."
    sleep 15
    
    # 启动前端和代理
    log_info "启动前端和代理服务..."
    docker-compose up -d frontend nginx
    
    log_info "所有服务启动完成 ✓"
}

# 检查服务状态
check_services() {
    log_step "检查服务状态..."
    
    # 等待服务完全启动
    sleep 10
    
    # 检查容器状态
    log_info "检查容器状态..."
    docker-compose ps
    
    # 检查健康状态
    log_info "检查服务健康状态..."
    
    # 检查前端
    if curl -f http://localhost/health &> /dev/null; then
        log_info "前端服务: 健康 ✓"
    else
        log_warn "前端服务: 异常 ✗"
    fi
    
    # 检查后端
    if curl -f http://localhost/api/health &> /dev/null; then
        log_info "后端服务: 健康 ✓"
    else
        log_warn "后端服务: 异常 ✗"
    fi
    
    log_info "服务状态检查完成"
}

# 显示访问信息
show_access_info() {
    log_step "部署完成！"
    
    echo
    echo "🎉 AI-Sound Platform 部署成功！"
    echo
    echo "📱 访问地址:"
    echo "  前端界面: http://localhost"
    echo "  API文档:  http://localhost/docs"
    echo "  健康检查: http://localhost/health"
    echo
    echo "🔧 管理命令:"
    echo "  查看状态: docker-compose ps"
    echo "  查看日志: docker-compose logs -f"
    echo "  停止服务: docker-compose down"
    echo "  重启服务: docker-compose restart"
    echo
    echo "📚 文档:"
    echo "  部署文档: docs/deployment.md"
    echo "  API文档:  docs/api.md"
    echo "  故障排查: docs/troubleshooting.md"
    echo
    echo "⚠️  注意事项:"
    echo "  - 请确保MegaTTS3引擎运行在端口9000"
    echo "  - 生产环境请修改默认密码"
    echo "  - 建议配置SSL证书"
    echo
}

# 错误处理
handle_error() {
    log_error "启动过程中发生错误"
    log_info "尝试查看日志以诊断问题:"
    echo "  docker-compose logs --tail=50"
    echo "  docker-compose ps"
    exit 1
}

# 主函数
main() {
    echo "🚀 AI-Sound Platform 一键部署脚本"
    echo "=================================="
    echo
    
    # 设置错误处理
    trap 'handle_error' ERR
    
    # 执行部署步骤
    check_requirements
    check_ports
    create_directories
    setup_environment
    build_images
    start_services
    check_services
    show_access_info
}

# 处理命令行参数
case "${1:-}" in
    --skip-checks)
        log_info "跳过端口检查"
        check_requirements() { log_info "跳过系统检查"; }
        check_ports() { log_info "跳过端口检查"; }
        ;;
    --rebuild)
        log_info "强制重新构建镜像"
        build_images() {
            log_step "强制重新构建Docker镜像..."
            docker-compose build --no-cache frontend backend
            log_info "镜像重新构建完成 ✓"
        }
        ;;
    --help|-h)
        echo "用法: $0 [选项]"
        echo
        echo "选项:"
        echo "  --skip-checks  跳过系统和端口检查"
        echo "  --rebuild      强制重新构建镜像"
        echo "  --help, -h     显示此帮助信息"
        exit 0
        ;;
esac

# 运行主函数
main "$@" 