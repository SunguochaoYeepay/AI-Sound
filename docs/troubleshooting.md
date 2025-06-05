# AI-Sound Platform 故障排查指南

## 🎯 快速诊断

在遇到问题时，首先执行以下基础检查：

```bash
# 1. 检查服务状态
docker-compose ps

# 2. 检查服务健康状态
curl -f http://localhost/health
curl -f http://localhost/api/health

# 3. 检查端口占用
netstat -tulpn | grep :80
netstat -tulpn | grep :8000
netstat -tulpn | grep :9000

# 4. 检查系统资源
docker stats
df -h
free -h
```

## 🚨 常见问题及解决方案

### 1. 服务启动失败

#### 问题描述
- 容器启动失败
- 服务无法正常启动
- Docker Compose 报错

#### 可能原因
1. 端口被占用
2. 磁盘空间不足
3. 内存不足
4. Docker配置错误

#### 解决步骤

**检查端口占用：**
```bash
# Windows
netstat -ano | findstr :80
netstat -ano | findstr :8000

# Linux/Mac
netstat -tulpn | grep :80
lsof -i :8000
```

**检查磁盘空间：**
```bash
# 检查磁盘使用
df -h

# 清理Docker资源
docker system prune -f
docker volume prune -f
docker image prune -f
```

**检查内存使用：**
```bash
# 检查内存
free -h

# 检查Docker内存限制
docker info | grep -i memory
```

**重新启动服务：**
```bash
# 完全重新启动
docker-compose down
docker-compose up -d --force-recreate
```

### 2. 数据库连接问题

#### 问题描述
- API返回数据库连接错误
- 后端服务无法启动
- 数据库初始化失败

#### 解决步骤

**检查数据库服务：**
```bash
# 检查数据库容器状态
docker-compose logs database

# 检查数据库连接
docker-compose exec database pg_isready -U ai_sound_user -d ai_sound

# 进入数据库容器
docker-compose exec database psql -U ai_sound_user -d ai_sound
```

**重置数据库：**
```bash
# 停止服务
docker-compose down

# 删除数据库数据（谨慎操作）
rm -rf data/database/postgres

# 重新启动
docker-compose up -d database

# 等待数据库初始化完成后启动其他服务
docker-compose up -d
```

**SQLite问题：**
```bash
# 检查SQLite文件权限
ls -la data/database/
chmod 664 data/database/ai_sound.db

# 修复数据库文件权限
sudo chown -R $USER:$USER data/database/
```

### 3. MegaTTS3连接问题

#### 问题描述
- 语音合成失败
- 连接MegaTTS3引擎超时
- TTS服务不可用

#### 解决步骤

**检查MegaTTS3服务：**
```bash
# 检查MegaTTS3是否运行在9000端口
curl -f http://localhost:9000/health
# 或
telnet localhost 9000
```

**检查网络连接：**
```bash
# 从后端容器测试连接
docker-compose exec backend curl -f http://host.docker.internal:9000/health

# 检查Docker网络配置
docker network ls
docker network inspect ai-sound_ai-sound-network
```

**修复网络问题：**
```bash
# 重新创建网络
docker-compose down
docker network prune -f
docker-compose up -d
```

### 4. 前端访问问题

#### 问题描述
- 页面无法加载
- 静态资源404错误
- API请求失败

#### 解决步骤

**检查Nginx配置：**
```bash
# 检查Nginx日志
docker-compose logs nginx

# 测试Nginx配置
docker-compose exec nginx nginx -t

# 重新加载Nginx配置
docker-compose exec nginx nginx -s reload
```

**检查前端服务：**
```bash
# 检查前端容器日志
docker-compose logs frontend

# 进入前端容器检查
docker-compose exec frontend ls -la /usr/share/nginx/html/
```

**清除浏览器缓存：**
- 按 Ctrl+F5 强制刷新
- 清除浏览器缓存和Cookie
- 尝试无痕模式访问

### 5. 音频文件访问问题

#### 问题描述
- 音频文件下载失败
- 文件路径404错误
- 权限拒绝错误

#### 解决步骤

**检查文件权限：**
```bash
# 检查音频文件目录权限
ls -la data/audio/

# 修复权限（Linux/Mac）
chmod -R 755 data/audio/
chown -R $USER:$USER data/audio/

# Windows - 确保Docker有访问权限
# 右键data文件夹 -> 属性 -> 安全 -> 编辑权限
```

**检查文件路径：**
```bash
# 确认文件存在
find data/audio/ -name "*.wav" -o -name "*.mp3"

# 检查Nginx音频路径配置
docker-compose exec nginx cat /etc/nginx/nginx.conf | grep audio
```

### 6. 性能问题

#### 问题描述
- 服务响应慢
- 内存使用过高
- CPU使用率高

#### 解决步骤

**监控资源使用：**
```bash
# 监控容器资源使用
docker stats

# 查看系统资源
htop
iotop
```

**优化措施：**
```bash
# 增加内存限制
# 在docker-compose.yml中添加：
# mem_limit: 2g
# memswap_limit: 2g

# 启用Redis缓存
docker-compose up -d redis

# 清理日志文件
find data/logs/ -name "*.log" -mtime +7 -delete
```

### 7. SSL/HTTPS问题

#### 问题描述
- HTTPS连接失败
- 证书错误
- 混合内容警告

#### 解决步骤

**检查SSL证书：**
```bash
# 检查证书文件
ls -la docker/nginx/ssl/

# 测试证书有效性
openssl x509 -in docker/nginx/ssl/cert.pem -text -noout
```

**更新证书：**
```bash
# 使用Let's Encrypt更新证书
certbot renew --dry-run

# 重新加载Nginx
docker-compose exec nginx nginx -s reload
```

## 🔍 日志分析

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志（最近100行）
docker-compose logs --tail=100 backend
docker-compose logs --tail=100 frontend
docker-compose logs --tail=100 nginx

# 查看特定时间段日志
docker-compose logs --since="2024-01-01T00:00:00" backend

# 保存日志到文件
docker-compose logs > debug.log
```

### 日志级别说明

| 级别 | 说明 | 示例 |
|------|------|------|
| ERROR | 错误信息 | 数据库连接失败 |
| WARN | 警告信息 | 配置项缺失 |
| INFO | 常规信息 | 服务启动完成 |
| DEBUG | 调试信息 | API请求详情 |

### 常见错误日志

**数据库连接错误：**
```
ERROR: could not connect to server: Connection refused
```

**端口占用错误：**
```
ERROR: for nginx  Cannot start service nginx: driver failed programming external connectivity
```

**内存不足错误：**
```
ERROR: Cannot start container: OCI runtime create failed
```

## 🛠️ 调试工具

### 容器内调试

```bash
# 进入后端容器
docker-compose exec backend bash

# 进入前端容器
docker-compose exec frontend sh

# 进入数据库容器
docker-compose exec database psql -U ai_sound_user -d ai_sound

# 查看容器内进程
docker-compose exec backend ps aux
```

### 网络调试

```bash
# 测试容器间连接
docker-compose exec backend ping frontend
docker-compose exec backend curl http://frontend

# 查看网络配置
docker network inspect ai-sound_ai-sound-network

# 端口映射检查
docker port ai-sound-nginx
```

### 文件系统调试

```bash
# 检查挂载点
docker-compose exec backend df -h

# 查看文件权限
docker-compose exec backend ls -la /app/data/

# 测试文件写入
docker-compose exec backend touch /app/data/test.txt
```

## 📞 获取帮助

### 自助资源

1. **官方文档**: [docs/deployment.md](deployment.md)
2. **API文档**: http://localhost/docs
3. **GitHub Issues**: 搜索已知问题

### 提交问题

在提交问题时，请提供以下信息：

```bash
# 系统信息
uname -a
docker --version
docker-compose --version

# 服务状态
docker-compose ps

# 相关日志
docker-compose logs --tail=50 > debug.log

# 配置信息（去除敏感信息）
cat .env | grep -v PASSWORD | grep -v SECRET
```

### 社区支持

- 💬 **GitHub Discussions**: 技术讨论
- 📧 **邮件支持**: support@yourdomain.com
- 🐛 **Bug报告**: GitHub Issues

---

## ⚡ 性能优化建议

### 系统级优化

1. **增加系统资源**
   - 内存: 最少4GB，推荐8GB+
   - CPU: 最少2核，推荐4核+
   - 磁盘: SSD，剩余空间>20GB

2. **Docker优化**
   ```bash
   # 调整Docker配置
   # /etc/docker/daemon.json
   {
     "log-driver": "json-file",
     "log-opts": {
       "max-size": "10m",
       "max-file": "3"
     }
   }
   ```

3. **数据库优化**
   - 使用PostgreSQL替代SQLite
   - 配置连接池
   - 定期清理日志

### 应用级优化

1. **启用缓存**
   ```bash
   # 启用Redis缓存
   docker-compose up -d redis
   ```

2. **配置CDN**
   - 静态资源使用CDN
   - 音频文件分发加速

3. **监控告警**
   - 配置Prometheus监控
   - 设置告警规则

---

**💡 提示**: 定期查看此文档，我们会持续更新常见问题的解决方案。 