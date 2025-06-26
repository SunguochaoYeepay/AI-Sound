"""
权限常量定义
"""

class PERMISSIONS:
    """权限常量类"""
    
    # 用户管理权限
    USER_VIEW = "user.view"
    USER_CREATE = "user.create"
    USER_EDIT = "user.edit"
    USER_DELETE = "user.delete"
    
    # 角色管理权限
    ROLE_VIEW = "role.view"
    ROLE_CREATE = "role.create"
    ROLE_EDIT = "role.edit"
    ROLE_DELETE = "role.delete"
    
    # TTS服务权限
    TTS_BASIC = "tts.basic"
    TTS_ADVANCED = "tts.advanced"
    TTS_CLONE = "tts.clone"
    
    # 项目管理权限
    PROJECT_VIEW = "project.view"
    PROJECT_CREATE = "project.create"
    PROJECT_EDIT = "project.edit"
    PROJECT_DELETE = "project.delete"
    
    # 书籍管理权限
    BOOK_VIEW = "book.view"
    BOOK_CREATE = "book.create"
    BOOK_EDIT = "book.edit"
    BOOK_DELETE = "book.delete"
    
    # 系统管理权限
    SYSTEM_SETTINGS = "system.settings"
    SYSTEM_LOGS = "system.logs"
    SYSTEM_BACKUP = "system.backup"
    SYSTEM_MONITOR = "system.monitor"


# 权限分组定义
PERMISSION_GROUPS = {
    "用户管理": [
        PERMISSIONS.USER_VIEW,
        PERMISSIONS.USER_CREATE,
        PERMISSIONS.USER_EDIT,
        PERMISSIONS.USER_DELETE,
    ],
    "角色管理": [
        PERMISSIONS.ROLE_VIEW,
        PERMISSIONS.ROLE_CREATE,
        PERMISSIONS.ROLE_EDIT,
        PERMISSIONS.ROLE_DELETE,
    ],
    "TTS服务": [
        PERMISSIONS.TTS_BASIC,
        PERMISSIONS.TTS_ADVANCED,
        PERMISSIONS.TTS_CLONE,
    ],
    "项目管理": [
        PERMISSIONS.PROJECT_VIEW,
        PERMISSIONS.PROJECT_CREATE,
        PERMISSIONS.PROJECT_EDIT,
        PERMISSIONS.PROJECT_DELETE,
    ],
    "书籍管理": [
        PERMISSIONS.BOOK_VIEW,
        PERMISSIONS.BOOK_CREATE,
        PERMISSIONS.BOOK_EDIT,
        PERMISSIONS.BOOK_DELETE,
    ],
    "系统管理": [
        PERMISSIONS.SYSTEM_SETTINGS,
        PERMISSIONS.SYSTEM_LOGS,
        PERMISSIONS.SYSTEM_BACKUP,
        PERMISSIONS.SYSTEM_MONITOR,
    ],
}

# 默认角色权限映射
DEFAULT_ROLE_PERMISSIONS = {
    "admin": [
        # 管理员拥有所有权限
        PERMISSIONS.USER_VIEW,
        PERMISSIONS.USER_CREATE,
        PERMISSIONS.USER_EDIT,
        PERMISSIONS.USER_DELETE,
        PERMISSIONS.ROLE_VIEW,
        PERMISSIONS.ROLE_CREATE,
        PERMISSIONS.ROLE_EDIT,
        PERMISSIONS.ROLE_DELETE,
        PERMISSIONS.TTS_BASIC,
        PERMISSIONS.TTS_ADVANCED,
        PERMISSIONS.TTS_CLONE,
        PERMISSIONS.PROJECT_VIEW,
        PERMISSIONS.PROJECT_CREATE,
        PERMISSIONS.PROJECT_EDIT,
        PERMISSIONS.PROJECT_DELETE,
        PERMISSIONS.BOOK_VIEW,
        PERMISSIONS.BOOK_CREATE,
        PERMISSIONS.BOOK_EDIT,
        PERMISSIONS.BOOK_DELETE,
        PERMISSIONS.SYSTEM_SETTINGS,
        PERMISSIONS.SYSTEM_LOGS,
        PERMISSIONS.SYSTEM_BACKUP,
        PERMISSIONS.SYSTEM_MONITOR,
    ],
    "user": [
        # 普通用户的基础权限
        PERMISSIONS.TTS_BASIC,
        PERMISSIONS.PROJECT_VIEW,
        PERMISSIONS.PROJECT_CREATE,
        PERMISSIONS.PROJECT_EDIT,
        PERMISSIONS.BOOK_VIEW,
        PERMISSIONS.BOOK_CREATE,
        PERMISSIONS.BOOK_EDIT,
    ],
}

# 权限描述映射
PERMISSION_DESCRIPTIONS = {
    PERMISSIONS.USER_VIEW: "查看用户列表和详情",
    PERMISSIONS.USER_CREATE: "创建新用户账户",
    PERMISSIONS.USER_EDIT: "编辑用户信息和设置",
    PERMISSIONS.USER_DELETE: "删除用户账户",
    
    PERMISSIONS.ROLE_VIEW: "查看角色列表和详情",
    PERMISSIONS.ROLE_CREATE: "创建新角色",
    PERMISSIONS.ROLE_EDIT: "编辑角色信息和权限",
    PERMISSIONS.ROLE_DELETE: "删除角色",
    
    PERMISSIONS.TTS_BASIC: "使用基础TTS合成功能",
    PERMISSIONS.TTS_ADVANCED: "使用高级TTS功能",
    PERMISSIONS.TTS_CLONE: "使用声音克隆功能",
    
    PERMISSIONS.PROJECT_VIEW: "查看项目列表和详情",
    PERMISSIONS.PROJECT_CREATE: "创建新项目",
    PERMISSIONS.PROJECT_EDIT: "编辑项目设置",
    PERMISSIONS.PROJECT_DELETE: "删除项目",
    
    PERMISSIONS.BOOK_VIEW: "查看书籍列表和内容",
    PERMISSIONS.BOOK_CREATE: "上传和创建书籍",
    PERMISSIONS.BOOK_EDIT: "编辑书籍信息",
    PERMISSIONS.BOOK_DELETE: "删除书籍",
    
    PERMISSIONS.SYSTEM_SETTINGS: "修改系统设置",
    PERMISSIONS.SYSTEM_LOGS: "查看系统日志",
    PERMISSIONS.SYSTEM_BACKUP: "执行系统备份和恢复",
    PERMISSIONS.SYSTEM_MONITOR: "查看系统监控信息",
}