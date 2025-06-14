"""
宸ュ叿鍑芥暟妯″潡
鎻愪緵閫氱敤鐨勬枃浠跺鐞嗐€佹棩蹇楄褰曘€佺粺璁℃洿鏂扮瓑鍔熻兘
"""

import os
import uuid
import json
import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session

from models import SystemLog, UsageStats

logger = logging.getLogger(__name__)

async def save_upload_file(
    file: UploadFile, 
    upload_dir: str, 
    allowed_extensions: List[str] = None,
    max_size_mb: int = 100
) -> Dict[str, Any]:
    """
    淇濆瓨涓婁紶鏂囦欢
    
    Args:
        file: FastAPI涓婁紶鏂囦欢瀵硅薄
        upload_dir: 涓婁紶鐩綍
        allowed_extensions: 鍏佽鐨勬枃浠舵墿灞曞悕鍒楄〃
        max_size_mb: 鏈€澶ф枃浠跺ぇ灏?MB)
    
    Returns:
        鍖呭惈鏂囦欢淇℃伅鐨勫瓧鍏?    """
    try:
        # 璇诲彇鏂囦欢鍐呭
        content = await file.read()
        
        # 楠岃瘉鏂囦欢澶у皬
        file_size_mb = len(content) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            raise ValueError(f"鏂囦欢澶у皬涓嶈兘瓒呰繃{max_size_mb}MB")
        
        # 楠岃瘉鏂囦欢鎵╁睍鍚?        if allowed_extensions:
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in allowed_extensions:
                raise ValueError(f"涓嶆敮鎸佺殑鏂囦欢鏍煎紡: {file_ext}")
        
        # 鐢熸垚鍞竴鏂囦欢鍚?        file_ext = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # 纭繚鐩綍瀛樺湪
        os.makedirs(upload_dir, exist_ok=True)
        
        # 淇濆瓨鏂囦欢
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return {
            "success": True,
            "filename": unique_filename,
            "original_name": file.filename,
            "file_path": file_path,
            "file_size_mb": round(file_size_mb, 2),
            "content_type": file.content_type
        }
        
    except Exception as e:
        logger.error(f"淇濆瓨鏂囦欢澶辫触: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

async def log_system_event(
    db: Session,
    level: str,
    message: str,
    module: str,
    details: Dict[str, Any] = None
):
    """
    璁板綍绯荤粺浜嬩欢鍒版暟鎹簱
    
    Args:
        db: 鏁版嵁搴撲細璇?        level: 鏃ュ織绾у埆 ('info', 'warn', 'error')
        message: 鏃ュ織娑堟伅
        module: 妯″潡鍚嶇О
        details: 璇︾粏淇℃伅瀛楀吀
    """
    try:
        # 妫€鏌ユ暟鎹簱浼氳瘽鐘舵€?        if not db or not hasattr(db, 'add'):
            logger.warning("鏃犳晥鐨勬暟鎹簱浼氳瘽锛岃烦杩囨棩蹇楄褰?)
            return
        
        # 鍒涘缓绯荤粺鏃ュ織璁板綍
        log_entry = SystemLog(
            level=level,
            message=message,
            module=module,
            details=json.dumps(details) if details else None,
            timestamp=datetime.utcnow()
        )
        
        # 鍙坊鍔犲埌浼氳瘽锛屼笉杩涜commit/rollback鎿嶄綔
        # 璁╄皟鐢ㄨ€呭喅瀹氫綍鏃舵彁浜や簨鍔?        db.add(log_entry)
        
        # 鍚屾椂璁板綍鍒板簲鐢ㄦ棩蹇?        if level == "info":
            logger.info(f"[{module}] {message}")
        elif level == "warn":
            logger.warning(f"[{module}] {message}")
        elif level == "error":
            logger.error(f"[{module}] {message}")
            
    except Exception as e:
        logger.error(f"璁板綍绯荤粺鏃ュ織澶辫触: {str(e)}")
        # 鏃ュ織璁板綍澶辫触涓嶅簲璇ュ奖鍝嶄富瑕佷笟鍔￠€昏緫
        pass

async def update_usage_stats(
    db: Session,
    success: bool = True,
    processing_time: float = 0.0,
    audio_generated: bool = False
):
    """
    鏇存柊浣跨敤缁熻
    
    Args:
        db: 鏁版嵁搴撲細璇?        success: 鏄惁鎴愬姛
        processing_time: 澶勭悊鏃堕棿(绉?
        audio_generated: 鏄惁鐢熸垚浜嗛煶棰戞枃浠?    """
    try:
        # 妫€鏌ユ暟鎹簱浼氳瘽鐘舵€?        if not db or not hasattr(db, 'query'):
            logger.warning("鏃犳晥鐨勬暟鎹簱浼氳瘽锛岃烦杩囩粺璁℃洿鏂?)
            return
        
        today = date.today().strftime("%Y-%m-%d")
        
        # 鏌ユ壘鎴栧垱寤轰粖澶╃殑缁熻璁板綍
        stats = db.query(UsageStats).filter(UsageStats.date == today).first()
        if not stats:
            stats = UsageStats(date=today)
            db.add(stats)
            # 浣跨敤flush鑰屼笉鏄痗ommit锛岃璋冪敤鑰呭喅瀹氫綍鏃舵彁浜?            db.flush()
        
        # 鏇存柊缁熻鏁版嵁锛岀‘淇濆鐞哊one鍊?        stats.total_requests = (stats.total_requests or 0) + 1
        
        if success:
            stats.successful_requests = (stats.successful_requests or 0) + 1
            stats.total_processing_time = (stats.total_processing_time or 0.0) + processing_time
        else:
            stats.failed_requests = (stats.failed_requests or 0) + 1
        
        if audio_generated:
            stats.audio_files_generated = (stats.audio_files_generated or 0) + 1
        
    except Exception as e:
        logger.error(f"鏇存柊浣跨敤缁熻澶辫触: {str(e)}")
        # 缁熻鏇存柊澶辫触涓嶅簲璇ュ奖鍝嶄富瑕佷笟鍔￠€昏緫
        pass

def validate_audio_file(file_path: str) -> Dict[str, Any]:
    """
    楠岃瘉闊抽鏂囦欢
    
    Args:
        file_path: 闊抽鏂囦欢璺緞
    
    Returns:
        楠岃瘉缁撴灉瀛楀吀
    """
    try:
        if not os.path.exists(file_path):
            return {"valid": False, "error": "鏂囦欢涓嶅瓨鍦?}
        
        # 妫€鏌ユ枃浠跺ぇ灏?        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return {"valid": False, "error": "鏂囦欢涓虹┖"}
        
        if file_size > 100 * 1024 * 1024:  # 100MB
            return {"valid": False, "error": "鏂囦欢杩囧ぇ"}
        
        # 妫€鏌ユ枃浠舵墿灞曞悕
        file_ext = os.path.splitext(file_path)[1].lower()
        supported_formats = ['.wav', '.mp3', '.flac', '.m4a', '.ogg']
        if file_ext not in supported_formats:
            return {"valid": False, "error": f"涓嶆敮鎸佺殑闊抽鏍煎紡: {file_ext}"}
        
        return {
            "valid": True,
            "file_size": file_size,
            "format": file_ext,
            "size_mb": round(file_size / (1024 * 1024), 2)
        }
        
    except Exception as e:
        return {"valid": False, "error": f"楠岃瘉澶辫触: {str(e)}"}

def get_audio_duration(file_path: str) -> Optional[float]:
    """
    鑾峰彇闊抽鏂囦欢鏃堕暱锛堢锛?    闇€瑕佸畨瑁?librosa 鎴?pydub
    
    Args:
        file_path: 闊抽鏂囦欢璺緞
    
    Returns:
        闊抽鏃堕暱(绉?锛屽け璐ヨ繑鍥濶one
    """
    # 娣诲姞鐜鍙橀噺鎺у埗寮€鍏?    if os.getenv('DISABLE_AUDIO_DURATION', 'false').lower() == 'true':
        return None
        
    try:
        # 灏濊瘯浣跨敤 librosa
        try:
            import librosa
            duration = librosa.get_duration(filename=file_path)
            return duration
        except ImportError:
            pass
        
        # 灏濊瘯浣跨敤 pydub
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(file_path)
            return len(audio) / 1000.0  # 杞崲涓虹
        except ImportError:
            pass
        
        # 鍙湪绗竴娆″鍏ュけ璐ユ椂鏄剧ず璀﹀憡
        if not hasattr(get_audio_duration, '_warning_shown'):
            logger.warning("鏃犳硶鑾峰彇闊抽鏃堕暱锛氭湭瀹夎 librosa 鎴?pydub")
            get_audio_duration._warning_shown = True
        return None
        
    except Exception as e:
        logger.error(f"鑾峰彇闊抽鏃堕暱澶辫触: {str(e)}")
        return None

def cleanup_old_files(directory: str, max_age_hours: int = 24) -> int:
    """
    娓呯悊杩囨湡鏂囦欢
    
    Args:
        directory: 鐩綍璺緞
        max_age_hours: 鏈€澶ф枃浠跺勾榫?灏忔椂)
    
    Returns:
        娓呯悊鐨勬枃浠舵暟閲?    """
    try:
        if not os.path.exists(directory):
            return 0
        
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        cleanup_count = 0
        
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getctime(file_path)
                if file_age > max_age_seconds:
                    try:
                        os.remove(file_path)
                        cleanup_count += 1
                        logger.info(f"娓呯悊杩囨湡鏂囦欢: {filename}")
                    except Exception as e:
                        logger.warning(f"娓呯悊鏂囦欢澶辫触 {filename}: {str(e)}")
        
        return cleanup_count
        
    except Exception as e:
        logger.error(f"娓呯悊鐩綍澶辫触 {directory}: {str(e)}")
        return 0

def format_file_size(size_bytes: int) -> str:
    """
    鏍煎紡鍖栨枃浠跺ぇ灏忔樉绀?    
    Args:
        size_bytes: 鏂囦欢澶у皬(瀛楄妭)
    
    Returns:
        鏍煎紡鍖栫殑鏂囦欢澶у皬瀛楃涓?    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def sanitize_filename(filename: str) -> str:
    """
    娓呯悊鏂囦欢鍚嶏紝绉婚櫎涓嶅畨鍏ㄥ瓧绗?    
    Args:
        filename: 鍘熷鏂囦欢鍚?    
    Returns:
        娓呯悊鍚庣殑鏂囦欢鍚?    """
    import re
    
    # 绉婚櫎璺緞鍒嗛殧绗﹀拰鍏朵粬涓嶅畨鍏ㄥ瓧绗?    unsafe_chars = r'[<>:"/\\|?*\x00-\x1f]'
    filename = re.sub(unsafe_chars, '_', filename)
    
    # 绉婚櫎寮€澶村拰缁撳熬鐨勭偣鍜岀┖鏍?    filename = filename.strip('. ')
    
    # 闄愬埗闀垮害
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[:100-len(ext)] + ext
    
    return filename or "unnamed"

def get_system_info() -> Dict[str, Any]:
    """
    鑾峰彇绯荤粺淇℃伅
    
    Returns:
        绯荤粺淇℃伅瀛楀吀
    """
    try:
        import psutil
        import platform
        
        # CPU淇℃伅
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # 鍐呭瓨淇℃伅
        memory = psutil.virtual_memory()
        
        # 纾佺洏淇℃伅
        disk = psutil.disk_usage('/')
        
        return {
            "platform": platform.system(),
            "architecture": platform.architecture()[0],
            "python_version": platform.python_version(),
            "cpu_count": cpu_count,
            "cpu_percent": cpu_percent,
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_percent": memory.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_percent": round((disk.used / disk.total) * 100, 1)
        }
        
    except ImportError:
        # 濡傛灉psutil鏈畨瑁咃紝杩斿洖鍩烘湰淇℃伅
        import platform
        return {
            "platform": platform.system(),
            "architecture": platform.architecture()[0],
            "python_version": platform.python_version(),
            "note": "瀹夎 psutil 浠ヨ幏鍙栨洿璇︾粏鐨勭郴缁熶俊鎭?
        }
    except Exception as e:
        logger.error(f"鑾峰彇绯荤粺淇℃伅澶辫触: {str(e)}")
        return {"error": str(e)}

def validate_parameters(
    time_step: int,
    p_weight: float,
    t_weight: float
) -> Dict[str, Any]:
    """
    楠岃瘉TTS鍙傛暟
    
    Args:
        time_step: 鏃堕棿姝ラ暱
        p_weight: P鏉冮噸
        t_weight: T鏉冮噸
    
    Returns:
        楠岃瘉缁撴灉瀛楀吀
    """
    errors = []
    
    # 楠岃瘉time_step
    if not isinstance(time_step, int) or time_step < 1 or time_step > 100:
        errors.append("time_step蹇呴』鏄?-100涔嬮棿鐨勬暣鏁?)
    
    # 楠岃瘉p_weight
    if not isinstance(p_weight, (int, float)) or p_weight < 0.1 or p_weight > 3.0:
        errors.append("p_weight蹇呴』鏄?.1-3.0涔嬮棿鐨勬暟鍊?)
    
    # 楠岃瘉t_weight
    if not isinstance(t_weight, (int, float)) or t_weight < 0.1 or t_weight > 3.0:
        errors.append("t_weight蹇呴』鏄?.1-3.0涔嬮棿鐨勬暟鍊?)
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    } 
