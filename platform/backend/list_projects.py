#!/usr/bin/env python3
import sys
sys.path.append('app')

from database import get_db
from models import NovelProject

try:
    db = next(get_db())
    projects = db.query(NovelProject).order_by(NovelProject.id.desc()).limit(5).all()
    print("最新5个项目:")
    for p in projects:
        print(f'项目ID: {p.id}, 名称: {p.name}, 状态: {p.status}')
    db.close()
except Exception as e:
    print(f"错误: {e}") 