# 前端构建阶段
FROM node:18-alpine as build-stage

WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源码
COPY . .

# 构建应用
RUN npm run build

# 生产阶段 - 使用nginx提供静态文件（ai-sound-nginx统一管理路由）
FROM nginx:alpine as production-stage

# 复制构建结果
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 创建简单的nginx配置，只提供静态文件，不做路由处理
RUN echo 'server { \
    listen 80; \
    root /usr/share/nginx/html; \
    index index.html; \
    \
    # 所有路径都返回index.html，让Vue Router处理 \
    location / { \
        try_files \$uri \$uri/ /index.html; \
    } \
    \
    # 静态资源缓存 \
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)\$ { \
        expires 1y; \
        add_header Cache-Control "public, immutable"; \
    } \
}' > /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动nginx
CMD ["nginx", "-g", "daemon off;"] 