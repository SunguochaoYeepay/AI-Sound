#!/bin/bash
# AI-Sound 自动化部署脚本
# 用途：一键部署生产环境

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查必要的命令
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装Docker Compose"
        exit 1
    fi
    
    # 检查Node.js (用于前端构建)
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装，请先安装Node.js 18+"
        exit 1
    fi
    
    log_success "系统要求检查通过"
}

# 创建必要的目录
create_directories() {
    log_info "创建数据目录..."
    
    mkdir -p data/{audio,database,logs/{nginx,backend},uploads,voice_profiles,cache,config,backups,temp}
    mkdir -p nginx-dist
    
    log_success "目录创建完成"
}

# 构建前端
build_frontend() {
    log_info "构建前端应用..."
    
    cd platform/frontend
    
    # 安装依赖
    if [ ! -d "node_modules" ]; then
        log_info "安装前端依赖..."
        npm install
    fi
    
    # 构建应用
    log_info "构建前端资源..."
    npm run build
    
    # 复制构建结果
    log_info "复制构建结果..."
    cp -r dist/* ../../nginx-dist/
    
    cd ../..
    log_success "前端构建完成"
}

# 启动服务
start_services() {
    log_info "启动Docker服务..."
    
    # 使用标准docker-compose配置
    if [ -f "docker-compose.yml" ]; then
        docker-compose down 2>/dev/null || true
        docker-compose up -d
    elif [ -f "docker/docker-compose.yml" ]; then
        cd docker
        docker-compose down 2>/dev/null || true
        docker-compose up -d
        cd ..
    else
        log_error "找不到docker-compose配置文件"
        exit 1
    fi
    
    log_success "服务启动完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 等待服务启动
    sleep 30
    
    # 检查容器状态
    log_info "检查容器状态..."
    docker-compose ps
    
    # 检查API健康状态
    log_info "检查API服务..."
    max_attempts=10
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:3001/health >/dev/null 2>&1; then
            log_success "API服务健康检查通过"
            break
        else
            log_warning "API服务尚未就绪，等待中... ($attempt/$max_attempts)"
            sleep 10
            ((attempt++))
        fi
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_error "API服务健康检查失败"
        return 1
    fi
    
    log_success "所有服务运行正常"
}

# 显示访问信息
show_access_info() {
    log_info "部署完成！访问信息："
    echo ""
    echo "🌐 前端界面:    http://localhost:3001"
    echo "📡 API接口:     http://localhost:3001/api"
    echo "📚 API文档:     http://localhost:3001/docs"
    echo "💊 健康检查:    http://localhost:3001/health"
    echo ""
    echo "📋 管理命令:"
    echo "  查看日志:     docker-compose logs -f"
    echo "  重启服务:     docker-compose restart"
    echo "  停止服务:     docker-compose down"
    echo ""
}

# 主函数
main() {
    echo "=================================="
    echo "🎵 AI-Sound 自动化部署脚本"
    echo "=================================="
    echo ""
    
    check_requirements
    create_directories
    build_frontend
    start_services
    
    if health_check; then
        show_access_info
        log_success "部署成功完成！"
        exit 0
    else
        log_error "部署失败，请检查日志"
        docker-compose logs --tail=50
        exit 1
    fi
}

# 处理命令行参数
case "${1:-}" in
    "dev")
        log_info "使用开发模式部署..."
        if [ -f "docker-compose.full.yml" ]; then
            export COMPOSE_FILE=docker-compose.full.yml
        elif [ -f "docker/docker-compose.full.yml" ]; then
            export COMPOSE_FILE=docker/docker-compose.full.yml
        fi
        ;;
    "clean")
        log_info "清理现有部署..."
        docker-compose down -v 2>/dev/null || true
        docker system prune -f
        log_success "清理完成"
        exit 0
        ;;
    "help"|"-h"|"--help")
        echo "用法: $0 [选项]"
        echo "选项:"
        echo "  (无参数)  生产模式部署"
        echo "  dev       开发模式部署"
        echo "  clean     清理现有部署"
        echo "  help      显示帮助信息"
        exit 0
        ;;
esac

# 执行主函数
main 