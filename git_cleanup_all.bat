@echo off
echo 开始处理所有Git变更...

echo.
echo ========== 当前Git状态 ==========
git status

echo.
echo ========== 添加所有变更（包括删除的文件）==========
REM 使用 git add -A 来添加所有变更，包括删除的文件
git add -A

echo.
echo ========== 添加核心修改文件 ==========
git add platform/backend/app/api/v1/auth.py
git add platform/backend/app/config/data/system_settings.json
git add platform/backend/app/config/logging_config.py
git add platform/backend/app/core/auth.py
git add platform/backend/app/middleware/logging_middleware.py
git add platform/backend/main.py
git add platform/frontend/src/views/LogMonitor.vue
git add platform/frontend/src/main.js

echo.
echo ========== 添加迁移文件 ==========
git add "platform/backend/alembic/versions/20250701_0925_c2bf04f8d306_合并所有迁移分支.py"

echo.
echo ========== 删除二进制备份文件 ==========
if exist platform\backend\ai_sound_sqlite_backup.db (
    del platform\backend\ai_sound_sqlite_backup.db
    git rm --cached platform/backend/ai_sound_sqlite_backup.db 2>nul
)

echo.
echo ========== 再次查看Git状态 ==========
git status

echo.
echo ========== 提交所有变更 ==========
git commit -m "fix: 修复日志系统问题并清理项目

核心修复：
- 修复bcrypt兼容性警告，配置警告过滤器  
- 修复认证依赖链，分离数据库会话与认证依赖
- 增强控制台日志输出，支持开发模式详细日志
- 修复API访问日志记录和显示
- 修复前端dayjs UTC插件配置，解决时间格式化问题

项目清理：
- 添加数据库迁移文件（合并所有迁移分支）
- 清理30+个临时测试文件和调试脚本
- 删除过时的启动脚本和修复脚本  
- 移除SQLite备份文件和二进制文件

系统现在可以正常显示日志监控页面和API访问日志，项目结构更加整洁"

echo.
echo ========== 推送到远程仓库 ==========
git push origin master

echo.
echo ✅ Git操作完成！
pause 