#!/usr/bin/env python3
"""
环境音独立化迁移执行脚本
按顺序执行数据库迁移和数据迁移
"""

import os
import sys
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def run_command(command: str, description: str) -> bool:
    """执行命令并返回是否成功"""
    print(f"\n🚀 {description}")
    print(f"执行命令: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} 成功")
        if result.stdout:
            print(f"输出: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失败")
        print(f"错误: {e.stderr}")
        return False

def main():
    """主执行函数"""
    print("🎯 开始环境音独立化迁移...")
    
    # 切换到backend目录
    os.chdir(project_root)
    
    # 步骤1: 执行数据库迁移
    if not run_command(
        "alembic upgrade head",
        "执行数据库迁移（添加novel_project_id字段）"
    ):
        print("❌ 数据库迁移失败，停止执行")
        return False
    
    # 步骤2: 执行数据迁移
    if not run_command(
        "python migrations/20250127_migrate_environment_analysis_to_independent_projects.py",
        "执行数据迁移（将环境音分析结果迁移到独立项目）"
    ):
        print("❌ 数据迁移失败，停止执行")
        return False
    
    print("\n🎉 环境音独立化迁移完成！")
    print("\n📋 迁移总结:")
    print("1. ✅ 数据库结构已更新，添加了novel_project_id外键")
    print("2. ✅ 环境音分析结果已迁移到独立的环境音项目")
    print("3. ✅ 合成项目中的环境音配置已清理")
    print("4. ✅ API已重构为使用独立的环境音项目服务")
    
    print("\n🔧 后续操作:")
    print("1. 重启后端服务以应用新的API逻辑")
    print("2. 测试环境音分析功能是否正常工作")
    print("3. 验证环境音项目与合成项目的关联关系")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
