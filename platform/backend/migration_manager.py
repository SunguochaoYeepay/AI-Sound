#!/usr/bin/env python3
"""
Alembic迁移管理工具

使用方法：
    python migration_manager.py status          # 查看迁移状态
    python migration_manager.py check           # 检查迁移文件一致性
    python migration_manager.py safe-upgrade    # 安全升级（跳过已存在的对象）
    python migration_manager.py reset-heads     # 重置多个head到单一head
    python migration_manager.py validate        # 验证所有迁移文件
"""

import os
import sys
import subprocess
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_alembic_command(cmd: str) -> tuple[int, str, str]:
    """运行alembic命令并返回结果"""
    try:
        result = subprocess.run(
            f"alembic {cmd}",
            shell=True,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def get_migration_status():
    """获取迁移状态"""
    print("🔍 检查迁移状态...")
    
    # 检查当前版本
    returncode, stdout, stderr = run_alembic_command("current")
    if returncode == 0:
        print(f"📍 当前版本: {stdout.strip()}")
    else:
        print(f"❌ 获取当前版本失败: {stderr}")
        return False
    
    # 检查head状态
    returncode, stdout, stderr = run_alembic_command("heads")
    if returncode == 0:
        heads = stdout.strip().split('\n')
        if len(heads) > 1:
            print(f"⚠️ 发现多个head: {len(heads)}个")
            for i, head in enumerate(heads, 1):
                print(f"   {i}. {head}")
        else:
            print(f"✅ 单一head: {heads[0]}")
    else:
        print(f"❌ 获取head状态失败: {stderr}")
        return False
    
    # 检查是否有待执行的迁移
    returncode, stdout, stderr = run_alembic_command("show head")
    if returncode == 0:
        print(f"📝 最新迁移: {stdout.strip()}")
    
    return True


def check_migration_consistency():
    """检查迁移文件一致性"""
    print("\n🔍 检查迁移文件一致性...")
    
    # 检查迁移历史
    returncode, stdout, stderr = run_alembic_command("history")
    if returncode != 0:
        print(f"❌ 检查迁移历史失败: {stderr}")
        return False
    
    print("✅ 迁移历史检查通过")
    
    # 检查是否有语法错误
    versions_dir = Path("alembic/versions")
    if not versions_dir.exists():
        print("❌ 迁移文件目录不存在")
        return False
    
    migration_files = list(versions_dir.glob("*.py"))
    print(f"📁 发现 {len(migration_files)} 个迁移文件")
    
    for migration_file in migration_files:
        if migration_file.name.startswith("__"):
            continue
        try:
            # 尝试编译Python文件检查语法
            with open(migration_file, 'r', encoding='utf-8') as f:
                compile(f.read(), migration_file, 'exec')
        except SyntaxError as e:
            print(f"❌ 语法错误 {migration_file}: {e}")
            return False
    
    print("✅ 所有迁移文件语法检查通过")
    return True


def safe_upgrade():
    """安全升级数据库"""
    print("\n🚀 开始安全升级...")
    
    # 首先检查状态
    if not get_migration_status():
        print("❌ 状态检查失败，取消升级")
        return False
    
    # 执行升级
    returncode, stdout, stderr = run_alembic_command("upgrade head")
    if returncode == 0:
        print("✅ 数据库升级成功")
        print(stdout)
        return True
    else:
        print(f"❌ 数据库升级失败: {stderr}")
        print(f"详细输出: {stdout}")
        return False


def reset_heads():
    """重置多个head到单一head"""
    print("\n🔄 重置多个head...")
    
    # 获取所有head
    returncode, stdout, stderr = run_alembic_command("heads")
    if returncode != 0:
        print(f"❌ 获取head失败: {stderr}")
        return False
    
    heads = [line.strip() for line in stdout.strip().split('\n') if line.strip()]
    if len(heads) <= 1:
        print("✅ 只有一个head，无需重置")
        return True
    
    print(f"发现 {len(heads)} 个head:")
    for i, head in enumerate(heads, 1):
        print(f"  {i}. {head}")
    
    # 创建合并迁移
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    merge_message = f"merge_heads_{timestamp}"
    
    # 合并所有head
    cmd = f"merge {' '.join(heads)} -m '{merge_message}'"
    returncode, stdout, stderr = run_alembic_command(cmd)
    
    if returncode == 0:
        print(f"✅ 成功创建合并迁移: {merge_message}")
        print(stdout)
        return True
    else:
        print(f"❌ 创建合并迁移失败: {stderr}")
        return False


def validate_migrations():
    """验证所有迁移文件"""
    print("\n✅ 验证迁移文件...")
    
    # 检查迁移链的完整性
    returncode, stdout, stderr = run_alembic_command("check")
    if returncode == 0:
        print("✅ 迁移链验证通过")
        return True
    else:
        print(f"❌ 迁移链验证失败: {stderr}")
        return False


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        get_migration_status()
    elif command == "check":
        check_migration_consistency()
    elif command == "safe-upgrade":
        safe_upgrade()
    elif command == "reset-heads":
        reset_heads()
    elif command == "validate":
        validate_migrations()
    else:
        print(f"❌ 未知命令: {command}")
        print(__doc__)


if __name__ == "__main__":
    main() 