# AI-Sound API对接指南

## 📋 概览

本文档提供前后端API对接的完整指南，确保前后端协作顺利。

**生成时间**: 2025-05-30 23:09:35
**后端地址**: http://localhost:9930
**前端地址**: http://localhost:8929

## 🔧 关键API端点

### 1. 系统信息
```
GET /health - 健康检查
GET /info - 系统信息
```

### 2. 引擎管理
```
GET /api/engines/ - 获取引擎列表
POST /api/engines/ - 创建引擎
GET /api/engines/{id} - 获取引擎详情
PUT /api/engines/{id} - 更新引擎
DELETE /api/engines/{id} - 删除引擎
```

### 3. 声音管理
```
GET /api/voices/ - 获取声音列表
POST /api/voices/ - 创建声音
POST /api/voices/upload - 上传声音文件
```

### 4. TTS合成
```
POST /api/tts/synthesize - 同步合成
POST /api/tts/synthesize-async - 异步合成
GET /api/tts/tasks/{id} - 查询任务状态
```

## 📊 标准响应格式

### 成功响应
```json
{
  "success": true,
  "data": {...},
  "message": "操作成功"
}
```

### 错误响应
```json
{
  "success": false,
  "error": "错误信息",
  "code": "ERROR_CODE"
}
```

## 🛠️ 前端调用示例

### 使用axios
```javascript
// 获取声音列表
const response = await axios.get('/api/voices/');
const voices = response.data.data || response.data;

// TTS合成
const ttsResponse = await axios.post('/api/tts/synthesize', {
  text: '要合成的文本',
  voice_id: 'xiaoxiao',
  format: 'wav'
});
```

## ⚠️ 常见问题

### 1. CORS问题
**现象**: 浏览器报CORS错误
**解决**: 后端添加CORS中间件，允许前端域名

### 2. 响应格式不一致
**现象**: 前端无法正确解析响应
**解决**: 统一使用标准响应格式

### 3. 接口超时
**现象**: 请求超时
**解决**: 增加超时设置，优化后端性能

## 🎯 最佳实践

1. **错误处理**: 前端要有完善的错误处理机制
2. **加载状态**: 显示加载状态，提升用户体验
3. **数据验证**: 前后端都要进行数据验证
4. **日志记录**: 记录关键操作日志，便于调试

## 📞 联系方式

如有问题，请联系开发团队。
