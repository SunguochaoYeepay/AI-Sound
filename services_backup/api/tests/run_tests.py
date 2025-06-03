"""
测试运行脚本
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(test_type="all", verbose=False, coverage=False):
    """运行测试"""
    
    # 基础pytest命令
    cmd = ["python", "-m", "pytest"]
    
    # 添加详细输出
    if verbose:
        cmd.append("-v")
    
    # 添加覆盖率
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])
    
    # 根据测试类型选择测试目录
    if test_type == "unit":
        cmd.append("tests/unit/")
    elif test_type == "integration":
        cmd.append("tests/integration/")
        cmd.append("-m integration")
    elif test_type == "api":
        cmd.append("tests/api/")
    elif test_type == "all":
        cmd.append("tests/")
    else:
        print(f"未知的测试类型: {test_type}")
        return 1
    
    # 添加其他有用的选项
    cmd.extend([
        "--tb=short",  # 简短的错误回溯
        "--strict-markers",  # 严格的标记模式
        "--disable-warnings"  # 禁用警告
    ])
    
    print(f"运行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
        return result.returncode
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"运行测试时出错: {e}")
        return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AI-Sound API测试运行器")
    parser.add_argument(
        "--type", "-t",
        choices=["unit", "integration", "api", "all"],
        default="all",
        help="测试类型 (默认: all)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="生成覆盖率报告"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("AI-Sound API 测试套件")
    print("=" * 60)
    print(f"测试类型: {args.type}")
    print(f"详细输出: {args.verbose}")
    print(f"覆盖率报告: {args.coverage}")
    print("=" * 60)
    
    exit_code = run_tests(args.type, args.verbose, args.coverage)
    
    if exit_code == 0:
        print("\n✅ 所有测试通过!")
    else:
        print(f"\n❌ 测试失败 (退出码: {exit_code})")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()