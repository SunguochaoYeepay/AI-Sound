"""
声纹特征提取与管理模块

负责从音频提取声纹特征、保存和管理声纹特征文件、提供元数据管理功能。
这些特征可用于MegaTTS3的个性化语音合成。
"""

import os
import sys
import logging
import numpy as np
import torch
import json
import shutil
import librosa
import hashlib
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("tts.voice_feature")

# 查找MegaTTS3路径
def find_megatts3_path():
    """
    查找MegaTTS3模块路径
    
    Returns:
        Path: MegaTTS3模块路径
    """
    megatts_paths = [
        Path(__file__).resolve().parent.parent.parent.parent / "MegaTTS3",  # 服务内相对路径
        Path("/app/MegaTTS3"),  # Docker容器内路径
        Path(__file__).resolve().parent.parent.parent.parent.parent / "MegaTTS3",  # 更上层目录
        Path("D:/AI-Sound/MegaTTS3"),  # 本地开发路径
    ]
    
    for path in megatts_paths:
        if path.exists():
            return path
    
    return None

# 尝试导入MegaTTS3模块
megatts_path = find_megatts3_path()
if megatts_path:
    logger.info(f"找到MegaTTS3路径: {megatts_path}")
    sys.path.insert(0, str(megatts_path))

# 默认配置
DEFAULT_SAMPLE_RATE = 24000
DEFAULT_MIN_AUDIO_LENGTH = 3.0  # 秒
DEFAULT_MAX_AUDIO_LENGTH = 10.0  # 秒
DEFAULT_VOICE_FEATURES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "voice_features")


class VoiceFeatureExtractor:
    """
    声纹特征提取器
    
    负责从音频文件中提取声纹特征，并保存为NPY文件。
    提供元数据管理功能，支持批量处理。
    """
    
    def __init__(
        self, 
        output_dir: str = DEFAULT_VOICE_FEATURES_DIR,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        use_gpu: bool = True
    ):
        """
        初始化声纹特征提取器
        
        Args:
            output_dir: 声纹特征输出目录
            sample_rate: 采样率
            use_gpu: 是否使用GPU
        """
        self.output_dir = output_dir
        self.sample_rate = sample_rate
        self.device = torch.device('cuda' if use_gpu and torch.cuda.is_available() else 'cpu')
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 元数据路径
        self.metadata_path = os.path.join(output_dir, "voice_metadata.json")
        self.metadata = self._load_metadata()
        
        # 加载音频编码器
        self.encoder = self._load_encoder()
        
        logger.info(f"声纹特征提取器初始化完成：输出目录={output_dir}, 设备={self.device}")
    
    def _load_metadata(self) -> Dict:
        """
        加载声音元数据
        
        Returns:
            Dict: 元数据字典
        """
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载元数据失败: {e}")
                return {"voices": {}, "last_updated": datetime.now().isoformat()}
        else:
            return {"voices": {}, "last_updated": datetime.now().isoformat()}
    
    def _save_metadata(self):
        """保存声音元数据"""
        try:
            self.metadata["last_updated"] = datetime.now().isoformat()
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            logger.info(f"元数据已保存到 {self.metadata_path}")
        except Exception as e:
            logger.error(f"保存元数据失败: {e}")
    
    def _load_encoder(self):
        """
        加载声学编码器模型
        
        Returns:
            音频编码器模型
        """
        # 首先尝试导入MegaTTS3的编码器
        try:
            # 尝试导入MegaTTS3的编码器
            from MegaTTS3.tts.infer_cli import MegaTTS3DiTInfer
            logger.info("使用MegaTTS3自带的音频编码器")
            
            # 这里需要提供合适的模型路径
            model_paths = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "checkpoints", "MegaTTS3-zh-en-v1.0", "model.pth"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "checkpoints", "model.pth"),
                os.path.join("D:/AI-Sound/checkpoints", "MegaTTS3-zh-en-v1.0", "model.pth"),
                os.path.join("D:/AI-Sound/checkpoints", "model.pth")
            ]
            
            # 查找存在的模型路径
            model_path = None
            for path in model_paths:
                if os.path.exists(path):
                    model_path = path
                    break
            
            if model_path is None:
                logger.warning("未找到MegaTTS3模型文件，将使用简单特征提取")
                return MockAudioEncoder()
            
            # 初始化MegaTTS3模型
            logger.info(f"加载MegaTTS3模型: {model_path}")
            # 实例化MegaTTS3DiTInfer
            infer_model = MegaTTS3DiTInfer(
                model_path=model_path,
                device=self.device.type
            )
            
            # 以编码器方式使用
            return infer_model
            
        except Exception as e:
            logger.warning(f"导入MegaTTS3编码器失败: {e}")
            logger.warning("将使用简化版特征提取器")
            return MockAudioEncoder()
    
    def _preprocess_audio(self, audio_path: str) -> np.ndarray:
        """
        预处理音频
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            np.ndarray: 处理后的音频数据
        """
        try:
            # 加载音频
            audio, sr = librosa.load(audio_path, sr=self.sample_rate, mono=True)
            
            # 检查音频长度
            audio_duration = len(audio) / self.sample_rate
            logger.info(f"音频时长: {audio_duration:.2f}秒")
            
            if audio_duration < DEFAULT_MIN_AUDIO_LENGTH:
                logger.warning(f"音频时长过短 ({audio_duration:.2f}秒 < {DEFAULT_MIN_AUDIO_LENGTH}秒)")
                # 填充到最小长度
                pad_length = int((DEFAULT_MIN_AUDIO_LENGTH - audio_duration) * self.sample_rate)
                audio = np.pad(audio, (0, pad_length), mode='constant')
                logger.info(f"已填充音频到 {DEFAULT_MIN_AUDIO_LENGTH}秒")
            
            elif audio_duration > DEFAULT_MAX_AUDIO_LENGTH:
                logger.warning(f"音频时长过长 ({audio_duration:.2f}秒 > {DEFAULT_MAX_AUDIO_LENGTH}秒)，将截取前{DEFAULT_MAX_AUDIO_LENGTH}秒")
                # 截取前MAX_AUDIO_LENGTH秒
                audio = audio[:int(DEFAULT_MAX_AUDIO_LENGTH * self.sample_rate)]
            
            # 标准化音量
            audio = librosa.util.normalize(audio)
            
            return audio
            
        except Exception as e:
            logger.error(f"音频预处理失败: {e}")
            raise ValueError(f"音频预处理失败: {e}")
    
    def extract_feature(
        self, 
        audio_path: str, 
        voice_id: str = None, 
        metadata: Dict = None
    ) -> Dict:
        """
        提取声纹特征
        
        Args:
            audio_path: 音频文件路径
            voice_id: 声音ID（可选）
            metadata: 音色元数据（可选）
            
        Returns:
            Dict: 声音信息
        """
        logger.info(f"开始提取声纹特征: {audio_path}")
        
        try:
            # 预处理音频
            audio = self._preprocess_audio(audio_path)
            
            # 转换为张量
            audio_tensor = torch.FloatTensor(audio).unsqueeze(0).to(self.device)
            
            # 提取特征
            with torch.no_grad():
                if hasattr(self.encoder, 'get_reference_mel'):
                    # 使用MegaTTS3特有方法提取特征
                    features = self.encoder.get_reference_mel(audio_tensor)
                else:
                    # 使用通用方法
                    features = self.encoder(audio_tensor)
                
            # 转换为NumPy数组
            features_np = features.cpu().numpy()
            
            # 生成声音ID（如果未提供）
            if voice_id is None:
                basename = os.path.splitext(os.path.basename(audio_path))[0]
                # 使用文件名 + 时间戳作为ID
                voice_id = f"{basename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 生成NPY文件路径
            npy_filename = f"{voice_id}.npy"
            npy_path = os.path.join(self.output_dir, npy_filename)
            
            # 保存NPY文件
            np.save(npy_path, features_np)
            logger.info(f"声纹特征已保存到 {npy_path}")
            
            # 准备元数据
            if metadata is None:
                metadata = {}
                
            # 文件大小
            file_size = os.path.getsize(npy_path)
            
            # 准备元数据
            voice_info = {
                "id": voice_id,
                "name": metadata.get("name", os.path.splitext(os.path.basename(audio_path))[0]),
                "description": metadata.get("description", ""),
                "feature_path": npy_path,
                "audio_path": os.path.abspath(audio_path),
                "created_at": datetime.now().isoformat(),
                "file_size": file_size,
                "feature_shape": features_np.shape,
                "tags": metadata.get("tags", []),
                "attributes": metadata.get("attributes", {})
            }
            
            # 添加基本属性
            if "attributes" not in voice_info:
                voice_info["attributes"] = {}
            
            # 如果未指定性别，通过名称进行简单推断
            if "gender" not in voice_info["attributes"]:
                name = voice_info["name"].lower()
                # 简单的性别推断
                if any(keyword in name for keyword in ["female", "woman", "girl", "lady", "女"]):
                    voice_info["attributes"]["gender"] = "female"
                elif any(keyword in name for keyword in ["male", "man", "boy", "guy", "男"]):
                    voice_info["attributes"]["gender"] = "male"
                else:
                    # 默认为未知
                    voice_info["attributes"]["gender"] = "unknown"
            
            # 更新元数据
            self.metadata["voices"][voice_id] = voice_info
            self._save_metadata()
            
            logger.info(f"声纹特征提取完成: {voice_id}")
            return voice_info
            
        except Exception as e:
            logger.error(f"提取声纹特征失败: {e}")
            raise ValueError(f"提取声纹特征失败: {e}")
    
    def batch_extract(
        self,
        audio_dir: str,
        metadata_pattern: Dict = None
    ) -> List[Dict]:
        """
        批量提取音频特征
        
        Args:
            audio_dir: 音频目录
            metadata_pattern: 元数据模板
            
        Returns:
            List[Dict]: 处理结果列表
        """
        logger.info(f"开始批量提取声纹特征: {audio_dir}")
        
        results = []
        audio_files = []
        
        # 收集所有支持的音频文件
        for root, _, files in os.walk(audio_dir):
            for file in files:
                if file.lower().endswith(('.wav', '.mp3', '.flac', '.ogg', '.m4a')):
                    audio_files.append(os.path.join(root, file))
        
        logger.info(f"找到 {len(audio_files)} 个音频文件")
        
        # 处理每个文件
        for i, audio_path in enumerate(audio_files):
            try:
                logger.info(f"处理 ({i+1}/{len(audio_files)}): {audio_path}")
                voice_info = self.extract_feature(audio_path, metadata=metadata_pattern)
                results.append(voice_info)
            except Exception as e:
                logger.error(f"处理文件 {audio_path} 失败: {e}")
        
        logger.info(f"批量提取完成，成功: {len(results)}/{len(audio_files)}")
        return results
    
    def get_all_voices(self) -> List[Dict]:
        """
        获取所有声音列表
        
        Returns:
            List[Dict]: 声音列表
        """
        return list(self.metadata["voices"].values())
    
    def get_voice(self, voice_id: str) -> Optional[Dict]:
        """
        获取特定声音信息
        
        Args:
            voice_id: 声音ID
            
        Returns:
            Optional[Dict]: 声音信息
        """
        return self.metadata["voices"].get(voice_id)
    
    def delete_voice(self, voice_id: str) -> bool:
        """
        删除声音
        
        Args:
            voice_id: 声音ID
            
        Returns:
            bool: 是否成功
        """
        if voice_id in self.metadata["voices"]:
            voice_info = self.metadata["voices"][voice_id]
            
            # 删除NPY文件
            try:
                if os.path.exists(voice_info["feature_path"]):
                    os.remove(voice_info["feature_path"])
                    logger.info(f"已删除NPY文件: {voice_info['feature_path']}")
            except Exception as e:
                logger.error(f"删除NPY文件失败: {e}")
            
            # 删除元数据
            del self.metadata["voices"][voice_id]
            self._save_metadata()
            
            logger.info(f"声纹特征已删除: {voice_id}")
            return True
        
        logger.warning(f"声纹特征不存在: {voice_id}")
        return False
    
    def update_voice_metadata(
        self,
        voice_id: str,
        metadata: Dict
    ) -> Optional[Dict]:
        """
        更新声音元数据
        
        Args:
            voice_id: 声音ID
            metadata: 元数据
            
        Returns:
            Optional[Dict]: 更新后的声音信息
        """
        if voice_id in self.metadata["voices"]:
            voice_info = self.metadata["voices"][voice_id]
            
            # 更新元数据
            for key, value in metadata.items():
                if key not in ["id", "feature_path", "created_at", "feature_shape", "file_size"]:
                    voice_info[key] = value
            
            # 保存元数据
            self._save_metadata()
            logger.info(f"声纹特征元数据已更新: {voice_id}")
            
            return voice_info
        
        logger.warning(f"声纹特征不存在: {voice_id}")
        return None
    
    def get_voice_feature(self, voice_id: str) -> Optional[np.ndarray]:
        """
        获取声音特征数据
        
        Args:
            voice_id: 声音ID
            
        Returns:
            Optional[np.ndarray]: 特征数据
        """
        voice_info = self.get_voice(voice_id)
        if voice_info and os.path.exists(voice_info["feature_path"]):
            try:
                return np.load(voice_info["feature_path"])
            except Exception as e:
                logger.error(f"加载NPY文件失败: {e}")
                return None
        return None
    
    def import_voice_feature(
        self,
        npy_path: str,
        voice_id: str = None,
        metadata: Dict = None,
        copy_file: bool = True
    ) -> Optional[Dict]:
        """
        导入已有的声纹特征文件
        
        Args:
            npy_path: NPY文件路径
            voice_id: 声音ID（可选）
            metadata: 元数据（可选）
            copy_file: 是否复制文件
            
        Returns:
            Optional[Dict]: 声音信息
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(npy_path):
                logger.error(f"NPY文件不存在: {npy_path}")
                return None
            
            # 加载NPY文件以验证其有效性
            features_np = np.load(npy_path)
            
            # 生成声音ID（如果未提供）
            if voice_id is None:
                basename = os.path.splitext(os.path.basename(npy_path))[0]
                voice_id = f"{basename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 目标NPY文件路径
            if copy_file:
                target_npy_path = os.path.join(self.output_dir, f"{voice_id}.npy")
                # 复制文件
                shutil.copy2(npy_path, target_npy_path)
                logger.info(f"已复制NPY文件: {npy_path} -> {target_npy_path}")
            else:
                target_npy_path = npy_path
            
            # 准备元数据
            if metadata is None:
                metadata = {}
            
            # 文件大小
            file_size = os.path.getsize(target_npy_path)
            
            # 准备声音信息
            voice_info = {
                "id": voice_id,
                "name": metadata.get("name", os.path.splitext(os.path.basename(npy_path))[0]),
                "description": metadata.get("description", "导入的声纹特征"),
                "feature_path": target_npy_path,
                "audio_path": metadata.get("audio_path", ""),
                "created_at": datetime.now().isoformat(),
                "imported_at": datetime.now().isoformat(),
                "file_size": file_size,
                "feature_shape": features_np.shape,
                "tags": metadata.get("tags", []),
                "attributes": metadata.get("attributes", {})
            }
            
            # 更新元数据
            self.metadata["voices"][voice_id] = voice_info
            self._save_metadata()
            
            logger.info(f"声纹特征导入完成: {voice_id}")
            return voice_info
            
        except Exception as e:
            logger.error(f"导入声纹特征失败: {e}")
            return None


# 后备音频编码器，当无法使用MegaTTS3编码器时使用
class MockAudioEncoder:
    """
    模拟音频编码器
    当无法加载MegaTTS3编码器时使用
    """
    
    def __init__(self):
        logger.warning("使用模拟音频编码器，仅用于测试")
    
    def __call__(self, audio_tensor: torch.Tensor) -> torch.Tensor:
        """
        提取音频特征
        
        Args:
            audio_tensor: 音频张量
            
        Returns:
            torch.Tensor: 特征张量
        """
        # 简单降维，创建假特征
        audio_numpy = audio_tensor.cpu().numpy()
        # 获取音频长度
        audio_length = audio_numpy.shape[1]
        # 创建随机特征
        feature_length = min(audio_length // 256, 1000)  # 假设每256样本一个特征
        feature_dim = 256  # 假设特征维度为256
        
        # 创建特征
        features = np.random.randn(1, feature_length, feature_dim).astype(np.float32) * 0.1
        
        # 返回张量
        return torch.from_numpy(features)
    
    def get_reference_mel(self, audio_tensor: torch.Tensor) -> torch.Tensor:
        """
        获取参考梅尔谱特征
        
        Args:
            audio_tensor: 音频张量
            
        Returns:
            torch.Tensor: 特征张量
        """
        return self.__call__(audio_tensor) 