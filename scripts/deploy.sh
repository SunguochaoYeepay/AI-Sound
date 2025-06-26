#!/bin/bash
# AI-Sound Docker部署脚本
# 支持Windows宿主机Ollama服务集成

set -e

echo "🚀 AI-Sound Docker部署开始..."

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

# 检查必要工具
check_requirements() {
    log_info "检查部署环境..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js未安装，请先安装Node.js 18+"
        exit 1
    fi
    
    # 检查npm
    if ! command -v npm &> /dev/null; then
        log_error "npm未安装，请先安装npm"
        exit 1
    fi
    
    log_success "环境检查通过"
}

# 检查Ollama服务
check_ollama() {
    log_info "检查Ollama服务..."
    
    # 检查Ollama是否运行
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        log_success "Ollama服务运行正常"
        
        # 检查模型
        if curl -s http://localhost:11434/api/tags | grep -q "gemma3:27b"; then
            log_success "Gemma3:27b模型已安装"
        else
            log_warning "Gemma3:27b模型未安装，请运行: ollama pull gemma3:27b"
        fi
    else
        log_warning "Ollama服务未运行，请确保Ollama在Windows上正常启动"
        log_info "启动命令: ollama serve"
    fi
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."
    
    mkdir -p data/{audio,database,logs,uploads,voice_profiles,cache,config,backups,temp,tts}
    mkdir -p data/logs/nginx
    mkdir -p nginx-dist
    
    log_success "目录创建完成"
}

# 构建前端
build_frontend() {
    log_info "构建前端应用..."
    
    cd platform/frontend
    
    # 安装依赖
    log_info "安装前端依赖..."
    npm install
    
    # 构建生产版本
    log_info "构建生产版本..."
    npm run build
    
    # 复制构建产物
    log_info "复制构建产物..."
    cp -r dist/* ../../nginx-dist/
    
    cd ../..
    
    log_success "前端构建完成"
}

# 构建Docker镜像
build_images() {
    log_info "构建Docker镜像..."
    
    # 构建后端镜像
    log_info "构建后端镜像..."
    docker build -t ai-sound-backend:latest -f docker/backend/Dockerfile .
    
    log_success "Docker镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动Docker服务..."
    
    # 停止现有服务
    docker-compose down
    
    # 启动服务
    docker-compose up -d
    
    log_success "Docker服务启动完成"
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务启动..."
    
    # 等待数据库
    log_info "等待数据库启动..."
    timeout=60
    while ! docker-compose exec -T database pg_isready -U ai_sound_user -d ai_sound > /dev/null 2>&1; do
        sleep 2
        timeout=$((timeout - 2))
        if [ $timeout -le 0 ]; then
            log_error "数据库启动超时"
            exit 1
        fi
    done
    log_success "数据库启动完成"
    
    # 等待后端
    log_info "等待后端服务启动..."
    timeout=60
    while ! curl -s http://localhost:3001/api/health > /dev/null 2>&1; do
        sleep 2
        timeout=$((timeout - 2))
        if [ $timeout -le 0 ]; then
            log_error "后端服务启动超时"
            exit 1
        fi
    done
    log_success "后端服务启动完成"
    
    # 等待前端
    log_info "等待前端服务启动..."
    timeout=30
    while ! curl -s http://localhost:3001 > /dev/null 2>&1; do
        sleep 2
        timeout=$((timeout - 2))
        if [ $timeout -le 0 ]; then
            log_error "前端服务启动超时"
            exit 1
        fi
    done
    log_success "前端服务启动完成"
}

# 显示部署信息
show_deployment_info() {
    log_success "🎉 AI-Sound部署完成！"
    echo ""
    echo "📋 服务信息:"
    echo "  🌐 前端界面: http://localhost:3001"
    echo "  🔧 API文档:  http://localhost:3001/docs"
    echo "  📊 健康检查: http://localhost:3001/api/health"
    echo ""
    echo "🐳 Docker服务状态:"
    docker-compose ps
    echo ""
    echo "📝 日志查看:"
    echo "  docker-compose logs -f backend"
    echo "  docker-compose logs -f nginx"
    echo ""
    echo "🔧 管理命令:"
    echo "  停止服务: docker-compose down"
    echo "  重启服务: docker-compose restart"
    echo "  查看状态: docker-compose ps"
    echo ""
    
    # 检查Ollama连接
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        log_success "✅ Ollama服务连接正常"
    else
        log_warning "⚠️  Ollama服务连接失败，请检查Windows上的Ollama服务"
    fi
}

# 主函数
main() {
    echo "🚀 AI-Sound Docker部署脚本"
    echo "支持Windows宿主机Ollama服务集成"
    echo ""
    
    # 检查参数
    SKIP_BUILD=false
    SKIP_FRONTEND=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --skip-frontend)
                SKIP_FRONTEND=true
                shift
                ;;
            -h|--help)
                echo "用法: $0 [选项]"
                echo "选项:"
                echo "  --skip-build     跳过Docker镜像构建"
                echo "  --skip-frontend  跳过前端构建"
                echo "  -h, --help       显示帮助信息"
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                exit 1
                ;;
        esac
    done
    
    # 执行部署步骤
    check_requirements
    check_ollama
    create_directories
    
    if [ "$SKIP_FRONTEND" = false ]; then
        build_frontend
    else
        log_warning "跳过前端构建"
    fi
    
    if [ "$SKIP_BUILD" = false ]; then
        build_images
    else
        log_warning "跳过Docker镜像构建"
    fi
    
    start_services
    wait_for_services
    show_deployment_info
}

# 错误处理
trap 'log_error "部署过程中发生错误，退出码: $?"' ERR

# 执行主函数
main "$@" 