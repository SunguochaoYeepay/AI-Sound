"""
环境音文件服务
统一处理文件相关操作（预览、下载、播放）
"""

import os
import logging
from typing import Dict, Any
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)


class EnvironmentFileService:
    """环境音文件服务"""
    
    @staticmethod
    def create_file_response(
        file_path: str,
        filename: str,
        action: str = "preview"  # preview, download, play
    ) -> FileResponse:
        """创建文件响应"""
        if not os.path.exists(file_path):
            raise ValueError("文件不存在")
        
        headers = {}
        if action == "download":
            headers["Content-Disposition"] = f"attachment; filename={filename}"
        elif action == "play":
            headers["Content-Disposition"] = "inline"
        
        return FileResponse(
            path=file_path,
            media_type="audio/wav",
            filename=filename,
            headers=headers if headers else None
        )
    
    @staticmethod
    def generate_safe_filename(track: Dict[str, Any], project_id: int, track_index: int) -> str:
        """生成安全的文件名"""
        keywords = track.get('environment_keywords', [])
        keyword_name = keywords[0] if keywords and len(keywords) > 0 else 'environment'
        
        # 中文关键词映射
        keyword_map = {
            '娇喝声': 'shout',
            '脚步声': 'footsteps', 
            '开门声': 'door_open',
            '驼铃声': 'camel_bell'
        }
        
        safe_keyword = keyword_map.get(keyword_name, 'environment')
        return f"{safe_keyword}_{project_id}_{track_index}.wav"
