#!/bin/bash

# MegaTTS3 健康检查脚本
# 版本: 1.0.0
# 作者: AI-Sound Team

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# 配置
MEGATTS3_URL="http://localhost:9000"
CONTAINER_NAME="ai-sound-megatts3"
MAX_GPU_MEMORY=80  # GPU内存使用率警告阈值
MAX_DISK_USAGE=80  # 磁盘使用率警告阈值

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

log_title() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# 检查MegaTTS3服务状态
check_service_status() {
    log_title "MegaTTS3 服务状态检查"
    
    # 检查容器状态
    if docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}" | grep -q "$CONTAINER_NAME"; then
        log_info "✅ MegaTTS3容器正在运行"
        
        # 获取容器运行时间
        uptime=$(docker ps --filter "name=$CONTAINER_NAME" --format "{{.Status}}")
        echo "   运行状态: $uptime"
    else
        log_error "❌ MegaTTS3容器未运行"
        echo "   尝试启动容器..."
        docker-compose -f docker-compose.megatts3.yml up -d
        return 1
    fi
    
    # 检查HTTP健康状态
    echo "   正在检查HTTP健康状态..."
    if curl -s -f "$MEGATTS3_URL/health" > /dev/null; then
        log_info "✅ MegaTTS3 HTTP服务响应正常"
        
        # 获取服务详细信息
        health_info=$(curl -s "$MEGATTS3_URL/health" | jq -r '.')
        echo "   健康状态详情:"
        echo "$health_info" | jq '.'
    else
        log_error "❌ MegaTTS3 HTTP服务无响应"
        return 1
    fi
}

# 检查GPU状态
check_gpu_status() {
    log_title "GPU 状态检查"
    
    if command -v nvidia-smi &> /dev/null; then
        # 检查GPU可用性
        if nvidia-smi > /dev/null 2>&1; then
            log_info "✅ NVIDIA GPU驱动正常"
            
            # 获取GPU使用情况
            gpu_info=$(nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu --format=csv,noheader,nounits)
            echo "   GPU详细信息:"
            echo "   索引 | 型号 | 内存使用/总计 | GPU使用率 | 温度"
            echo "   ----|------|-------------|---------|------"
            
            while IFS=',' read -r index name mem_used mem_total util temp; do
                # 清理空格
                index=$(echo "$index" | xargs)
                name=$(echo "$name" | xargs)
                mem_used=$(echo "$mem_used" | xargs)
                mem_total=$(echo "$mem_total" | xargs)
                util=$(echo "$util" | xargs)
                temp=$(echo "$temp" | xargs)
                
                # 计算内存使用率
                mem_percent=$((mem_used * 100 / mem_total))
                
                # 状态指示
                if [ "$mem_percent" -gt "$MAX_GPU_MEMORY" ]; then
                    status="⚠️ "
                    log_warn "GPU $index 内存使用率过高: ${mem_percent}%"
                else
                    status="✅ "
                fi
                
                echo "   $status GPU$index | $name | ${mem_used}MB/${mem_total}MB (${mem_percent}%) | ${util}% | ${temp}°C"
                
            done <<< "$gpu_info"
            
            # 检查容器内GPU访问
            echo "   检查容器内GPU访问..."
            if docker exec "$CONTAINER_NAME" nvidia-smi > /dev/null 2>&1; then
                log_info "✅ 容器可以访问GPU"
            else
                log_error "❌ 容器无法访问GPU"
            fi
            
        else
            log_error "❌ GPU驱动异常或无可用GPU"
        fi
    else
        log_warn "⚠️  未安装nvidia-smi工具"
    fi
}

# 检查系统资源
check_system_resources() {
    log_title "系统资源检查"
    
    # 检查内存使用
    echo "   系统内存使用情况:"
    free -h | grep -E "Mem|Swap"
    
    # 检查容器资源使用
    echo "   MegaTTS3容器资源使用:"
    docker stats "$CONTAINER_NAME" --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"
    
    # 检查磁盘空间
    echo "   磁盘空间使用情况:"
    df -h | grep -E "Filesystem|/$|/app"
    
    # 检查MegaTTS3相关目录空间
    if [ -d "MegaTTS/MegaTTS3" ]; then
        echo "   MegaTTS3数据目录使用情况:"
        du -sh MegaTTS/MegaTTS3/* 2>/dev/null | sort -hr
        
        # 检查模型文件
        if [ -d "MegaTTS/MegaTTS3/checkpoints" ]; then
            model_size=$(du -sh MegaTTS/MegaTTS3/checkpoints | cut -f1)
            echo "   模型文件总大小: $model_size"
        fi
        
        # 检查缓存大小
        if [ -d "MegaTTS/MegaTTS3/storage/cache" ]; then
            cache_size=$(du -sh MegaTTS/MegaTTS3/storage/cache | cut -f1)
            echo "   缓存文件大小: $cache_size"
        fi
    fi
}

# 检查网络连接
check_network() {
    log_title "网络连接检查"
    
    # 检查端口监听
    echo "   检查MegaTTS3端口监听..."
    if netstat -tuln 2>/dev/null | grep -q ":9000 "; then
        log_info "✅ 端口9000正在监听"
    else
        log_warn "⚠️  端口9000未监听"
    fi
    
    # 检查容器网络
    echo "   检查容器网络配置..."
    network_info=$(docker inspect "$CONTAINER_NAME" | jq -r '.[0].NetworkSettings.Networks')
    echo "   网络配置: $(echo "$network_info" | jq 'keys[]')"
    
    # 检查API响应时间
    echo "   测试API响应时间..."
    start_time=$(date +%s%N)
    if curl -s -f "$MEGATTS3_URL/health" > /dev/null; then
        end_time=$(date +%s%N)
        response_time=$(( (end_time - start_time) / 1000000 ))
        
        if [ "$response_time" -lt 1000 ]; then
            log_info "✅ API响应时间: ${response_time}ms (优秀)"
        elif [ "$response_time" -lt 3000 ]; then
            log_warn "⚠️  API响应时间: ${response_time}ms (一般)"
        else
            log_error "❌ API响应时间: ${response_time}ms (过慢)"
        fi
    else
        log_error "❌ API响应失败"
    fi
}

# 检查模型状态
check_model_status() {
    log_title "模型状态检查"
    
    # 检查模型文件
    echo "   检查模型文件完整性..."
    if [ -d "MegaTTS/MegaTTS3/checkpoints" ]; then
        find MegaTTS/MegaTTS3/checkpoints -name "*.pt" -o -name "*.pth" | while read -r model_file; do
            if [ -f "$model_file" ]; then
                size=$(du -h "$model_file" | cut -f1)
                echo "   ✅ $(basename "$model_file"): $size"
            fi
        done
        
        # 检查配置文件
        find MegaTTS/MegaTTS3/checkpoints -name "*.yaml" -o -name "*.yml" | while read -r config_file; do
            if [ -f "$config_file" ]; then
                echo "   ✅ 配置文件: $(basename "$config_file")"
            fi
        done
    else
        log_warn "⚠️  未找到模型目录"
    fi
    
    # 通过API检查模型加载状态
    echo "   检查模型加载状态..."
    if curl -s -f "$MEGATTS3_URL/api/v1/info" > /dev/null; then
        model_info=$(curl -s "$MEGATTS3_URL/api/v1/info")
        echo "   模型信息:"
        echo "$model_info" | jq '.'
    else
        log_warn "⚠️  无法获取模型信息"
    fi
}

# 性能测试
performance_test() {
    log_title "性能测试"
    
    echo "   执行简单的语音合成测试..."
    test_text="Hello, this is a performance test."
    
    start_time=$(date +%s%N)
    
    # 创建测试请求
    test_request=$(cat <<EOF
{
    "text": "$test_text",
    "voice_id": "default",
    "parameters": {
        "speed": 1.0,
        "pitch": 1.0
    }
}
EOF
)
    
    # 执行测试
    response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "$test_request" \
        "$MEGATTS3_URL/api/v1/tts/synthesize" \
        --max-time 30)
    
    http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" = "200" ]; then
        end_time=$(date +%s%N)
        synthesis_time=$(( (end_time - start_time) / 1000000 ))
        
        log_info "✅ 语音合成测试成功"
        echo "   合成时间: ${synthesis_time}ms"
        echo "   文本长度: ${#test_text} 字符"
        
        # 计算性能指标
        chars_per_second=$((${#test_text} * 1000 / synthesis_time))
        echo "   处理速度: ${chars_per_second} 字符/秒"
        
    else
        log_error "❌ 语音合成测试失败 (HTTP: $http_code)"
    fi
}

# 检查日志
check_logs() {
    log_title "日志检查"
    
    echo "   最近的容器日志 (最后20行):"
    docker logs --tail=20 "$CONTAINER_NAME" 2>&1 | while IFS= read -r line; do
        if echo "$line" | grep -qi "error"; then
            echo -e "   ${RED}$line${NC}"
        elif echo "$line" | grep -qi "warn"; then
            echo -e "   ${YELLOW}$line${NC}"
        else
            echo "   $line"
        fi
    done
    
    # 检查错误日志
    error_count=$(docker logs "$CONTAINER_NAME" 2>&1 | grep -ci "error" || echo "0")
    if [ "$error_count" -gt 0 ]; then
        log_warn "⚠️  发现 $error_count 个错误日志条目"
    else
        log_info "✅ 无错误日志"
    fi
}

# 生成健康报告
generate_report() {
    log_title "健康检查总结"
    
    echo "检查时间: $(date)"
    echo "MegaTTS3版本: $(curl -s "$MEGATTS3_URL/api/v1/info" | jq -r '.version // "未知"')"
    echo "系统负载: $(uptime | awk -F'load average:' '{print $2}')"
    
    # 检查关键指标
    echo ""
    echo "关键指标状态:"
    
    # 服务状态
    if docker ps --filter "name=$CONTAINER_NAME" --format "{{.Names}}" | grep -q "$CONTAINER_NAME"; then
        echo "  🟢 服务运行状态: 正常"
    else
        echo "  🔴 服务运行状态: 异常"
    fi
    
    # API可用性
    if curl -s -f "$MEGATTS3_URL/health" > /dev/null; then
        echo "  🟢 API可用性: 正常"
    else
        echo "  🔴 API可用性: 异常"
    fi
    
    # GPU状态
    if command -v nvidia-smi &> /dev/null && nvidia-smi > /dev/null 2>&1; then
        echo "  🟢 GPU状态: 正常"
    else
        echo "  🟡 GPU状态: 未知或异常"
    fi
    
    echo ""
}

# 主函数
main() {
    echo -e "${PURPLE}🔍 MegaTTS3 健康检查开始...${NC}"
    echo "================================================"
    
    # 检查是否安装了必要工具
    for cmd in curl jq docker; do
        if ! command -v $cmd &> /dev/null; then
            log_error "缺少必要工具: $cmd"
            exit 1
        fi
    done
    
    # 执行各项检查
    check_service_status
    echo ""
    check_gpu_status
    echo ""
    check_system_resources
    echo ""
    check_network
    echo ""
    check_model_status
    echo ""
    check_logs
    echo ""
    
    # 性能测试（可选）
    if [ "${1:-}" = "--performance" ] || [ "${1:-}" = "-p" ]; then
        performance_test
        echo ""
    fi
    
    generate_report
    
    echo "================================================"
    echo -e "${PURPLE}✨ MegaTTS3 健康检查完成${NC}"
}

# 处理命令行参数
case "${1:-}" in
    --help|-h)
        echo "MegaTTS3 健康检查脚本"
        echo ""
        echo "用法: $0 [选项]"
        echo ""
        echo "选项:"
        echo "  --performance, -p  执行性能测试"
        echo "  --help, -h         显示此帮助信息"
        echo ""
        echo "示例:"
        echo "  $0                 # 基础健康检查"
        echo "  $0 -p             # 包含性能测试的完整检查"
        exit 0
        ;;
    --performance|-p)
        main --performance
        ;;
    "")
        main
        ;;
    *)
        echo "未知选项: $1"
        echo "使用 $0 --help 查看帮助信息"
        exit 1
        ;;
esac 