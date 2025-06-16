"""
路径管理工具
自动适配本地和Docker环境的文件路径
"""

import os
import platform
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class PathManager:
    """路径管理器 - 自动适配不同运行环境"""
    
    def __init__(self):
        self.is_docker = self._detect_docker_environment()
        self.is_windows = platform.system() == 'Windows'
        self.base_paths = self._get_base_paths()
        
        logger.info(f"路径管理器初始化: Docker={self.is_docker}, Windows={self.is_windows}")
        logger.info(f"基础路径: {self.base_paths}")
    
    def _detect_docker_environment(self) -> bool:
        """检测是否运行在Docker容器中"""
        # 方法1: 检查 /.dockerenv 文件
        if os.path.exists('/.dockerenv'):
            return True
        
        # 方法2: 检查 /proc/1/cgroup
        try:
            with open('/proc/1/cgroup', 'r') as f:
                content = f.read()
                if 'docker' in content or 'containerd' in content:
                    return True
        except (FileNotFoundError, PermissionError):
            pass
        
        # 方法3: 检查环境变量
        if os.environ.get('DOCKER_CONTAINER') == 'true':
            return True
        
        # 方法4: 检查主机名
        hostname = os.environ.get('HOSTNAME', '')
        if len(hostname) == 12 and hostname.isalnum():  # Docker默认主机名格式
            return True
        
        return False
    
    def _get_base_paths(self) -> Dict[str, str]:
        """获取不同环境的基础路径配置"""
        if self.is_docker:
            return {
                'data': '/app/data',
                'storage': '/app/storage',
                'voice_profiles': '/app/data/voice_profiles',
                'audio': '/app/storage/audio',
                'books': '/app/storage/books',
                'uploads': '/app/storage/uploads',
                'temp': '/app/storage/temp'
            }
        else:
            # 本地环境 - 自动检测项目根目录
            project_root = self._find_project_root()
            return {
                'data': str(project_root / 'data'),
                'storage': str(project_root / 'storage'),
                'voice_profiles': str(project_root / 'data' / 'voice_profiles'),
                'audio': str(project_root / 'storage' / 'audio'),
                'books': str(project_root / 'storage' / 'books'),
                'uploads': str(project_root / 'storage' / 'uploads'),
                'temp': str(project_root / 'storage' / 'temp')
            }
    
    def _find_project_root(self) -> Path:
        """查找项目根目录"""
        current = Path.cwd()
        
        # 向上查找包含特定文件的目录
        markers = ['docker-compose.yml', 'README.md', '.git']
        
        for parent in [current] + list(current.parents):
            if any((parent / marker).exists() for marker in markers):
                logger.info(f"找到项目根目录: {parent}")
                return parent
        
        # 如果找不到，使用当前目录
        logger.warning(f"未找到项目根目录，使用当前目录: {current}")
        return current
    
    def normalize_path(self, path: str) -> Optional[str]:
        """标准化路径 - 自动适配当前环境"""
        if not path:
            return None
        
        # 已经是当前环境的路径
        if os.path.exists(path):
            return os.path.abspath(path)
        
        # 尝试路径转换
        converted_path = self._convert_path(path)
        if converted_path and os.path.exists(converted_path):
            return os.path.abspath(converted_path)
        
        # 尝试相对路径解析
        relative_path = self._resolve_relative_path(path)
        if relative_path and os.path.exists(relative_path):
            return os.path.abspath(relative_path)
        
        logger.warning(f"无法解析路径: {path}")
        return None
    
    def _convert_path(self, path: str) -> Optional[str]:
        """在不同环境间转换路径"""
        # 标准化路径分隔符
        normalized_path = path.replace('\\', '/')
        
        if self.is_docker:
            # 当前是Docker，转换Windows路径
            if normalized_path.startswith('D:/AI-Sound/'):
                return normalized_path.replace('D:/AI-Sound/', '/app/')
            elif normalized_path.startswith('data/'):
                # 相对路径转换
                return '/app/' + normalized_path
        else:
            # 当前是本地，转换Docker路径或相对路径
            if normalized_path.startswith('/app/'):
                # Docker路径转本地路径
                relative = normalized_path[5:]  # 去掉 '/app/'
                project_root = str(self._find_project_root())
                local_path = os.path.join(project_root, relative)
                return local_path.replace('/', os.sep)
            elif normalized_path.startswith('data/'):
                # 相对路径转本地绝对路径
                project_root = str(self._find_project_root())
                local_path = os.path.join(project_root, normalized_path)
                return local_path.replace('/', os.sep)
        
        return None
    
    def _resolve_relative_path(self, path: str) -> Optional[str]:
        """解析相对路径"""
        # 提取文件名
        filename = os.path.basename(path)
        
        # 在voice_profiles目录中查找
        voice_profiles_dir = self.base_paths['voice_profiles']
        if os.path.exists(voice_profiles_dir):
            candidate = os.path.join(voice_profiles_dir, filename)
            if os.path.exists(candidate):
                return candidate
        
        # 在其他目录中查找
        for dir_type, dir_path in self.base_paths.items():
            if os.path.exists(dir_path):
                candidate = os.path.join(dir_path, filename)
                if os.path.exists(candidate):
                    return candidate
        
        return None
    
    def get_storage_path(self, path_type: str, filename: str = None) -> str:
        """获取存储路径"""
        base_path = self.base_paths.get(path_type)
        if not base_path:
            raise ValueError(f"未知的路径类型: {path_type}")
        
        # 确保目录存在
        os.makedirs(base_path, exist_ok=True)
        
        if filename:
            return os.path.join(base_path, filename)
        return base_path
    
    def validate_voice_profile_paths(self, voice_profile) -> Dict[str, Any]:
        """验证声音档案的所有路径"""
        result = {
            'valid': True,
            'issues': [],
            'fixed_paths': {}
        }
        
        path_fields = ['reference_audio_path', 'latent_file_path', 'sample_audio_path']
        
        for field in path_fields:
            original_path = getattr(voice_profile, field, None)
            if not original_path:
                continue
            
            normalized_path = self.normalize_path(original_path)
            
            if normalized_path:
                if normalized_path != original_path:
                    result['fixed_paths'][field] = {
                        'old': original_path,
                        'new': normalized_path
                    }
            else:
                result['valid'] = False
                result['issues'].append(f"{field}: 文件不存在 - {original_path}")
        
        return result
    
    def auto_fix_voice_profile_paths(self, db_session) -> Dict[str, Any]:
        """自动修复所有声音档案的路径"""
        from app.models import VoiceProfile
        
        result = {
            'total': 0,
            'fixed': 0,
            'failed': [],
            'details': []
        }
        
        voices = db_session.query(VoiceProfile).all()
        result['total'] = len(voices)
        
        for voice in voices:
            voice_result = self.validate_voice_profile_paths(voice)
            
            if voice_result['fixed_paths']:
                # 应用修复
                for field, paths in voice_result['fixed_paths'].items():
                    setattr(voice, field, paths['new'])
                    logger.info(f"修复声音档案 {voice.name} 的 {field}: {paths['old']} -> {paths['new']}")
                
                result['fixed'] += 1
                result['details'].append({
                    'voice_id': voice.id,
                    'voice_name': voice.name,
                    'fixed_paths': voice_result['fixed_paths']
                })
            
            if voice_result['issues']:
                result['failed'].append({
                    'voice_id': voice.id,
                    'voice_name': voice.name,
                    'issues': voice_result['issues']
                })
        
        if result['fixed'] > 0:
            try:
                db_session.commit()
                logger.info(f"成功修复 {result['fixed']} 个声音档案的路径")
            except Exception as e:
                db_session.rollback()
                logger.error(f"提交路径修复失败: {e}")
                raise
        
        return result


# 全局路径管理器实例
_path_manager = None

def get_path_manager() -> PathManager:
    """获取路径管理器单例"""
    global _path_manager
    if _path_manager is None:
        _path_manager = PathManager()
    return _path_manager


def normalize_path(path: str) -> Optional[str]:
    """便捷函数：标准化路径"""
    return get_path_manager().normalize_path(path)


def get_storage_path(path_type: str, filename: str = None) -> str:
    """便捷函数：获取存储路径"""
    return get_path_manager().get_storage_path(path_type, filename)


def validate_environment() -> Dict[str, Any]:
    """验证当前环境配置"""
    pm = get_path_manager()
    
    result = {
        'environment': 'docker' if pm.is_docker else 'local',
        'platform': platform.system(),
        'base_paths': pm.base_paths,
        'path_checks': {}
    }
    
    # 检查关键目录
    for path_type, path in pm.base_paths.items():
        result['path_checks'][path_type] = {
            'path': path,
            'exists': os.path.exists(path),
            'writable': os.access(path, os.W_OK) if os.path.exists(path) else False
        }
    
    return result 