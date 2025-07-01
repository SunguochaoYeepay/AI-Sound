#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的日志系统配置
提供文件日志、控制台日志、模块化配置和日志轮转
"""

import os
import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any

# 数据库日志处理器
class DatabaseLogHandler(logging.Handler):
    """数据库日志处理器 - 将日志写入SystemLog表"""
    
    def __init__(self):
        super().__init__()
        self._session = None
        
    def get_session(self):
        """获取数据库会话（延迟初始化）"""
        if self._session is None:
            try:
                from ..database import SessionLocal
                self._session = SessionLocal()
            except Exception:
                # 如果数据库还未初始化，跳过数据库日志
                return None
        return self._session
    
    def emit(self, record):
        """发送日志记录到数据库"""
        try:
            session = self.get_session()
            if session is None:
                return
                
            from ..models.system import SystemLog, LogLevel, LogModule
            
            # 映射日志级别
            level_mapping = {
                'DEBUG': LogLevel.DEBUG,
                'INFO': LogLevel.INFO,
                'WARNING': LogLevel.WARNING,
                'ERROR': LogLevel.ERROR,
                'CRITICAL': LogLevel.CRITICAL
            }
            
            # 映射模块名称
            module_mapping = {
                'background_music': LogModule.BACKGROUND_MUSIC,
                'music_generation': LogModule.MUSIC_GENERATION,
                'intelligent_analysis': LogModule.INTELLIGENT_ANALYSIS,
                'tts_voice': LogModule.TTS_VOICE,
                'environment_sounds': LogModule.ENVIRONMENT_SOUNDS,
                'audio_processing': LogModule.AUDIO_PROCESSING,
                'api_requests': LogModule.API_REQUESTS,
                'database': LogModule.DATABASE_OPS,
                'websocket': LogModule.WEBSOCKET_COMM,
                'main': LogModule.SYSTEM,
            }
            
            # 确定模块类型
            logger_name = record.name.lower()
            module = LogModule.SYSTEM  # 默认值
            
            for key, mod in module_mapping.items():
                if key in logger_name:
                    module = mod
                    break
            
            # 创建日志记录
            log_entry = SystemLog(
                level=level_mapping.get(record.levelname, LogLevel.INFO),
                module=module,
                message=record.getMessage(),
                source_file=record.pathname,
                source_line=record.lineno,
                function=record.funcName
            )
            
            session.add(log_entry)
            session.commit()
            
        except Exception as e:
            # 数据库日志失败不应该影响应用运行
            pass
    
    def close(self):
        """关闭处理器"""
        if self._session:
            self._session.close()
        super().close()

class LoggingConfig:
    """日志系统配置管理器"""
    
    def __init__(self):
        self.log_dir = Path("data/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 日志格式
        self.detailed_format = '[%(asctime)s] %(name)s.%(funcName)s:%(lineno)d - %(levelname)s - %(message)s'
        self.simple_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # 文件配置
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.backup_count = 10
        
    def setup_logging(self, level: str = "INFO") -> None:
        """设置完整的日志系统"""
        
        # 清除现有的处理器
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 设置根日志级别
        root_logger.setLevel(getattr(logging, level.upper()))
        
        # 1. 主应用日志文件（详细格式）
        main_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "ai_sound_main.log",
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        main_handler.setLevel(logging.DEBUG)
        main_handler.setFormatter(logging.Formatter(self.detailed_format))
        root_logger.addHandler(main_handler)
        
        # 2. 错误日志文件（只记录错误和警告）
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "ai_sound_errors.log",
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.WARNING)
        error_handler.setFormatter(logging.Formatter(self.detailed_format))
        root_logger.addHandler(error_handler)
        
        # 3. 控制台输出（简化格式）
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(self.simple_format))
        root_logger.addHandler(console_handler)
        
        # 4. 数据库日志处理器（WARNING及以上级别）
        try:
            db_handler = DatabaseLogHandler()
            db_handler.setLevel(logging.WARNING)  # 只记录重要日志到数据库
            root_logger.addHandler(db_handler)
            logging.info("📊 数据库日志处理器已启用")
        except Exception as e:
            logging.warning(f"⚠️ 数据库日志处理器启用失败: {e}")
        
        # 5. 设置模块专用日志
        self._setup_module_loggers()
        
        logging.info("✅ 完整日志系统初始化完成")
        logging.info(f"📁 日志目录: {self.log_dir.absolute()}")
        logging.info(f"📝 主日志: ai_sound_main.log")
        logging.info(f"🚨 错误日志: ai_sound_errors.log")
    
    def _setup_module_loggers(self) -> None:
        """设置各模块专用日志"""
        
        # 背景音乐模块日志
        self._create_module_logger(
            "app.services.background_music_service",
            "background_music.log",
            logging.DEBUG
        )
        
        self._create_module_logger(
            "app.services.background_music_generation_service", 
            "background_music.log",
            logging.DEBUG
        )
        
        self._create_module_logger(
            "app.api.v1.background_music",
            "background_music.log", 
            logging.DEBUG
        )
        
        # 音乐生成模块日志
        self._create_module_logger(
            "app.services.song_generation_service",
            "music_generation.log",
            logging.DEBUG
        )
        
        self._create_module_logger(
            "app.services.music_orchestrator",
            "music_generation.log",
            logging.DEBUG
        )
        
        self._create_module_logger(
            "app.api.v1.music_generation",
            "music_generation.log",
            logging.DEBUG
        )
        
        self._create_module_logger(
            "app.api.v1.music_generation_async",
            "music_generation.log",
            logging.DEBUG
        )
        
        self._create_module_logger(
            "app.clients.songgeneration_engine",
            "music_generation.log",
            logging.DEBUG
        )
        
        # TTS和语音模块日志
        self._create_module_logger(
            "app.tts_client",
            "tts_voice.log",
            logging.DEBUG
        )
        
        self._create_module_logger(
            "app.clients.tts_client",
            "tts_voice.log",
            logging.DEBUG
        )
        
        self._create_module_logger(
            "app.api.v1.characters",
            "tts_voice.log",
            logging.DEBUG
        )
        
        # 环境音模块日志
        self._create_module_logger(
            "app.services.environment_generation_service",
            "environment_sounds.log",
            logging.DEBUG
        )
        
        self._create_module_logger(
            "app.services.tangoflux_environment_generator",
            "environment_sounds.log",
            logging.DEBUG
        )
        
        self._create_module_logger(
            "app.clients.tangoflux_client",
            "environment_sounds.log",
            logging.DEBUG
        )
        
        self._create_module_logger(
            "app.api.v1.environment_generation",
            "environment_sounds.log",
            logging.DEBUG
        )
        
        # 智能分析模块日志
        self._create_module_logger(
            "app.services.llm_scene_analyzer",
            "intelligent_analysis.log",
            logging.DEBUG
        )
        
        self._create_module_logger(
            "app.services.intelligent_scene_analyzer",
            "intelligent_analysis.log",
            logging.DEBUG
        )
        
        self._create_module_logger(
            "app.services.chapter_analysis_service",
            "intelligent_analysis.log",
            logging.DEBUG
        )
        
        self._create_module_logger(
            "app.api.v1.intelligent_analysis",
            "intelligent_analysis.log",
            logging.DEBUG
        )
        
        # 音频处理模块日志
        self._create_module_logger(
            "app.services.audio_editor_service",
            "audio_processing.log",
            logging.DEBUG
        )
        
        self._create_module_logger(
            "app.services.audio_sync_service",
            "audio_processing.log",
            logging.DEBUG
        )
        
        self._create_module_logger(
            "app.clients.audio_processor",
            "audio_processing.log",
            logging.DEBUG
        )
        
        self._create_module_logger(
            "app.api.v1.audio_editor",
            "audio_processing.log",
            logging.DEBUG
        )
        
        # API和中间件日志
        self._create_module_logger(
            "app.middleware.logging_middleware",
            "api_requests.log",
            logging.INFO
        )
        
        self._create_module_logger(
            "app.api.v1.system",
            "api_requests.log",
            logging.INFO
        )
        
        # 数据库日志
        self._create_module_logger(
            "app.database",
            "database.log",
            logging.WARNING  # 只记录重要信息
        )
        
        # WebSocket日志
        self._create_module_logger(
            "app.websocket.manager",
            "websocket.log",
            logging.DEBUG
        )
        
        # 🔇 静音吵闹的开发工具日志
        self._silence_noisy_loggers()
        
        logging.info("📋 模块专用日志配置完成")
    
    def _silence_noisy_loggers(self) -> None:
        """静音吵闹的开发工具日志"""
        # 文件监控日志太吵闹，只显示WARNING及以上
        logging.getLogger("watchfiles.main").setLevel(logging.WARNING)
        logging.getLogger("watchfiles").setLevel(logging.WARNING)
        
        # Uvicorn访问日志调整
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        
        # APScheduler日志调整（如果使用）
        logging.getLogger("apscheduler").setLevel(logging.WARNING)
        
        logging.info("🔇 已静音吵闹的开发工具日志")
    
    def _create_module_logger(self, logger_name: str, log_file: str, level: int) -> None:
        """创建模块专用日志记录器"""
        
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        
        # 避免重复添加处理器
        if not any(isinstance(h, logging.handlers.RotatingFileHandler) 
                  and str(h.baseFilename).endswith(log_file) 
                  for h in logger.handlers):
            
            # 1. 文件处理器
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / log_file,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(logging.Formatter(self.detailed_format))
            logger.addHandler(file_handler)
            
            # 2. 数据库处理器（INFO及以上级别）
            try:
                db_handler = DatabaseLogHandler()
                db_handler.setLevel(logging.INFO)  # 模块日志记录INFO及以上级别
                logger.addHandler(db_handler)
            except Exception:
                # 数据库处理器失败不影响文件日志
                pass
    
    def get_log_files_info(self) -> Dict[str, Any]:
        """获取日志文件信息"""
        log_files = []
        
        for log_file in self.log_dir.glob("*.log"):
            try:
                stat = log_file.stat()
                log_files.append({
                    "name": log_file.name,
                    "size": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "modified": stat.st_mtime
                })
            except Exception:
                continue
        
        return {
            "log_directory": str(self.log_dir.absolute()),
            "total_files": len(log_files),
            "log_files": sorted(log_files, key=lambda x: x["modified"], reverse=True)
        }
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """清理旧日志文件"""
        import time
        
        current_time = time.time()
        cutoff_time = current_time - (days * 24 * 60 * 60)
        
        cleaned_count = 0
        for log_file in self.log_dir.glob("*.log.*"):  # 备份日志文件
            try:
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    cleaned_count += 1
            except Exception:
                continue
        
        return cleaned_count


# 全局日志配置实例
logging_config = LoggingConfig()

def init_logging(level: str = "INFO") -> None:
    """初始化日志系统"""
    logging_config.setup_logging(level)

def get_logging_info() -> Dict[str, Any]:
    """获取日志系统信息"""
    return logging_config.get_log_files_info() 