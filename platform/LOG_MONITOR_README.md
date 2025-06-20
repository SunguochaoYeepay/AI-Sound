# 日志监控系统使用指南

## 概述

AI-Sound平台的日志监控系统提供完整的系统运行状态跟踪、错误诊断和性能分析功能。

## 功能特性

### 🔍 实时日志监控
- 实时查看系统日志
- 多级别日志过滤（调试、信息、警告、错误、严重）
- 模块化日志分类（系统、TTS、数据库、API、WebSocket等）
- 关键词搜索和时间范围过滤

### 📊 统计分析
- 日志级别分布统计
- 错误率计算和趋势分析
- 模块活动监控
- 系统健康状态评估

### 🚨 错误监控
- 错误日志高亮显示
- 最近错误快速访问
- 错误详情查看
- 异常堆栈追踪

### 📥 数据导出
- 支持JSON和CSV格式导出
- 自定义导出条件
- 批量日志下载

### 🧹 日志管理
- 自动日志清理
- 可配置保留天数
- 存储空间优化

## 快速开始

### 前端访问

1. 在浏览器中访问 `/logs` 页面
2. 在Dashboard中查看日志概览
3. 使用过滤器筛选感兴趣的日志

### 后端集成

#### 1. 导入日志工具
```python
from app.utils.logger import log_info, log_error, log_api_request
from app.models.log import LogLevel, LogModule
```

#### 2. 记录系统日志
```python
# 基本日志记录
log_info("用户登录成功", module=LogModule.AUTH, user_id="12345")
log_error("数据库连接失败", module=LogModule.DATABASE, details={"host": "localhost"})

# API请求日志（自动记录）
log_api_request(
    method="POST",
    path="/api/v1/synthesis",
    status_code=200,
    response_time=150.5,
    user_id="12345"
)

# TTS操作日志
log_tts_operation(
    operation="synthesis",
    status="completed",
    duration=3.2,
    text_length=120,
    voice_model="zh-CN-XiaoxiaoNeural"
)

# 合成操作日志
log_synthesis_operation(
    project_id="proj_123",
    operation="start_synthesis",
    status="running",
    progress=45.6,
    chapters_count=12
)
```

#### 3. 自定义日志记录
```python
from app.utils.logger import log_to_database
from app.models.log import LogLevel, LogModule

log_to_database(
    level=LogLevel.WARNING,
    module=LogModule.SYSTEM,
    message="磁盘空间不足",
    details={
        "available_space": "2GB",
        "threshold": "5GB",
        "disk": "/data"
    },
    user_id="system"
)
```

## 数据库设置

### 创建日志表

如果您是首次设置，需要创建日志表：

```bash
# 方法1: 使用Alembic迁移（推荐）
cd platform/backend
alembic upgrade head

# 方法2: 直接运行Python脚本
python -c "from app.database.migration_helper import initialize_log_system; initialize_log_system()"
```

### 表结构说明

系统日志表 `system_logs` 包含以下字段：

- `id`: 主键
- `level`: 日志级别（debug, info, warning, error, critical）
- `module`: 模块名称（system, tts, database, api, websocket等）
- `message`: 日志消息
- `details`: JSON格式的详细信息
- `source_file`: 源文件路径
- `source_line`: 源代码行号
- `user_id`: 用户ID
- `session_id`: 会话ID
- `ip_address`: 客户端IP地址
- `user_agent`: 用户代理字符串
- `created_at`: 创建时间

## 配置选项

### 中间件配置

在 `main.py` 中添加日志中间件：

```python
from app.middleware.logging_middleware import LoggingMiddleware

# 添加日志中间件
app.add_middleware(
    LoggingMiddleware,
    skip_paths=["/health", "/docs", "/static/"]
)
```

### 性能优化

- 日志表已经添加了必要的索引以提高查询性能
- 建议定期清理旧日志（保留30-90天）
- 对于高流量系统，可以考虑使用异步日志写入

## API接口

### 获取日志列表
```
GET /api/v1/logs/list?level=error&module=tts&page=1&page_size=50
```

### 获取统计信息
```
GET /api/v1/logs/stats?hours=24
```

### 获取最近日志
```
GET /api/v1/logs/recent?limit=20&level=error
```

### 导出日志
```
GET /api/v1/logs/export?format=csv&level=error&start_time=2024-01-01T00:00:00Z
```

### 清理旧日志
```
POST /api/v1/logs/clear?days=30
```

## 前端组件

### LogMonitor 页面
完整的日志监控界面，包含：
- 统计卡片
- 过滤器
- 日志表格
- 详情弹窗
- 导出功能

### LogSummary 组件
Dashboard中的日志概览组件，显示：
- 关键指标
- 最近错误
- 级别分布
- 模块活动

## 故障排除

### 常见问题

1. **日志表不存在**
   ```bash
   python -c "from app.database.migration_helper import create_log_tables; create_log_tables()"
   ```

2. **日志记录失败**
   - 检查数据库连接
   - 确认表结构正确
   - 查看控制台错误信息

3. **前端显示异常**
   - 检查API接口是否正常
   - 确认路由配置正确
   - 查看浏览器控制台错误

### 调试模式

启用详细日志输出：

```python
import logging
logging.getLogger("app.utils.logger").setLevel(logging.DEBUG)
```

## 最佳实践

1. **合理使用日志级别**
   - DEBUG: 调试信息，生产环境建议关闭
   - INFO: 正常操作信息
   - WARNING: 警告信息，需要关注但不影响功能
   - ERROR: 错误信息，需要立即处理
   - CRITICAL: 严重错误，系统可能无法继续运行

2. **结构化日志信息**
   - 使用 `details` 字段存储结构化数据
   - 避免在 `message` 中包含大量变量信息
   - 保持消息格式一致

3. **性能考虑**
   - 避免记录过于频繁的操作
   - 使用异步日志写入
   - 定期清理旧日志

4. **安全性**
   - 不要记录敏感信息（密码、token等）
   - 使用日志中间件自动清理敏感字段

## 扩展功能

### 日志告警
可以基于日志数据创建告警规则：

```python
# 示例：错误率监控
async def check_error_rate():
    error_count = await get_error_count(hours=1)
    total_count = await get_total_count(hours=1)
    error_rate = error_count / total_count * 100
    
    if error_rate > 5:
        # 发送告警
        send_alert(f"错误率过高: {error_rate:.2f}%")
```

### 日志聚合
对于分布式部署，可以将日志发送到外部系统：

```python
# 发送到ELK Stack
import elasticsearch

def send_to_elasticsearch(log_data):
    es = elasticsearch.Elasticsearch()
    es.index(index="ai-sound-logs", body=log_data)
```

## 支持

如果在使用过程中遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查系统日志文件
3. 联系技术支持团队

---

📝 **注意**: 这是一个实时更新的文档，功能可能会持续改进和扩展。