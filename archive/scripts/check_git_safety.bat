@echo off
echo ========================================
echo    Git 数据安全检查工具
echo ========================================
echo.

cd /d "%~dp0"

echo [检查1] 查找可能被跟踪的MongoDB数据文件...
git ls-files | findstr -i "\.wt$\|WiredTiger\|mongod\.lock\|\.bson$" >nul
if errorlevel 1 (
    echo [✓] 没有发现MongoDB数据文件被跟踪
) else (
    echo [✗] 警告：发现MongoDB数据文件被Git跟踪！
    echo 被跟踪的文件：
    git ls-files | findstr -i "\.wt$\|WiredTiger\|mongod\.lock\|\.bson$"
    echo.
    echo 建议运行：git rm --cached [文件名]
)

echo.
echo [检查2] 查找Docker数据卷目录...
git ls-files | findstr "docker/volumes/.*/" >nul
if errorlevel 1 (
    echo [✓] Docker数据卷目录未被跟踪
) else (
    echo [✗] 警告：发现Docker数据卷被Git跟踪！
    echo 被跟踪的目录：
    git ls-files | findstr "docker/volumes/"
)

echo.
echo [检查3] 验证.gitignore规则...
git check-ignore docker/volumes/mongodb/ >nul
if errorlevel 1 (
    echo [✗] 警告：MongoDB目录未被.gitignore忽略！
) else (
    echo [✓] MongoDB目录已被正确忽略
)

echo.
echo [检查4] 当前Git状态...
echo 未跟踪的文件数量：
git status --porcelain | findstr "^??" | find /c "??"

echo.
echo [检查5] 数据目录大小...
if exist "docker\volumes\mongodb" (
    echo MongoDB数据目录存在，大小：
    dir /s docker\volumes\mongodb | findstr "个文件"
) else (
    echo MongoDB数据目录不存在
)

echo.
echo ========================================
echo 检查完成！确保数据安全！
echo ========================================
pause 