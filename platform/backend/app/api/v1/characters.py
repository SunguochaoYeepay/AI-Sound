from fastapi import APIRouter
from .characters.crud import router as crud_router
from .characters.batch import router as batch_router
from .characters.ai import router as ai_router
from .characters.matching import router as matching_router
import os

# 创建主路由
router = APIRouter(prefix="/characters", tags=["characters"])

# 包含子路由
router.include_router(crud_router, tags=["characters-crud"])
router.include_router(batch_router, prefix="/batch", tags=["characters-batch"])
router.include_router(ai_router, prefix="/ai", tags=["characters-ai"])
router.include_router(matching_router, prefix="/matching", tags=["characters-matching"])

# 路径配置（保留以确保向后兼容）
if os.path.exists("/.dockerenv"):
    # Docker环境
    VOICE_PROFILES_DIR = "/app/data/voice_profiles"
    AVATARS_DIR = "/app/data/avatars"
    TEMP_DIR = "/app/data/temp"
else:
    # 本地环境
    VOICE_PROFILES_DIR = "data/voice_profiles"
    AVATARS_DIR = "data/avatars"
    TEMP_DIR = "data/temp"

# 路径标准化函数（保留以确保向后兼容）
def normalize_path(path: str) -> str:
    """标准化文件路径"""
    if not path:
        return ""
    
    # 处理Windows路径分隔符
    normalized = path.replace('\\', '/').replace('//', '/')
    return normalized

# 检查并修复文件路径
def fix_voice_file_path(voice_profile):
    """检查并修复声音文件路径"""
    if not voice_profile.reference_audio_path:
        return None, "声音文件路径为空"
    
    # 标准化路径
    original_path = voice_profile.reference_audio_path
    normalized_path = normalize_path(original_path)
    
    # 如果是相对路径，转换为绝对路径
    if not os.path.isabs(normalized_path):
        if os.path.exists("/.dockerenv"):
            # Docker环境
            full_path = f"/app/{normalized_path}"
        else:
            # 本地环境
            full_path = normalized_path
    else:
        full_path = normalized_path
    
    # 检查文件是否存在
    if os.path.exists(full_path):
        return full_path, None
    
    # 如果文件不存在，尝试在voice_profiles目录中查找
    filename = os.path.basename(full_path)
    voice_dir = "/app/data/voice_profiles" if os.path.exists("/.dockerenv") else "data/voice_profiles"
    candidate_path = os.path.join(voice_dir, filename)
    
    if os.path.exists(candidate_path):
        return candidate_path, None
    
    # 返回错误信息，包含可用的文件列表
    available_files = []
    if os.path.exists(voice_dir):
        available_files = [f for f in os.listdir(voice_dir) if f.endswith('.wav')]
    
    error_msg = f"声音文件不存在: {filename}"
    if available_files:
        error_msg += f"\n可用的声音文件: {', '.join(available_files[:5])}"
        if len(available_files) > 5:
            error_msg += f"等共{len(available_files)}个文件"
    
    return None, error_msg

# 相似度计算函数（保留以确保向后兼容）
def calculate_similarity(str1: str, str2: str) -> float:
    """计算两个字符串的相似度"""
    if not str1 or not str2:
        return 0.0
    
    # 简单的字符串相似度计算
    str1, str2 = str1.lower(), str2.lower()
    
    # 完全匹配
    if str1 == str2:
        return 1.0
    
    # 包含关系
    if str1 in str2 or str2 in str1:
        return 0.8
    
    # 计算编辑距离
    def levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    max_len = max(len(str1), len(str2))
    distance = levenshtein_distance(str1, str2)
    similarity = 1 - (distance / max_len)
    
    return max(0.0, similarity)

# 默认头像生成函数（保留以确保向后兼容）
def _generate_default_avatar_svg(name: str = "角色", voice_type: str = "custom") -> str:
    """生成默认的SVG头像"""
    # 根据角色名称生成颜色
    import hashlib
    hash_object = hashlib.md5(name.encode())
    hex_dig = hash_object.hexdigest()
    
    # 从hash生成颜色
    r = int(hex_dig[0:2], 16)
    g = int(hex_dig[2:4], 16)
    b = int(hex_dig[4:6], 16)
    
    # 确保颜色不会太暗
    r = max(r, 100)
    g = max(g, 100)
    b = max(b, 100)
    
    color = f"rgb({r},{g},{b})"
    
    # 获取角色名称的第一个字符
    initial = name[0] if name else "角"
    
    svg_content = f'''
<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
    <circle cx="100" cy="100" r="90" fill="{color}" stroke="#fff" stroke-width="4"/>
    <text x="100" y="120" font-family="Arial, sans-serif" font-size="60" font-weight="bold" 
          text-anchor="middle" fill="white">{initial}</text>
</svg>
    '''.strip()
    
    return svg_content

# Pydantic模型（保留以确保向后兼容）
from pydantic import BaseModel
from typing import List

class CharacterMatchRequest(BaseModel):
    book_id: int
    chapter_id: int

class CharacterMatchResponse(BaseModel):
    matched_characters: List[dict]
    unmatched_characters: List[dict]
    total_count: int
    matched_count: int

class ApplyMatchesRequest(BaseModel):
    matches: List[dict]

class CharacterSyncRequest(BaseModel):
    book_id: int
    chapter_id: int