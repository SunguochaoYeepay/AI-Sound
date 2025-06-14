# 前端开发指南

## 🚨 重要提醒

**修改前端代码后必须重新构建并部署才能看到效果！**

## 📋 标准开发流程

### 方式一：手动部署（每次修改后执行）
```bash
# 运行自动部署脚本
./scripts/deploy-frontend.ps1
```

### 方式二：自动监控（推荐开发时使用）
```bash
# 启动文件监控，自动重新部署
./scripts/dev-watch.ps1
```

### 方式三：手动操作
```bash
# 1. 构建前端
cd platform/frontend
npm run build

# 2. 复制文件（根据docker-compose配置选择）
cd ../..
# 如果使用nginx-dist目录：
Copy-Item -Path "platform/frontend/dist/*" -Destination "nginx-dist/" -Recurse -Force

# 3. 重启nginx
docker-compose restart nginx
```

## 🔧 配置说明

### Docker挂载方式
- **直接挂载dist目录**（推荐）：修改后只需构建，无需复制
- **nginx-dist中转目录**：需要构建+复制+重启

### 开发环境设置
- 使用 `scripts/dev-watch.ps1` 进行实时监控
- 支持文件变化自动重新部署
- 包含防抖动机制，避免频繁构建

## 🎯 最佳实践

1. **开发阶段**：使用 `./scripts/dev-watch.ps1` 自动监控
2. **测试阶段**：使用 `./scripts/deploy-frontend.ps1` 手动部署
3. **生产环境**：集成到CI/CD流程中

## ⚠️ 常见问题

### Q: 修改代码后页面没有变化？
A: 检查是否执行了构建和部署步骤

### Q: 浏览器显示旧内容？
A: 强制刷新 `Ctrl+F5` 清除缓存

### Q: 构建失败？
A: 检查代码语法错误，查看控制台错误信息

## 📁 文件结构
```
AI-Sound/
├── platform/frontend/
│   ├── src/           # 源代码
│   └── dist/          # 构建输出
├── nginx-dist/        # nginx挂载目录（可选）
├── scripts/
│   ├── deploy-frontend.ps1 # 部署脚本
│   └── dev-watch.ps1      # 开发监控脚本
└── docs/              # 文档目录
``` 