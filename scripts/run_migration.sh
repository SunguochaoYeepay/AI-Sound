#!/bin/bash

# =====================================================
# 智能分析系统数据库迁移执行脚本
# 功能: 安全执行数据库迁移，包含备份和回滚机制
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
DB_PASSWORD="ai_sound_password"
BACKUP_DIR="./database/backups"
MIGRATION_FILE="./database/migrations/001_smart_analysis_upgrade.sql"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/backup_before_migration_$TIMESTAMP.sql"

# 创建备份目录
mkdir -p $BACKUP_DIR

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  AI-Sound 智能分析系统数据库迁移${NC}"
echo -e "${BLUE}======================================${NC}"

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
        docker compose up -d database
        sleep 10
    fi
    
    # 检查数据库连接
    if docker compose exec database pg_isready -h localhost -p 5432 -U $DB_USER; then
        echo -e "${GREEN}✅ 数据库连接正常${NC}"
    else
        echo -e "${RED}❌ 数据库连接失败${NC}"
        exit 1
    fi
}

# 函数: 创建数据库备份
create_backup() {
    echo -e "${YELLOW}创建数据库备份...${NC}"
    
    docker compose exec -T database pg_dump \
        -h localhost \
        -U $DB_USER \
        -d $DB_NAME \
        --clean \
        --if-exists \
        --verbose \
        > "$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 备份创建成功: $BACKUP_FILE${NC}"
        echo -e "   备份大小: $(du -h "$BACKUP_FILE" | cut -f1)"
    else
        echo -e "${RED}❌ 备份创建失败${NC}"
        exit 1
    fi
}

# 函数: 执行迁移
run_migration() {
    echo -e "${YELLOW}执行数据库迁移...${NC}"
    
    # 复制迁移文件到容器
    docker cp "$MIGRATION_FILE" ai-sound-db:/tmp/migration.sql
    
    # 执行迁移
    if docker compose exec -T database psql -U $DB_USER -d $DB_NAME -f /tmp/migration.sql; then
        echo -e "${GREEN}✅ 数据库迁移执行成功${NC}"
    else
        echo -e "${RED}❌ 数据库迁移执行失败${NC}"
        echo -e "${YELLOW}正在恢复数据库...${NC}"
        restore_backup
        exit 1
    fi
}

# 函数: 恢复备份
restore_backup() {
    echo -e "${YELLOW}从备份恢复数据库...${NC}"
    
    if [ -f "$BACKUP_FILE" ]; then
        docker compose exec -T database psql -U $DB_USER -d $DB_NAME < "$BACKUP_FILE"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ 数据库恢复成功${NC}"
        else
            echo -e "${RED}❌ 数据库恢复失败${NC}"
        fi
    else
        echo -e "${RED}❌ 备份文件不存在: $BACKUP_FILE${NC}"
    fi
}

# 函数: 验证迁移结果
verify_migration() {
    echo -e "${YELLOW}验证迁移结果...${NC}"
    
    # 检查新表是否存在
    NEW_TABLES=("book_chapters" "analysis_sessions" "analysis_results" "synthesis_tasks" "user_presets")
    
    for table in "${NEW_TABLES[@]}"; do
        if docker compose exec -T database psql -U $DB_USER -d $DB_NAME -c "\dt $table" | grep -q "$table"; then
            echo -e "${GREEN}✅ 表 $table 创建成功${NC}"
        else
            echo -e "${RED}❌ 表 $table 创建失败${NC}"
            return 1
        fi
    done
    
    # 检查新字段是否存在
    echo -e "${YELLOW}检查新增字段...${NC}"
    
    # books表新字段
    if docker compose exec -T database psql -U $DB_USER -d $DB_NAME -c "\d books" | grep -q "structure_status"; then
        echo -e "${GREEN}✅ books表新字段添加成功${NC}"
    else
        echo -e "${RED}❌ books表新字段添加失败${NC}"
        return 1
    fi
    
    # novel_projects表新字段
    if docker compose exec -T database psql -U $DB_USER -d $DB_NAME -c "\d novel_projects" | grep -q "analysis_config"; then
        echo -e "${GREEN}✅ novel_projects表新字段添加成功${NC}"
    else
        echo -e "${RED}❌ novel_projects表新字段添加失败${NC}"
        return 1
    fi
    
    # 检查预设配置是否插入
    preset_count=$(docker compose exec -T database psql -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM user_presets;" -t | tr -d ' ')
    if [ "$preset_count" -ge "2" ]; then
        echo -e "${GREEN}✅ 预设配置插入成功 ($preset_count 条)${NC}"
    else
        echo -e "${RED}❌ 预设配置插入失败${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ 所有验证检查通过${NC}"
    return 0
}

# 函数: 显示迁移总结
show_summary() {
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}         迁移完成总结${NC}"
    echo -e "${BLUE}======================================${NC}"
    echo -e "${GREEN}✅ 新增表: 5个${NC}"
    echo -e "   - book_chapters (书籍章节)"
    echo -e "   - analysis_sessions (分析会话)"
    echo -e "   - analysis_results (分析结果)"
    echo -e "   - synthesis_tasks (合成任务)"
    echo -e "   - user_presets (用户预设)"
    echo ""
    echo -e "${GREEN}✅ 修改表: 2个${NC}"
    echo -e "   - books (+4字段)"
    echo -e "   - novel_projects (+4字段)"
    echo ""
    echo -e "${GREEN}✅ 新增索引: 25个${NC}"
    echo -e "${GREEN}✅ 新增触发器: 6个${NC}"
    echo -e "${GREEN}✅ 预设配置: 2个${NC}"
    echo ""
    echo -e "${GREEN}🎉 数据库迁移成功完成！${NC}"
    echo -e "${YELLOW}💾 备份文件保存在: $BACKUP_FILE${NC}"
}

# 主执行流程
main() {
    echo -e "${BLUE}开始执行数据库迁移...${NC}"
    echo ""
    
    # 1. 检查数据库连接
    check_db_connection
    echo ""
    
    # 2. 创建备份
    create_backup
    echo ""
    
    # 3. 执行迁移
    run_migration
    echo ""
    
    # 4. 验证结果
    if verify_migration; then
        echo ""
        show_summary
    else
        echo -e "${RED}❌ 迁移验证失败，请检查错误信息${NC}"
        exit 1
    fi
}

# 处理命令行参数
case "${1:-}" in
    "backup")
        check_db_connection
        create_backup
        ;;
    "restore")
        if [ -z "$2" ]; then
            echo -e "${RED}错误: 请指定备份文件路径${NC}"
            echo "用法: $0 restore <backup_file>"
            exit 1
        fi
        BACKUP_FILE="$2"
        restore_backup
        ;;
    "verify")
        check_db_connection
        verify_migration
        ;;
    "")
        main
        ;;
    *)
        echo "用法: $0 [backup|restore <file>|verify]"
        echo ""
        echo "选项:"
        echo "  backup         - 仅创建数据库备份"
        echo "  restore <file> - 从指定备份文件恢复"
        echo "  verify         - 验证迁移结果"
        echo "  (无参数)       - 执行完整迁移流程"
        exit 1
        ;;
esac 