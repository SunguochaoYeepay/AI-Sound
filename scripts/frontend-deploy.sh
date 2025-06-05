#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 检查参数
MODE=${1:-prod}

echo -e "${BLUE}===========================================${NC}"
echo -e "${BLUE}   🚀 AI-Sound 前端自动构建部署脚本${NC}"
echo -e "${BLUE}   📦 模式: ${CYAN}${MODE}${NC}"
echo -e "${BLUE}===========================================${NC}"
echo

# 检查当前目录
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ 请在项目根目录运行此脚本！${NC}"
    echo -e "${YELLOW}💡 当前目录: $(pwd)${NC}"
    exit 1
fi

# 检查依赖
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm 未安装或不在 PATH 中${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose 未安装或不在 PATH 中${NC}"
    exit 1
fi

# 步骤1: 构建前端代码
echo -e "${YELLOW}[1/5] 🏗️  开始构建前端代码...${NC}"
cd platform/frontend

# 检查前端依赖
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 安装前端依赖...${NC}"
    if ! npm install; then
        echo -e "${RED}❌ 依赖安装失败！${NC}"
        exit 1
    fi
fi

# 根据模式选择构建命令
if [ "$MODE" = "dev" ]; then
    echo -e "${CYAN}🔧 开发模式构建...${NC}"
elif [ "$MODE" = "prod" ]; then
    echo -e "${CYAN}🚀 生产模式构建...${NC}"
else
    echo -e "${RED}❌ 未知模式: $MODE (支持: dev, prod)${NC}"
    exit 1
fi

if ! npm run build; then
    echo -e "${RED}❌ 前端构建失败！${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 前端构建完成${NC}"
echo

# 回到项目根目录
cd ../..

# 步骤2: 清理nginx目录
echo -e "${YELLOW}[2/5] 🧹 清理nginx目录...${NC}"
if [ -d "nginx-dist" ]; then
    rm -rf nginx-dist/*
else
    mkdir -p nginx-dist
fi
echo -e "${GREEN}✅ nginx目录清理完成${NC}"
echo

# 步骤3: 拷贝构建文件
echo -e "${YELLOW}[3/5] 📂 拷贝构建文件到nginx目录...${NC}"
if [ ! -d "platform/frontend/dist" ]; then
    echo -e "${RED}❌ 构建目录不存在: platform/frontend/dist${NC}"
    exit 1
fi

if ! cp -r platform/frontend/dist/* nginx-dist/; then
    echo -e "${RED}❌ 文件拷贝失败！${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 文件拷贝完成${NC}"
echo

# 步骤4: 重启nginx容器
echo -e "${YELLOW}[4/5] 🔄 重启nginx容器...${NC}"
if ! docker-compose restart nginx; then
    echo -e "${RED}❌ nginx重启失败！${NC}"
    echo -e "${YELLOW}💡 提示: 请检查Docker是否运行正常${NC}"
    exit 1
fi
echo -e "${GREEN}✅ nginx重启完成${NC}"
echo

# 步骤5: 等待nginx启动
echo -e "${YELLOW}[5/5] 🔍 等待nginx启动...${NC}"
sleep 3
echo -e "${GREEN}✅ nginx启动完成${NC}"
echo

echo -e "${BLUE}===========================================${NC}"
echo -e "${GREEN}   🎉 前端部署完成！${NC}"
echo -e "${GREEN}   📱 访问地址: http://localhost:3001${NC}"
echo -e "${GREEN}   💻 部署模式: ${CYAN}${MODE}${NC}"
echo -e "${BLUE}===========================================${NC}"
echo

# 检查容器状态
echo -e "${YELLOW}📊 容器状态检查:${NC}"
docker-compose ps

echo
echo -e "${CYAN}💡 使用方法:${NC}"
echo -e "  ${GREEN}./scripts/frontend-deploy.sh${NC}           (生产模式)"
echo -e "  ${GREEN}./scripts/frontend-deploy.sh dev${NC}       (开发模式)"
echo -e "  ${GREEN}./scripts/frontend-deploy.sh prod${NC}      (生产模式)" 