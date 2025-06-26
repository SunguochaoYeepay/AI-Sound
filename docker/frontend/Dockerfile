# AI-Sound 前端构建 Dockerfile
FROM node:18-alpine AS builder

# 设置工作目录
WORKDIR /app

# 复制package文件
COPY platform/frontend/package*.json ./

# 安装依赖
RUN npm config set registry https://registry.npmmirror.com && \
    npm install

# 复制源代码
COPY platform/frontend/ ./

# 构建应用
RUN npm run build

# 使用nginx提供静态文件服务
FROM nginx:alpine AS production

# 复制构建产物
COPY --from=builder /app/dist/ /usr/share/nginx/html/

# 复制nginx配置（如果需要自定义）
# COPY docker/frontend/nginx.conf /etc/nginx/nginx.conf

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# 启动nginx
CMD ["nginx", "-g", "daemon off;"] 