# 构建阶段
FROM node:18-alpine AS build

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 安装依赖
RUN npm config set registry https://registry.npmmirror.com/ && \
    npm install

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产阶段
FROM nginx:latest

# 从构建阶段复制构建结果到Nginx目录
COPY --from=build /app/dist /usr/share/nginx/html

# 配置Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 运行Nginx
CMD ["nginx", "-g", "daemon off;"]