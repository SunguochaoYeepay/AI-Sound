@echo off
echo 🧹 Docker清理脚本
echo ==========================================

echo 1️⃣ 停止所有相关容器...
docker-compose stop

echo 2️⃣ 删除所有相关容器...
docker-compose rm -f

echo 3️⃣ 清理Docker系统缓存...
docker system prune -af

echo 4️⃣ 清理Docker构建缓存...
docker builder prune -af

echo 5️⃣ 删除项目相关镜像...
for /f "tokens=*" %%i in ('docker images -q services-* services_*') do docker rmi -f %%i

echo 6️⃣ 清理未使用的卷...
docker volume prune -f

echo 7️⃣ 显示清理结果...
docker system df

echo ==========================================
echo ✅ Docker清理完成！
echo 💾 释放的空间信息如上所示
pause 