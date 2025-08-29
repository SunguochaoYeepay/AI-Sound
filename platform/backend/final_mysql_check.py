#!/usr/bin/env python3
"""
最终MySQL配置检查
确保所有核心配置都正确设置为MySQL
"""

import os
import re

def check_core_configs():
    """检查核心配置文件"""
    print("🔍 检查核心配置文件...")
    
    configs_to_check = [
        ('.env', 'mysql+pymysql://'),
        ('app/database.py', 'mysql+pymysql://'),
        ('app/config.py', 'mysql+pymysql://'),
        ('app/config/__init__.py', 'mysql+pymysql://'),
        ('app/config/environment.py', '"port": 3306')
    ]
    
    all_good = True
    for file_path, expected_content in configs_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if expected_content in content:
                print(f"✅ {file_path}: 配置正确")
            else:
                print(f"❌ {file_path}: 配置错误")
                all_good = False
        else:
            print(f"⚠️  {file_path}: 文件不存在")
            all_good = False
    
    return all_good

def check_database_connection():
    """检查数据库连接"""
    print("\n🔍 检查数据库连接...")
    
    try:
        from app.database import engine
        from sqlalchemy import inspect
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'environment_projects' in tables:
            print("✅ 数据库连接: 正常，environment_projects表存在")
            print(f"📊 数据库表数量: {len(tables)}")
            return True
        else:
            print("❌ 数据库连接: environment_projects表不存在")
            return False
            
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def check_environment_variables():
    """检查环境变量"""
    print("\n🔍 检查环境变量...")
    
    # 重新加载环境变量
    from dotenv import load_dotenv
    load_dotenv()
    
    database_url = os.getenv('DATABASE_URL', '')
    
    if 'mysql+pymysql://' in database_url:
        print("✅ DATABASE_URL: MySQL配置正确")
        print(f"   {database_url}")
        return True
    else:
        print(f"❌ DATABASE_URL: 配置错误")
        print(f"   {database_url}")
        return False

def main():
    """主函数"""
    print("🔧 最终MySQL配置检查开始...\n")
    
    results = []
    results.append(check_core_configs())
    results.append(check_database_connection())
    results.append(check_environment_variables())
    
    print("\n" + "="*60)
    print("📋 最终验证结果汇总:")
    print("="*60)
    
    if all(results):
        print("🎉 所有核心配置验证通过！MySQL配置完全正确！")
        print("\n✅ 可以正常使用MySQL数据库进行开发")
        print("✅ 环境音项目管理功能可以正常使用")
        print("✅ 所有API应该都能正常工作")
    else:
        print("⚠️  部分配置需要修复")
        print("\n建议检查上述错误项")
    
    print("\n📊 详细状态:")
    print(f"- 核心配置文件: {'✅' if results[0] else '❌'}")
    print(f"- 数据库连接: {'✅' if results[1] else '❌'}")
    print(f"- 环境变量: {'✅' if results[2] else '❌'}")
    
    print("\n🚀 下一步:")
    print("1. 启动后端服务: python main.py")
    print("2. 测试API: http://localhost:8001/docs")
    print("3. 测试环境音项目管理功能")

if __name__ == "__main__":
    main()
