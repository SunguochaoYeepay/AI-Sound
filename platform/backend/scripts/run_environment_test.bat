@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   环境音分析测试脚本
echo ========================================
echo.

:menu
echo 请选择测试类型：
echo.
echo 1. 快速测试 (推荐日常使用)
echo 2. 完整测试 (包含多个场景)
echo 3. 退出
echo.
set /p choice=请输入选择 (1-3): 

if "%choice%"=="1" goto quick_test
if "%choice%"=="2" goto full_test
if "%choice%"=="3" goto exit
echo 无效选择，请重新输入
goto menu

:quick_test
echo.
echo 🚀 开始快速测试...
echo.
python quick_test_environment.py
echo.
echo 快速测试完成！
pause
goto menu

:full_test
echo.
echo 🚀 开始完整测试...
echo.
python test_environment_analysis.py
echo.
echo 完整测试完成！
pause
goto menu

:exit
echo.
echo 感谢使用环境音分析测试脚本！
echo.
pause
