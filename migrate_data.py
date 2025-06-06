#!/usr/bin/env python3
"""
数据迁移脚本：从SQLite迁移到PostgreSQL
"""
import sqlite3
import psycopg2
from datetime import datetime
import json

def check_sqlite_data():
    """检查SQLite数据"""
    print("🔍 === 检查SQLite数据 ===")
    
    sqlite_conn = sqlite3.connect('data/database.db')
    cursor = sqlite_conn.cursor()
    
    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"📋 SQLite表: {[t[0] for t in tables]}")
    
    for table_name in [t[0] for t in tables]:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"📊 {table_name}: {count} 条记录")
        
        if count > 0:
            # 显示前几条数据
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            rows = cursor.fetchall()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            print(f"📋 {table_name} 字段: {columns}")
            for i, row in enumerate(rows[:2]):
                print(f"   示例{i+1}: {dict(zip(columns, row))}")
            print("---")
    
    sqlite_conn.close()

def migrate_data():
    """迁移数据"""
    print("\n🚀 === 开始数据迁移 ===")
    
    # 连接SQLite
    sqlite_conn = sqlite3.connect('data/database.db')
    sqlite_cursor = sqlite_conn.cursor()
    
    # 连接PostgreSQL
    try:
        pg_conn = psycopg2.connect(
            host="localhost",
            port="5432", 
            database="ai_sound",
            user="ai_sound_user",
            password="ai_sound_password"
        )
        pg_cursor = pg_conn.cursor()
        print("✅ PostgreSQL连接成功")
    except Exception as e:
        print(f"❌ PostgreSQL连接失败: {e}")
        print("💡 尝试通过Docker容器连接...")
        return migrate_via_docker()
    
    # 迁移voice_profiles表
    print("\n📁 迁移voice_profiles...")
    sqlite_cursor.execute("SELECT * FROM voice_profiles")
    voices = sqlite_cursor.fetchall()
    
    if voices:
        sqlite_cursor.execute("PRAGMA table_info(voice_profiles)")
        columns = [col[1] for col in sqlite_cursor.fetchall()]
        
        for voice in voices:
            voice_dict = dict(zip(columns, voice))
            print(f"   迁移声音: {voice_dict.get('name', 'Unknown')}")
            
            # 插入PostgreSQL
            placeholders = ', '.join(['%s'] * len(voice_dict))
            columns_str = ', '.join(voice_dict.keys())
            values = list(voice_dict.values())
            
            try:
                pg_cursor.execute(f"""
                    INSERT INTO voice_profiles ({columns_str}) 
                    VALUES ({placeholders})
                    ON CONFLICT (name) DO NOTHING
                """, values)
            except Exception as e:
                print(f"   ⚠️ 插入失败: {e}")
    
    # 迁移novel_projects表
    print("\n📚 迁移novel_projects...")
    sqlite_cursor.execute("SELECT * FROM novel_projects")
    projects = sqlite_cursor.fetchall()
    
    if projects:
        sqlite_cursor.execute("PRAGMA table_info(novel_projects)")
        columns = [col[1] for col in sqlite_cursor.fetchall()]
        
        for project in projects:
            project_dict = dict(zip(columns, project))
            print(f"   迁移项目: {project_dict.get('name', 'Unknown')}")
            
            # 处理JSON字段
            if 'character_mapping' in project_dict and project_dict['character_mapping']:
                try:
                    json.loads(project_dict['character_mapping'])
                except:
                    project_dict['character_mapping'] = '{}'
            
            placeholders = ', '.join(['%s'] * len(project_dict))
            columns_str = ', '.join(project_dict.keys())
            values = list(project_dict.values())
            
            try:
                pg_cursor.execute(f"""
                    INSERT INTO novel_projects ({columns_str}) 
                    VALUES ({placeholders})
                    ON CONFLICT (id) DO NOTHING
                """, values)
            except Exception as e:
                print(f"   ⚠️ 插入失败: {e}")
    
    # 提交事务
    try:
        pg_conn.commit()
        print("✅ 数据迁移完成!")
    except Exception as e:
        print(f"❌ 提交失败: {e}")
        pg_conn.rollback()
    
    sqlite_conn.close()
    pg_conn.close()

def migrate_via_docker():
    """通过Docker容器迁移数据"""
    print("🐳 通过Docker容器迁移数据...")
    
    # 这里生成SQL脚本，然后在容器内执行
    sqlite_conn = sqlite3.connect('data/database.db')
    cursor = sqlite_conn.cursor()
    
    # 生成迁移SQL
    with open('migration.sql', 'w', encoding='utf-8') as f:
        f.write("-- AI-Sound数据迁移脚本\n")
        f.write("-- 从SQLite迁移到PostgreSQL\n\n")
        
        # 迁移voice_profiles
        cursor.execute("SELECT * FROM voice_profiles")
        voices = cursor.fetchall()
        if voices:
            cursor.execute("PRAGMA table_info(voice_profiles)")
            columns = [col[1] for col in cursor.fetchall()]
            
            f.write("-- 迁移声音档案\n")
            for voice in voices:
                voice_dict = dict(zip(columns, voice))
                
                # 处理NULL和特殊字符
                values = []
                for key, value in voice_dict.items():
                    if value is None:
                        values.append('NULL')
                    elif isinstance(value, str):
                        # 转义单引号
                        escaped_value = value.replace("'", "''")
                        values.append(f"'{escaped_value}'")
                    else:
                        values.append(str(value))
                
                columns_str = ', '.join(voice_dict.keys())
                values_str = ', '.join(values)
                
                f.write(f"""INSERT INTO voice_profiles ({columns_str}) 
VALUES ({values_str}) ON CONFLICT (name) DO NOTHING;\n""")
        
        # 迁移novel_projects
        cursor.execute("SELECT * FROM novel_projects")
        projects = cursor.fetchall()
        if projects:
            cursor.execute("PRAGMA table_info(novel_projects)")
            columns = [col[1] for col in cursor.fetchall()]
            
            f.write("\n-- 迁移小说项目\n")
            for project in projects:
                project_dict = dict(zip(columns, project))
                
                values = []
                for key, value in project_dict.items():
                    if value is None:
                        values.append('NULL')
                    elif isinstance(value, str):
                        escaped_value = value.replace("'", "''")
                        values.append(f"'{escaped_value}'")
                    else:
                        values.append(str(value))
                
                columns_str = ', '.join(project_dict.keys())
                values_str = ', '.join(values)
                
                f.write(f"""INSERT INTO novel_projects ({columns_str}) 
VALUES ({values_str}) ON CONFLICT (id) DO NOTHING;\n""")
    
    sqlite_conn.close()
    print("✅ 生成migration.sql文件完成")
    return True

if __name__ == "__main__":
    check_sqlite_data()
    migrate_via_docker()