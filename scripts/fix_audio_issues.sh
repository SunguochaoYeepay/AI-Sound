#!/bin/bash

# =====================================================
# AI-Sound 音频文件问题修复脚本
# 功能: 修复AudioFile模型相关问题
# =====================================================

set -e  # 遇到错误立即停止

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="ai_sound"
DB_USER="ai_sound_user"
MIGRATION_FILE="./database/migrations/002_fix_audio_segment_issues.sql"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  AI-Sound 音频文件问题修复${NC}"
echo -e "${BLUE}========================================${NC}"

# 检查必要文件
if [ ! -f "$MIGRATION_FILE" ]; then
    echo -e "${RED}错误: 迁移文件不存在: $MIGRATION_FILE${NC}"
    exit 1
fi

# 函数: 检查数据库连接
check_db_connection() {
    echo -e "${YELLOW}检查数据库连接...${NC}"
    
    # 检查Docker容器是否运行
    if ! docker compose ps | grep -q "ai-sound-db.*Up"; then
        echo -e "${YELLOW}启动数据库容器...${NC}"
        docker compose up -d ai-sound-db
        sleep 10
    fi
    
    # 检查数据库连接
    if docker compose exec ai-sound-db pg_isready -h localhost -p 5432 -U $DB_USER; then
        echo -e "${GREEN}✅ 数据库连接正常${NC}"
    else
        echo -e "${RED}❌ 数据库连接失败${NC}"
        exit 1
    fi
}

# 函数: 执行迁移
run_migration() {
    echo -e "${YELLOW}执行数据库迁移...${NC}"
    
    # 复制迁移文件到容器
    docker cp "$MIGRATION_FILE" ai-sound-db:/tmp/migration_002.sql
    
    # 执行迁移
    if docker compose exec -T ai-sound-db psql -U $DB_USER -d $DB_NAME -f /tmp/migration_002.sql; then
        echo -e "${GREEN}✅ 数据库迁移执行成功${NC}"
    else
        echo -e "${RED}❌ 数据库迁移执行失败${NC}"
        exit 1
    fi
}

# 函数: 重启后端服务
restart_backend() {
    echo -e "${YELLOW}重启后端服务以应用模型更改...${NC}"
    
    # 重启后端容器
    docker compose restart ai-sound-backend
    
    # 等待服务启动
    echo -e "${YELLOW}等待后端服务启动...${NC}"
    sleep 15
    
    # 检查健康状态
    if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 后端服务启动成功${NC}"
    else
        echo -e "${YELLOW}⚠️  后端服务可能需要更多时间启动${NC}"
        echo -e "${YELLOW}请手动检查: curl http://localhost:8000/api/health${NC}"
    fi
}

# 函数: 测试音频文件列表API
test_audio_api() {
    echo -e "${YELLOW}测试音频文件列表API...${NC}"
    
    # 等待一下确保服务完全启动
    sleep 5
    
    if curl -f -s http://localhost:8000/api/v1/audio-library/files?page=1&page_size=5 > /dev/null; then
        echo -e "${GREEN}✅ 音频文件列表API正常${NC}"
    else
        echo -e "${RED}❌ 音频文件列表API仍有问题${NC}"
        echo -e "${YELLOW}请检查后端日志: docker compose logs ai-sound-backend${NC}"
    fi
}

# 主执行流程
main() {
    echo -e "${BLUE}开始修复音频文件问题...${NC}"
    echo ""
    
    # 1. 检查数据库连接
    check_db_connection
    echo ""
    
    # 2. 执行迁移
    run_migration
    echo ""
    
    # 3. 重启后端服务
    restart_backend
    echo ""
    
    # 4. 测试API
    test_audio_api
    echo ""
    
    # 5. 显示完成信息
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}🎉 音频文件问题修复完成！${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "${GREEN}修复内容:${NC}"
    echo -e "  ✅ 添加了 text_segments.completed_at 字段"
    echo -e "  ✅ 修复了 AudioFile.to_dict() 方法的安全性"
    echo -e "  ✅ 清理了孤儿数据引用"
    echo -e "  ✅ 添加了性能索引"
    echo -e "  ✅ 创建了数据完整性检查工具"
    echo ""
    echo -e "${YELLOW}下一步操作:${NC}"
    echo -e "  1. 访问 http://localhost:3001/audio-library 测试音频库"
    echo -e "  2. 检查是否还有错误: docker compose logs ai-sound-backend"
    echo -e "  3. 运行完整性检查: docker compose exec ai-sound-db psql -U $DB_USER -d $DB_NAME -c \"SELECT * FROM check_audio_files_integrity();\""
    echo ""
}

# 执行主函数
main 