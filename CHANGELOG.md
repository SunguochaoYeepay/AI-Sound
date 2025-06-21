# 更新日志

## [2025-01-26] 修复备份功能PostgreSQL工具依赖问题

### 🐛 问题修复
- **备份功能错误**：修复"pg_dump 工具未安装"的500错误
- **PostgreSQL依赖**：解决Windows平台PostgreSQL客户端工具缺失问题
- **路径检测优化**：增强pg_dump工具的自动检测和路径查找
- **错误提示改进**：提供详细的PostgreSQL安装指导信息

### 🔧 技术改进
- **环境检查功能**：新增`check_backup_environment()`方法
- **智能路径查找**：支持多个PostgreSQL版本的自动检测
- **Windows兼容性**：解决asyncio子进程在Windows平台的兼容问题
- **日志系统完善**：修复SystemLog字段错误和异步调用问题

### 📁 文件变更
#### 后端
- `app/utils/backup_engine.py` - 优化备份引擎和错误处理
- `app/utils/restore_engine.py` - 修复恢复引擎路径检测
- `app/utils/logger.py` - 修复日志系统异步调用问题
- `app/api/v1/backup.py` - 修复SystemLog字段错误
- `app/api/v1/logs.py` - 修复枚举字段访问
- `main.py` - 完善系统日志记录

#### 文档
- `docs/tools-dependencies.md` - 新增PostgreSQL工具依赖安装指南

### 🧹 代码清理
- 删除20+个临时测试文件和调试脚本
- 清理无用的环境测试代码
- 移除过期的项目检查文件

### 💾 内存更新
- 记录PostgreSQL工具依赖问题的完整解决方案
- 保存Windows平台兼容性修复经验

## [2024-12-20] 新增日志监控功能

### ✨ 新功能
- **日志监控系统**：完整的日志查看、过滤、统计和管理功能
- **实时统计面板**：显示日志总数、各级别统计和错误率
- **高级过滤器**：支持按级别、模块、时间、关键词过滤
- **数据导出**：支持JSON和CSV格式导出
- **自动刷新**：实时监控系统日志变化

### 🔧 技术改进
- **数据库扩展**：在system_logs表中新增7个字段，提升日志详细程度
- **性能优化**：新增多个数据库索引，优化查询性能
- **API完善**：新增8个日志相关API接口
- **前端组件**：新增LogMonitor页面和LogSummary组件

### 📁 文件变更
#### 后端
- `app/models/system.py` - 扩展日志模型
- `app/api/v1/logs.py` - 新增日志API接口
- `app/utils/logger.py` - 日志工具函数
- `migrate_log_fields.py` - 数据库迁移脚本

#### 前端  
- `src/views/LogMonitor.vue` - 日志监控主页面
- `src/components/LogSummary.vue` - 统计组件
- `src/api/logs.js` - API接口封装
- `src/App.vue` - 导航菜单更新

### 🐛 问题修复
- 修复前端图标导入错误
- 修复API路径映射问题
- 解决数据库字段类型兼容性问题

### 📖 文档
- 新增完整的功能说明文档
- 提供部署和使用指南
- 包含API接口文档和扩展说明