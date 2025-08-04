from app.database import get_db
from app.models.character import Character

# 使用现有的数据库连接
db = next(get_db())

try:
    # 查询所有角色
    chars = db.query(Character).all()
    print(f'Total characters: {len(chars)}')
    
    # 检查有头像的角色
    has_avatar = [c for c in chars if c.avatar_path and c.avatar_path.strip()]
    print(f'Characters with avatar: {len(has_avatar)}')
    
    for c in has_avatar[:5]:
        print(f'  - {c.name}: {c.avatar_path}')
    
    # 检查没有头像的角色
    no_avatar = [c for c in chars if not c.avatar_path or not c.avatar_path.strip()]
    print(f'Characters without avatar: {len(no_avatar)}')
    
    # 显示前几个没有头像的角色
    for c in no_avatar[:5]:
        print(f'  - {c.name}: {c.avatar_path}')
        
finally:
    db.close()