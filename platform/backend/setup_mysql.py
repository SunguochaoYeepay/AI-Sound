#!/usr/bin/env python3
"""
MySQL数据库设置脚本
"""

import pymysql

print("开始设置MySQL数据库...")

try:
    # 使用root用户连接MySQL
    connection = pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        password='123qwe',
        charset='utf8mb4'
    )
    
    print("✅ MySQL连接成功！")
    
    with connection.cursor() as cursor:
        # 创建数据库
        cursor.execute("CREATE DATABASE IF NOT EXISTS ai_sound CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("✅ 数据库ai_sound创建成功")
        
        # 创建用户
        cursor.execute("CREATE USER IF NOT EXISTS 'ai_sound_user'@'localhost' IDENTIFIED BY 'ai_sound_password'")
        print("✅ 用户ai_sound_user创建成功")
        
        # 授权
        cursor.execute("GRANT ALL PRIVILEGES ON ai_sound.* TO 'ai_sound_user'@'localhost'")
        cursor.execute("FLUSH PRIVILEGES")
        print("✅ 用户权限设置成功")
        
        # 切换到ai_sound数据库
        cursor.execute("USE ai_sound")
        print("✅ 切换到ai_sound数据库")
    
    connection.close()
    print("✅ MySQL数据库设置完成！")
    
except Exception as e:
    print(f"❌ MySQL设置失败: {e}")
    import traceback
    traceback.print_exc()
