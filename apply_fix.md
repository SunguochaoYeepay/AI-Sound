## 🔧 MegaTTS3 SSL端口问题修复

### 问题分析
错误信息：`Cannot connect to host ai-sound-megatts3:7930 ssl:default [Connection refused]`

**根本原因**：aiohttp默认会尝试SSL连接，导致端口从7929变成7930。

### 修复内容
1. ✅ 已修复 `tts_client.py` - 强制禁用SSL连接
2. ✅ 已修复健康检查中的SSL问题
3. ✅ 使用 `TCPConnector(ssl=False)` 强制HTTP连接

### 需要执行的命令

请在PowerShell中执行：

```powershell
# 1. 重启backend容器应用修复
docker stop ai-sound-backend
docker rm ai-sound-backend
docker compose -f docker-compose.prod.yml up -d --build backend

# 2. 等待容器启动
Start-Sleep 15

# 3. 检查容器状态
docker ps | findstr ai-sound

# 4. 测试健康检查
curl http://localhost:3001/api/health

# 5. 查看backend日志
docker logs ai-sound-backend --tail 20
```

### 或者使用批处理脚本

双击运行 `restart_backend.bat` 文件。

### 预期结果
- ✅ 前端不再显示 "7930端口" 错误
- ✅ 语音合成功能正常工作
- ✅ 后端日志显示连接到7929端口成功 