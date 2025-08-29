# 🧪 AI-Sound Platform 系统测试指南

## 📋 测试概览
本指南将帮助您验证AI-Sound Platform的所有核心功能是否正常工作。

## 🚀 快速启动测试

### Step 1: 启动后端服务
```powershell
# 方法1: 直接启动
cd platform\backend
python main.py

# 方法2: 后台启动 
Start-Job -ScriptBlock { Set-Location "D:\AI-Sound\platform\backend"; python main.py }
```

**预期结果:**
```
INFO:     Will watch for changes in these directories: ['D:\\AI-Sound\\platform\\backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
🚀 AI-Sound平台后端启动中...
📊 初始化数据库...
🎵 初始化TTS客户端...
🔌 初始化WebSocket管理器...
✅ AI-Sound平台后端启动完成!
INFO:     Application startup complete.
```

### Step 2: 启动前端服务
```powershell
# 方法1: 直接启动
cd platform\frontend
npm run dev

# 方法2: 后台启动
Start-Job -ScriptBlock { Set-Location "D:\AI-Sound\platform\frontend"; npm run dev }
```

**预期结果:**
```
  VITE v5.0.8  ready in 1234 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: http://192.168.x.x:3000/
  ➜  press h to show help
```

## 🔍 系统健康检查

### 1. 后端API测试
在浏览器中访问以下URLs：

**✅ 基础检查:**
- `http://localhost:8000/` - 根端点
- `http://localhost:8000/health` - 健康检查
- `http://localhost:8000/docs` - API文档

**✅ API端点测试:**
- `http://localhost:8000/api/v1/books` - 书籍列表
- `http://localhost:8000/api/v1/chapters` - 章节列表
- `http://localhost:8000/api/v1/projects` - 项目列表

### 2. 前端页面测试
在浏览器中访问：

**✅ 页面检查:**
- `http://localhost:3000/` - 首页/仪表板
- `http://localhost:3000/books` - 书籍管理
- `http://localhost:3000/projects` - 项目管理

### 3. 前后端连接测试
打开浏览器开发者工具(F12)，在前端页面中检查：

**✅ Network标签:**
- 查看是否有API请求发送到后端
- 检查是否返回正确的JSON响应
- 确认没有CORS错误

**✅ Console标签:**
- 检查是否有JavaScript错误
- 确认WebSocket连接成功

## 🧪 功能测试清单

### ✅ 后端功能测试

| 功能模块 | 测试点 | 期望结果 | 状态 |
|---------|--------|----------|------|
| **API路由** | GET /api/v1/books | 返回书籍列表JSON | ⭕ |
| **数据库连接** | GET /health | database.status = "healthy" | ⭕ |
| **WebSocket** | WebSocket连接 | 连接成功，收到欢迎消息 | ⭕ |
| **TTS客户端** | TTS服务检查 | tts_client.status = true | ⭕ |
| **文件管理** | 文件上传测试 | 文件成功保存 | ⭕ |

### ✅ 前端功能测试

| 功能模块 | 测试点 | 期望结果 | 状态 |
|---------|--------|----------|------|
| **页面渲染** | 访问首页 | 页面正常显示 | ⭕ |
| **API调用** | 获取数据 | 成功获取后端数据 | ⭕ |
| **状态管理** | Pinia store | 状态正确更新 | ⭕ |
| **路由跳转** | 页面导航 | 路由正常工作 | ⭕ |
| **组件交互** | UI组件 | 交互功能正常 | ⭕ |

### ✅ 集成测试

| 测试场景 | 测试步骤 | 期望结果 | 状态 |
|---------|---------|----------|------|
| **API对接** | 前端调用后端API | 数据正确显示 | ⭕ |
| **实时通信** | WebSocket消息 | 实时更新成功 | ⭕ |
| **文件上传** | 上传音频文件 | 文件处理成功 | ⭕ |
| **错误处理** | 模拟API错误 | 错误正确显示 | ⭕ |

## 🐛 故障排除

### 后端启动问题
```powershell
# 检查Python环境
python --version

# 检查依赖
cd platform\backend
pip list | findstr fastapi

# 检查端口占用
Get-NetTCPConnection -LocalPort 8000
```

### 前端启动问题
```powershell
# 检查Node.js环境
node --version
npm --version

# 重新安装依赖
cd platform\frontend
npm install

# 检查端口占用
Get-NetTCPConnection -LocalPort 3000
```

### 常见错误解决

**❌ CORS错误:**
- 检查后端CORS配置
- 确认前端代理设置

**❌ 模块导入错误:**
- 检查Python路径
- 确认依赖安装完整

**❌ 端口冲突:**
- 更改配置文件中的端口
- 或关闭占用端口的进程

## 📊 测试报告模板

```
==============================================
🧪 AI-Sound Platform 系统测试报告
测试时间: [填写时间]
测试人员: [填写姓名]
==============================================

✅ 后端服务状态:
- 启动状态: [ ] 成功 [ ] 失败
- API响应: [ ] 正常 [ ] 异常
- 健康检查: [ ] 通过 [ ] 失败

✅ 前端服务状态:
- 启动状态: [ ] 成功 [ ] 失败
- 页面加载: [ ] 正常 [ ] 异常
- API调用: [ ] 成功 [ ] 失败

✅ 集成测试结果:
- 前后端通信: [ ] 正常 [ ] 异常
- WebSocket连接: [ ] 成功 [ ] 失败
- 文件上传: [ ] 成功 [ ] 失败

总体评估: [ ] 通过 [ ] 需要修复
```

## 🎯 下一步计划

**通过基础测试后:**
1. 进行TTS功能测试
2. 测试音频文件处理
3. 验证数据库操作
4. 进行性能测试

**如果测试失败:**
1. 查看错误日志
2. 检查配置文件
3. 验证依赖安装
4. 联系技术支持 