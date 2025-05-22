# MegaTTS3 管理系统前端

## 本地开发

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 环境变量配置

创建`.env`文件：

```
# API地址
VITE_API_BASE_URL=http://localhost:9930
```

## 构建生产版本

```bash
# 构建
npm run build

# 预览构建结果
npm run preview
```

## 容器化部署（可选）

使用Nginx容器部署：

```bash
docker build -t megatts3-admin:latest .
docker run -p 80:80 megatts3-admin:latest
``` 