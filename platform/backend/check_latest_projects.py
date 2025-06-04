#!/usr/bin/env python3
"""
查看最新的项目
"""
import sys
sys.path.append('app')

from database import get_db
from models import NovelProject

def check_latest_projects():
    print("🔍 === 查看最新项目 ===")
    
    db = next(get_db())
    
    # 查询最新的5个项目
    projects = db.query(NovelProject).order_by(NovelProject.id.desc()).limit(10).all()
    
    print(f"📋 最新的 {len(projects)} 个项目:")
    
    for project in projects:
        print(f"\n项目 {project.id}:")
        print(f"  名称: {project.name}")
        print(f"  状态: {project.status}")
        print(f"  角色映射: {project.character_mapping}")
        print(f"  创建时间: {project.created_at}")

if __name__ == "__main__":
    check_latest_projects() 