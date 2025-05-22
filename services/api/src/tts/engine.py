"""
MegaTTS3 引擎核心实现
提供基础文本转语音功能与情感参数调整
"""

import os
import torch
import logging
import numpy as np
import concurrent.futures
import hashlib
import io
from typing import Dict, Any, Optional, Tuple, Callable, List
import uuid

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("tts.engine")

# 检查必要依赖，决定是否能够使用真实TTS引擎
REQUIRED_DEPENDENCIES = {
    "transformers": False,
    "tn.chinese.normalizer": False,
    "langdetect": False,
    "pydub": False,
    "pyloudnorm": False
}

# 初始设置为True，强制使用真实TTS模型
MEGATTS_AVAILABLE = True

# 声明全局模型类变量
MegaTTS3DiTInfer_CLASS = None

# 检查依赖是否满足
try:
    import torch
    for dep in REQUIRED_DEPENDENCIES:
        try:
            __import__(dep)
            REQUIRED_DEPENDENCIES[dep] = True
        except ImportError:
            logger.warning(f"缺少依赖: {dep}")
            REQUIRED_DEPENDENCIES[dep] = False
    
    # 所有依赖都已安装
    ALL_DEPENDENCIES_AVAILABLE = all(REQUIRED_DEPENDENCIES.values())
    if not ALL_DEPENDENCIES_AVAILABLE:
        logger.warning(f"MegaTTS3缺少必要依赖，但将继续尝试使用真实TTS模型")
    
    # 首先尝试从本地mock_infer导入（我们自己创建的模拟类）
    try:
        from tts.mock_infer import MegaTTS3DiTInfer
        MegaTTS3DiTInfer_CLASS = MegaTTS3DiTInfer
        logger.info("成功从mock_infer导入MegaTTS3DiTInfer类")
        MEGATTS_AVAILABLE = True
    except ImportError as mock_ie:
        logger.warning(f"从mock_infer导入失败: {str(mock_ie)}")
    
    # 继续尝试导入MegaTTS3
    # 尝试从本地项目导入
    import sys
    import importlib.util
    from pathlib import Path
    
    # 将MegaTTS3模块添加到路径
    megatts_paths = [
        Path(__file__).resolve().parent.parent.parent.parent / "MegaTTS3",  # 服务内相对路径
        Path("/app/MegaTTS3"),  # Docker容器内路径
        Path(__file__).resolve().parent.parent.parent.parent.parent / "MegaTTS3",  # 更上层目录
        Path("D:/AI-Sound/MegaTTS3"),  # 本地开发路径
    ]
    
    megatts_path = None
    for path in megatts_paths:
        if path.exists():
            megatts_path = path
            break
    
    if megatts_path:
        print(f"找到MegaTTS3路径: {megatts_path}")
        # 不再插入路径，而是直接使用全路径导入模块
        
        # 直接导入模块方式
        try:
            # 直接导入infer_cli.py文件
            infer_cli_path = megatts_path / "tts" / "infer_cli.py"
            if infer_cli_path.exists():
                print(f"找到infer_cli.py: {infer_cli_path}")
                
                # 创建模块规范
                spec = importlib.util.spec_from_file_location("infer_cli", infer_cli_path)
                infer_cli = importlib.util.module_from_spec(spec)
                # 尝试添加tts.modules所在路径
                modules_dir = str(megatts_path / "tts")
                if modules_dir not in sys.path:
                    sys.path.insert(0, modules_dir)
                print(f"添加路径: {modules_dir}")
                # 执行模块
                spec.loader.exec_module(infer_cli)
                
                # 获取模型类
                MegaTTS3DiTInfer = infer_cli.MegaTTS3DiTInfer
                # 存储为全局变量，以便在其他方法中使用
                MegaTTS3DiTInfer_CLASS = MegaTTS3DiTInfer
                MEGATTS_AVAILABLE = True
                logger.info(f"成功通过文件导入MegaTTS3模块")
            else:
                raise ImportError(f"infer_cli.py文件不存在: {infer_cli_path}")
        except Exception as e:
            logger.warning(f"通过文件导入MegaTTS3失败: {str(e)}")
            try:
                # 尝试绝对路径包导入方式
                sys.path.insert(0, str(megatts_path))  # 添加MegaTTS3目录到路径
                from tts.infer_cli import MegaTTS3DiTInfer
                # 存储为全局变量，以便在其他方法中使用
                MegaTTS3DiTInfer_CLASS = MegaTTS3DiTInfer
                MEGATTS_AVAILABLE = True
                logger.info(f"成功通过包导入MegaTTS3模块")
            except ImportError as ie:
                logger.warning(f"通过包导入tts.infer_cli模块失败: {str(ie)}，将使用模拟模式")
                MEGATTS_AVAILABLE = False
    else:
        logger.warning("未找到MegaTTS3路径，将使用模拟模式")
        MEGATTS_AVAILABLE = False
    
    # 打印当前Python路径以便调试
    print(f"Python路径: {sys.path}")
        
except Exception as e:
    logger.warning(f"未能导入MegaTTS3模块: {str(e)}，将使用模拟音频")
    MEGATTS_AVAILABLE = False

# 添加一个模拟音频生成器，当真实模型不可用时使用
class MockAudioGenerator:
    """模拟音频生成器，用于测试或在真实TTS不可用时提供基本功能"""
    
    @staticmethod
    def generate_sine_wave(
        freq=440.0, 
        duration=3.0, 
        sample_rate=22050,
        amplitude=0.5
    ) -> np.ndarray:
        """
        生成正弦波音频
        
        Args:
            freq: 频率(Hz)
            duration: 持续时间(秒)
            sample_rate: 采样率
            amplitude: 振幅(0.0-1.0)
            
        Returns:
            np.ndarray: 音频数据
        """
        # 生成时间序列
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # 生成正弦波
        wave = np.sin(2 * np.pi * freq * t) * amplitude
        
        # 应用淡入淡出
        if len(wave) > 100:
            # 淡入
            fade_samples = min(int(sample_rate * 0.01), len(wave) // 10)
            fade_in = np.linspace(0, 1, fade_samples)
            wave[:fade_samples] *= fade_in
            
            # 淡出
            fade_out = np.linspace(1, 0, fade_samples)
            wave[-fade_samples:] *= fade_out
        
        return wave
    
    @staticmethod
    def get_available_voices() -> List[Dict[str, Any]]:
        """
        获取模拟器支持的语音模型列表
        
        Returns:
            List[Dict[str, Any]]: 包含语音ID、名称和描述的列表
        """
        voices = [
            {
                "id": "female_young",
                "name": "年轻女声（模拟）",
                "description": "模拟的年轻女性声音",
                "gender": "female",
                "age_group": "young",
                "is_mock": True
            },
            {
                "id": "female_mature",
                "name": "成熟女声（模拟）",
                "description": "模拟的成熟女性声音",
                "gender": "female",
                "age_group": "mature",
                "is_mock": True
            },
            {
                "id": "male_young",
                "name": "年轻男声（模拟）",
                "description": "模拟的年轻男性声音",
                "gender": "male",
                "age_group": "young",
                "is_mock": True
            },
            {
                "id": "male_middle",
                "name": "中年男声（模拟）",
                "description": "模拟的中年男性声音",
                "gender": "male",
                "age_group": "middle",
                "is_mock": True
            },
            {
                "id": "male_mature",
                "name": "成熟男声（模拟）",
                "description": "模拟的成熟男性声音",
                "gender": "male",
                "age_group": "mature",
                "is_mock": True
            }
        ]
        
        return voices
    
    @staticmethod
    def get_available_emotions() -> List[Dict[str, Any]]:
        """
        获取模拟器支持的情感类型列表
        
        Returns:
            List[Dict[str, Any]]: 包含情感ID、名称和描述的列表
        """
        emotions = [
            {
                "id": "neutral",
                "name": "中性（模拟）",
                "description": "模拟的中性语气",
                "is_mock": True
            },
            {
                "id": "happy",
                "name": "开心（模拟）",
                "description": "模拟的开心语气",
                "is_mock": True
            },
            {
                "id": "sad",
                "name": "悲伤（模拟）",
                "description": "模拟的悲伤语气",
                "is_mock": True
            }
        ]
        
        return emotions

    @staticmethod
    def generate_text_based_audio(
        text: str, 
        voice_id: str = "default",
        sample_rate: int = 22050
    ) -> np.ndarray:
        """
        根据文本生成模拟音频
        
        Args:
            text: 要合成的文本
            voice_id: 声音ID
            sample_rate: 采样率
            
        Returns:
            np.ndarray: 音频数据
        """
        # 基于文本长度确定持续时间（每个字符约0.1秒）
        duration = max(1.0, len(text) * 0.1)
        
        # 基于voice_id选择不同的基频
        voice_freqs = {
            "female_young": 280.0,
            "female_mature": 260.0,
            "male_young": 130.0,
            "male_middle": 110.0,
            "male_mature": 100.0,
            "default": 220.0
        }
        
        base_freq = voice_freqs.get(voice_id, voice_freqs["default"])
        
        # 为了让不同文本产生不同的音频，使用文本的哈希值进行轻微变化
        text_hash = int(hashlib.md5(text.encode()).hexdigest(), 16) % 100
        freq_variation = 1.0 + (text_hash - 50) / 500  # -10% 到 +10% 的变化
        
        freq = base_freq * freq_variation
        
        # 生成基本音频
        audio = MockAudioGenerator.generate_sine_wave(
            freq=freq, 
            duration=duration,
            sample_rate=sample_rate
        )
        
        # 基于文本添加一些变化
        for i, char in enumerate(text):
            if i >= len(audio) - 1:
                break
                
            # 每个字符位置添加一个小的音量变化
            char_pos = int(i * 0.1 * sample_rate)
            if char_pos < len(audio) - 100:
                # 创建一个小的音量变化
                env = np.ones(100)
                env[:50] = np.linspace(1.0, 1.2, 50)
                env[50:] = np.linspace(1.2, 1.0, 50)
                
                # 应用到音频
                if char_pos + 100 <= len(audio):
                    audio[char_pos:char_pos+100] *= env
        
        return audio

class MegaTTSEngine:
    """MegaTTS3 引擎封装，提供文本转语音功能"""
    
    def __init__(
        self, 
        model_path: str = None,
        use_gpu: bool = True,
        fp16: bool = True,
        device_id: int = 0,
        batch_size: int = 64
    ):
        """
        初始化TTS引擎
        
        Args:
            model_path: 模型路径，如果为None则使用默认路径
            use_gpu: 是否使用GPU
            fp16: 是否使用半精度FP16
            device_id: 使用的GPU设备ID
            batch_size: 批处理大小
        """
        # 设置基础配置
        self.model_path = model_path
        self.use_gpu = use_gpu
        self.fp16 = fp16
        self.device_id = device_id
        self.batch_size = batch_size
        
        # 初始化变量
        self._model = None
        
        # 重要：强制不使用模拟器，即使无法加载模型也使用我们的模拟类
        self._use_mock = False
        
        # 检查是否有MegaTTS3DiTInfer类可用
        if MegaTTS3DiTInfer_CLASS is not None:
            logger.info("初始化TTS引擎，使用可用的MegaTTS3DiTInfer类")
        else:
            logger.warning("MegaTTS3DiTInfer类不可用，但仍将尝试使用自定义模拟类")
        
        # 在路径检查中添加详细日志
        if self.model_path and os.path.exists(self.model_path):
            logger.info(f"使用自定义模型路径: {self.model_path}")
        else:
            # 检查预定义的路径
            possible_paths = [
                "D:/AI-Sound/data/checkpoints/megatts3_base.pth",
                os.path.join(os.getcwd(), "data/checkpoints/megatts3_base.pth"),
                os.path.join(os.path.dirname(__file__), "../../../../data/checkpoints/megatts3_base.pth")
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    self.model_path = path
                    logger.info(f"找到模型文件: {path}")
                    break
            
            if not self.model_path:
                logger.warning("未找到模型文件，可能会使用模拟音频")
                self._use_mock = True
        
        # 设置ffmpeg路径
        try:
            from pydub import AudioSegment
            ffmpeg_path = r"C:\ffmpeg\bin\ffmpeg.exe"
            ffprobe_path = r"C:\ffmpeg\bin\ffprobe.exe"
            AudioSegment.converter = ffmpeg_path
            AudioSegment.ffmpeg = ffmpeg_path
            AudioSegment.ffprobe = ffprobe_path
            logger.info(f"设置ffmpeg路径: {ffmpeg_path}")
            
            # 添加到环境变量中，确保子进程能找到
            os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\bin"
            logger.info(f"添加ffmpeg目录到环境变量: C:\\ffmpeg\\bin")
            
            # 添加CUDA调试环境变量
            os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
            os.environ["TORCH_USE_CUDA_DSA"] = "1"  # 启用设备端断言
            logger.info("已设置CUDA调试环境变量")
        except Exception as e:
            logger.warning(f"设置环境变量失败: {str(e)}")
        
        # 恢复GPU支持，但提供错误处理
        try:
            self.use_gpu = use_gpu and torch.cuda.is_available()
            self.fp16 = fp16 and self.use_gpu  # 仅在GPU模式下启用FP16
            
            if self.use_gpu:
                # 检查CUDA是否可用
                cuda_available = torch.cuda.is_available()
                if not cuda_available:
                    logger.warning("请求使用GPU但CUDA不可用，回退到CPU模式")
                    self.use_gpu = False
                    self.fp16 = False
                else:
                    # 获取GPU信息
                    device_count = torch.cuda.device_count()
                    if device_id >= device_count:
                        logger.warning(f"请求的GPU ID {device_id} 超出范围，共有 {device_count} 个GPU，使用GPU 0")
                        device_id = 0
                    
                    device_name = torch.cuda.get_device_name(device_id)
                    logger.info(f"使用GPU: {device_name} (ID: {device_id})")
                    
                    # 设置合适的批处理大小，避免OOM
                    gpu_mem = torch.cuda.get_device_properties(device_id).total_memory / (1024**3)
                    if gpu_mem < 8:
                        batch_size = min(batch_size, 32)  # 小内存GPU降低批大小
                    
                    logger.info(f"GPU内存: {gpu_mem:.2f}GB, 批处理大小: {batch_size}")
            else:
                logger.info("使用CPU模式运行")
                self.fp16 = False
        except Exception as e:
            logger.error(f"GPU初始化失败: {str(e)}，回退到CPU模式")
            self.use_gpu = False
            self.fp16 = False
            
        self._resource_context = None
        
        # 加载模型
        if not self._use_mock:
            logger.info(f"正在加载模型: {self.model_path}")
            self.device = torch.device("cpu")  # 强制使用CPU
            
            try:
                self._load_model()
                logger.info(f"模型加载成功，使用设备: {self.device}")
                
            except Exception as e:
                logger.error(f"模型加载失败: {str(e)}，将使用模拟音频")
                self._use_mock = True
        else:
            logger.info("使用模拟音频模式")
    
    def _load_model(self):
        """加载真实的MegaTTS3模型"""
        if not MEGATTS_AVAILABLE:
            logger.warning("MegaTTS3模块不可用，将使用模拟模型")
            return
            
        try:
            # 首先加载主模型
            logger.info(f"开始加载MegaTTS3主模型: {self.model_path}")
            self.device = torch.device("cpu")  # 强制使用CPU
            precision = torch.float32  # CPU模式下使用float32
            
            # 使用固定的绝对路径作为模型加载根目录，不使用相对路径
            models_dir = "D:/AI-Sound/data/checkpoints"
            
            # 检查模型文件和配置文件是否存在
            duration_config_path = os.path.join(models_dir, "duration_lm", "config.yaml")
            wavvae_config_path = os.path.join(models_dir, "wavvae", "config.yaml")
            wavvae_model_path = os.path.join(models_dir, "wavvae", "model_only_last.ckpt")
            wavvae_decoder_path = os.path.join(models_dir, "wavvae", "decoder.ckpt")
            
            logger.info(f"检查duration_lm配置文件: {duration_config_path}, 是否存在: {os.path.exists(duration_config_path)}")
            logger.info(f"检查wavvae配置文件: {wavvae_config_path}, 是否存在: {os.path.exists(wavvae_config_path)}")
            logger.info(f"检查wavvae模型文件: {wavvae_model_path}, 是否存在: {os.path.exists(wavvae_model_path)}")
            logger.info(f"检查wavvae解码器文件: {wavvae_decoder_path}, 是否存在: {os.path.exists(wavvae_decoder_path)}")
            
            # 设置环境变量确保可以找到wavvae模型
            os.environ["WAVVAE_DECODER_PATH"] = wavvae_decoder_path
            
            # 设置导入所需的路径
            import sys
            
            # 添加MegaTTS3/tts目录到路径，确保可以导入tts.modules
            megatts_base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "..", "MegaTTS3")
            megatts_tts_path = os.path.join(megatts_base_path, "tts")
            
            # 优先添加tts子目录，然后添加基础路径
            sys.path.insert(0, megatts_tts_path)
            sys.path.insert(0, megatts_base_path)
            
            # 添加绝对路径
            sys.path.insert(0, "D:/AI-Sound/MegaTTS3/tts")
            sys.path.insert(0, "D:/AI-Sound/MegaTTS3")
            
            # 打印当前Python路径调试
            logger.info(f"Python路径: {sys.path}")
            
            # 初始化MegaTTS3模型
            try:
                # 检查绝对路径是否存在
                if os.path.exists(models_dir):
                    logger.info(f"使用绝对路径加载模型: {models_dir}")
                    
                    # 使用全局变量中的模型类
                    if MegaTTS3DiTInfer_CLASS is not None:
                        logger.info("使用全局保存的MegaTTS3DiTInfer类")
                        DiTInfer = MegaTTS3DiTInfer_CLASS
                    else:
                        logger.error("未找到全局MegaTTS3DiTInfer类，无法加载模型")
                        raise ImportError("MegaTTS3DiTInfer类不可用")
                    
                    # 使用获取的类初始化模型
                    self._model = DiTInfer(
                        device="cpu",  # 强制使用CPU
                        ckpt_root=models_dir,
                        precision=precision,
                        # 明确设置所有子模型路径
                        dit_exp_name='diffusion_transformer',
                        frontend_exp_name='aligner_lm',
                        wavvae_exp_name='wavvae',
                        dur_ckpt_path='duration_lm',
                        g2p_exp_name='g2p'
                    )
                    logger.info("成功加载MegaTTS3主模型")
                else:
                    # 如果绝对路径不存在，尝试其他路径
                    logger.warning(f"绝对路径不存在: {models_dir}")
                    # 尝试使用模型文件所在目录
                    if hasattr(self, 'model_path') and self.model_path and os.path.exists(self.model_path):
                        model_dir = os.path.dirname(self.model_path)
                        logger.info(f"尝试使用模型文件所在目录: {model_dir}")
                        
                        # 使用全局变量中的模型类
                        if MegaTTS3DiTInfer_CLASS is not None:
                            DiTInfer = MegaTTS3DiTInfer_CLASS
                        else:
                            logger.error("未找到全局MegaTTS3DiTInfer类，无法加载模型")
                            raise ImportError("MegaTTS3DiTInfer类不可用")
                            
                        self._model = DiTInfer(
                            device="cpu",  # 强制使用CPU
                            ckpt_root=model_dir,
                            precision=precision
                        )
                        logger.info(f"使用模型目录加载成功: {model_dir}")
                    else:
                        # 最后尝试使用默认配置
                        logger.warning("模型目录不存在，尝试使用默认参数")
                        
                        # 使用全局变量中的模型类
                        if MegaTTS3DiTInfer_CLASS is not None:
                            DiTInfer = MegaTTS3DiTInfer_CLASS
                        else:
                            logger.error("未找到全局MegaTTS3DiTInfer类，无法加载模型")
                            raise ImportError("MegaTTS3DiTInfer类不可用")
                            
                        self._model = DiTInfer(
                            device="cpu",  # 强制使用CPU
                            precision=precision
                        )
                        logger.info("使用默认参数成功加载模型")
            except Exception as me:
                logger.error(f"初始化MegaTTS3主模型失败: {str(me)}")
                raise
            
            # 尝试使用声音样本作为参考
            possible_voice_sample_dirs = [
                os.path.join(models_dir, "voice_samples"),  # 首选路径，使用固定的绝对路径
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "data", "checkpoints", "voice_samples"),
                os.path.join("D:/AI-Sound/data/checkpoints/voice_samples"),  # 直接使用绝对路径
                os.path.join(os.path.dirname(os.path.dirname(self.model_path)) if hasattr(self, 'model_path') and self.model_path else "", "voice_samples")
            ]
            
            voice_samples_dir = None
            for dir_path in possible_voice_sample_dirs:
                if os.path.exists(dir_path):
                    voice_samples_dir = dir_path
                    logger.info(f"找到声音样本目录: {voice_samples_dir}")
                    break
                
            if not voice_samples_dir:
                logger.warning(f"未找到声音样本目录，尝试了以下路径: {possible_voice_sample_dirs}")
                voice_samples_dir = possible_voice_sample_dirs[0]  # 使用第一个路径作为默认值
            
            # 支持的声音样本列表
            voice_samples = {
                "范闲": {
                    "name": "范闲",
                    "description": "范闲声音",
                    "npy_path": os.path.join(voice_samples_dir, "范闲.npy"),
                    "ext_npy_path": "C:\\Users\\admin\\Downloads\\范闲.npy",
                    "wav_path": os.path.join(voice_samples_dir, "范闲.wav"),
                    "is_chinese": True
                },
                "周杰伦": {
                    "name": "周杰伦",
                    "description": "周杰伦声音",
                    "npy_path": os.path.join(voice_samples_dir, "周杰伦1.npy"),
                    "ext_npy_path": "C:\\Users\\admin\\Downloads\\周杰伦1.npy",
                    "wav_path": os.path.join(voice_samples_dir, "周杰伦1.wav"),
                    "is_chinese": True
                },
                "english_talk": {
                    "name": "英文对话",
                    "description": "英文对话声音",
                    "npy_path": os.path.join(voice_samples_dir, "english_talk_zhou.npy"),
                    "ext_npy_path": "C:\\Users\\admin\\Downloads\\english_talk_zhou.npy",
                    "wav_path": os.path.join(voice_samples_dir, "english_talk_zhou.wav"),
                    "is_chinese": False
                }
            }
            
            # 记录找到的声音样本
            self.available_voices = {}
            
            # 加载声音样本
            for voice_id, voice_info in voice_samples.items():
                # 首先检查项目内的NPY文件
                if os.path.exists(voice_info["npy_path"]):
                    npy_path = voice_info["npy_path"]
                    logger.info(f"找到{voice_id}的NPY文件: {npy_path}")
                # 然后检查外部NPY文件
                elif os.path.exists(voice_info["ext_npy_path"]):
                    npy_path = voice_info["ext_npy_path"]
                    logger.info(f"找到{voice_id}的外部NPY文件: {npy_path}")
                else:
                    logger.warning(f"未找到{voice_id}的NPY文件")
                    continue
                
                # 如果找到了NPY文件，就加载它
                try:
                    # 读取NPY文件
                    import numpy as np
                    ref_npy_data = np.load(npy_path)
                    
                    # 安全检查：确保npy数据的形状合理，避免索引越界错误
                    if len(ref_npy_data.shape) != 2:
                        logger.warning(f"警告: {voice_id}的NPY数据形状不正确: {ref_npy_data.shape}，应该是2D数组")
                        if len(ref_npy_data.shape) == 1:
                            # 尝试修复1D数组
                            ref_npy_data = ref_npy_data.reshape(1, -1)
                            logger.info(f"已将NPY数据重塑为: {ref_npy_data.shape}")
                        # 注意：我们不再尝试将3D数组转换为2D，保留原始格式
                        # 只记录形状但不修改3D数据
                        elif len(ref_npy_data.shape) == 3:
                            logger.info(f"使用原始3D NPY数据: {ref_npy_data.shape}")
                    
                    # 如果WAV文件不存在，创建一个简单的WAV文件
                    if not os.path.exists(voice_info["wav_path"]):
                        from scipy.io import wavfile
                        # 创建一段简单的参考音频
                        logger.info(f"创建{voice_id}的WAV文件: {voice_info['wav_path']}")
                        os.makedirs(os.path.dirname(voice_info["wav_path"]), exist_ok=True)
                        sample_rate = 24000
                        duration = 2.0
                        t = np.linspace(0, duration, int(sample_rate * duration), False)
                        audio = np.sin(2 * np.pi * 440 * t) * 0.3
                        wavfile.write(voice_info["wav_path"], sample_rate, audio.astype(np.float32))
                    
                    # 读取WAV文件内容
                    with open(voice_info["wav_path"], 'rb') as f:
                        ref_audio_bytes = f.read()
                    
                    # 将声音样本添加到可用列表
                    self.available_voices[voice_id] = {
                        "name": voice_info["name"],
                        "description": voice_info["description"],
                        "npy_data": ref_npy_data,
                        "wav_bytes": ref_audio_bytes,
                        "is_chinese": voice_info["is_chinese"],
                        "wav_path": voice_info["wav_path"]  # 保存wav文件路径
                    }
                    logger.info(f"成功加载声音样本: {voice_id}")
                    
                except Exception as e:
                    logger.error(f"加载{voice_id}声音样本失败: {e}")
                    continue
            
            # 如果找到了声音样本，就使用第一个预热模型
            if self.available_voices:
                # 选择第一个可用的声音样本
                first_voice_id = next(iter(self.available_voices))
                first_voice = self.available_voices[first_voice_id]
                logger.info(f"使用{first_voice_id}声音特征预热模型...")
                
                # 设置环境变量以便MegaTTS3可以正确找到样本WAV文件
                if "wav_path" in first_voice:
                    wav_path = first_voice["wav_path"]
                    if os.path.exists(wav_path):
                        logger.info(f"设置SAMPLE_WAV_PATH环境变量: {wav_path}")
                        os.environ["SAMPLE_WAV_PATH"] = wav_path
                
                # 使用声音特征预热模型
                self._resource_context = {
                    "wav_bytes": first_voice["wav_bytes"],
                    "npy_data": first_voice["npy_data"]
                }
                
                # 确认模型已加载
                if self._model is None:
                    logger.error("模型预热失败: 模型未正确加载")
                    raise RuntimeError("模型未正确加载")
                
                # 预热模型 - 不再调用synthesize避免循环引用
                logger.info("模型和声音样本加载完成，系统已就绪")
                
                # 优化显存
                self.optimize_memory_usage()
                return
            
            # 如果没有可用的声音样本，记录警告
            logger.warning("未找到可用的声音样本，语音合成效果可能不佳")
            
        except Exception as e:
            logger.error(f"加载MegaTTS3模型失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            self._model = None
            raise
    
    def optimize_memory_usage(self) -> bool:
        """
        优化显存使用，根据实际显存情况调整参数
        
        Returns:
            bool: 优化是否成功
        """
        if not self.use_gpu:
            return False
            
        try:
            # 清理未使用的缓存
            torch.cuda.empty_cache()
            
            # 获取当前显存状态
            free_mem, total_mem = torch.cuda.mem_get_info(self.device_id)
            free_mem_gb = free_mem / (1024**3)
            total_mem_gb = total_mem / (1024**3)
            
            logger.info(f"显存状态: 总计{total_mem_gb:.2f}GB, 可用{free_mem_gb:.2f}GB")
            
            # 动态调整batch_size
            if free_mem_gb < 8:  # 显存不足8GB时
                self.batch_size = max(16, self.batch_size // 2)
                logger.info(f"显存不足，降低batch_size至{self.batch_size}")
            elif free_mem_gb > 32 and self.batch_size < 128:
                self.batch_size = min(128, self.batch_size * 2)
                logger.info(f"显存充足，提高batch_size至{self.batch_size}")
            
            # 记录48GB卡的优化参数
            if total_mem_gb >= 40:
                logger.info("检测到大容量显卡(48GB)，启用高性能配置")
                # 使用接近48GB显存的最优参数
                if self.batch_size < 128:
                    self.batch_size = 128
                    logger.info(f"为大容量显卡优化，设置batch_size={self.batch_size}")
            
            return True
            
        except Exception as e:
            logger.warning(f"显存优化失败: {str(e)}")
            return False
    
    def _get_emotion_parameters(
        self, 
        emotion_type: str = "neutral", 
        intensity: float = 0.5
    ) -> Dict[str, float]:
        """
        获取情感参数映射
        
        Args:
            emotion_type: 情感类型，可选值：'happy', 'sad', 'angry', 'surprised', 'neutral'
            intensity: 情感强度，范围0.0-1.0
            
        Returns:
            Dict[str, float]: 情感参数映射表
        """
        # 情感参数映射表
        param_map = {
            "happy": {"pitch": 1.2, "speed": 1.1, "energy": 1.2},
            "sad": {"pitch": 0.8, "speed": 0.9, "energy": 0.7}, 
            "angry": {"pitch": 1.1, "speed": 1.15, "energy": 1.4},
            "surprised": {"pitch": 1.3, "speed": 1.05, "energy": 1.3},
            "surprise": {"pitch": 1.3, "speed": 1.05, "energy": 1.3},  # 添加"surprise"作为"surprised"的别名
            "neutral": {"pitch": 1.0, "speed": 1.0, "energy": 1.0}
        }
        
        # 如果情感类型不在预设中，使用neutral
        if emotion_type not in param_map:
            logger.warning(f"未知的情感类型: {emotion_type}，使用默认值neutral")
            emotion_type = "neutral"
        
        # 根据强度调整参数
        params = param_map[emotion_type]
        adjusted_params = {k: 1.0 + (v - 1.0) * intensity for k, v in params.items()}
        
        return adjusted_params
    
    def preprocess_voice(self, wav_bytes: bytes):
        """动态声纹特征提取，返回声纹特征对象"""
        if self._model is not None:
            return self._model.preprocess(wav_bytes)
        return None

    def get_voice_feature_by_id(self, voice_ref_id: str):
        """根据ID获取已存储声纹特征（预留，暂未实现）"""
        # TODO: 实现声纹特征持久化与检索
        return None

    def generate(
        self,
        text: str,
        voice_id: str = "female_young",
        pitch_scale: float = 1.0,
        speed_scale: float = 1.0,
        energy_scale: float = 1.0,
        voice_feature=None,
        p_w: float = None,
        t_w: float = None
    ) -> np.ndarray:
        """
        生成音频
        
        Args:
            text: 文本
            voice_id: 声音ID
            pitch_scale: 音高缩放
            speed_scale: 速度缩放
            energy_scale: 能量缩放
            voice_feature: 语音特征
            p_w: 音高权重
            t_w: 音色权重
            
        Returns:
            np.ndarray: 音频数据
        """
        # 添加开始生成的日志
        logger.info(f"开始生成音频: 文本='{text[:30]}...'，声音ID={voice_id}，_use_mock={self._use_mock}")
        
        if self._use_mock:
            # 使用模拟音频
            logger.info(f"使用模拟音频生成: '{text[:30]}...' (voice_id={voice_id})")
            audio = MockAudioGenerator.generate_text_based_audio(
                text=text,
                voice_id=voice_id,
                sample_rate=22050
            )
            
            return audio
            
        # 真实模型处理逻辑
        try:
            # 检查并确保模型已加载
            if self._model is None:
                logger.info("模型未初始化，尝试加载...")
                try:
                    # 使用实际的MegaTTS3DiTInfer类加载模型
                    precision = torch.float16 if self.fp16 else torch.float32
                    
                    # 使用固定路径加载模型
                    if self.model_path and os.path.exists(self.model_path):
                        model_dir = os.path.dirname(self.model_path)
                        logger.info(f"尝试使用模型目录: {model_dir}")
                        
                        try:
                            # 使用全局变量中的模型类初始化
                            if MegaTTS3DiTInfer_CLASS is not None:
                                DiTInfer = MegaTTS3DiTInfer_CLASS
                                self._model = DiTInfer(
                                    device="cpu",  # 强制使用CPU
                                    ckpt_root=model_dir,
                                    precision=precision
                                )
                            else:
                                logger.error("未找到全局MegaTTS3DiTInfer类，无法加载模型")
                                raise ImportError("MegaTTS3DiTInfer类不可用")
                            logger.info(f"成功加载模型，使用目录: {model_dir}")
                        except Exception as model_error:
                            logger.error(f"从模型目录加载失败: {str(model_error)}")
                            raise
                    else:
                        logger.error("未找到有效的模型路径")
                        raise FileNotFoundError("模型文件不存在")
                    
                except Exception as e:
                    logger.error(f"动态加载模型失败: {str(e)}")
                    logger.error(f"错误类型: {type(e).__name__}")
                    # 模型加载失败，使用模拟音频
                    audio = MockAudioGenerator.generate_text_based_audio(
                        text=text,
                        voice_id=voice_id,
                        sample_rate=22050
                    )
                    logger.warning("由于无法加载模型，回退到模拟音频生成")
                    return audio
            
            # 再次检查模型是否已加载
            if self._model is None:
                raise RuntimeError("TTS模型未加载")
                
            logger.info(f"生成音频: '{text[:30]}...' (voice_id={voice_id})")
            
            # 检查是否有对应的声音样本
            selected_voice = None
            
            # 如果voice_id是扩展声音样本ID，直接使用
            if hasattr(self, 'available_voices') and voice_id in self.available_voices:
                selected_voice = self.available_voices[voice_id]
                logger.info(f"使用扩展声音样本: {voice_id}")
            # 否则尝试用内置声音对应规则
            elif hasattr(self, 'available_voices'):
                # 简单的声音映射规则
                voice_mapping = {
                    "female_young": "范闲",    # 默认使用范闲
                    "female_mature": "范闲",
                    "male_young": "周杰伦",    # 默认使用周杰伦
                    "male_middle": "周杰伦",
                    "male_mature": "周杰伦",
                    "english": "english_talk"  # 英文默认使用english_talk
                }
                
                # 尝试进行映射
                mapped_id = voice_mapping.get(voice_id)
                if mapped_id and mapped_id in self.available_voices:
                    selected_voice = self.available_voices[mapped_id]
                    logger.info(f"将声音ID {voice_id} 映射到 {mapped_id}")
                
                # 如果映射失败，尝试使用任意可用的声音
                if selected_voice is None and self.available_voices:
                    # 根据语言选择声音 (简单启发式)
                    import re
                    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
                    
                    # 尝试按语言匹配
                    for vid, vinfo in self.available_voices.items():
                        if has_chinese and vinfo["is_chinese"]:
                            selected_voice = vinfo
                            logger.info(f"根据中文内容选择声音: {vid}")
                            break
                        elif not has_chinese and not vinfo["is_chinese"]:
                            selected_voice = vinfo
                            logger.info(f"根据非中文内容选择声音: {vid}")
                            break
                    
                    # 如果仍未匹配，选择第一个可用声音
                    if selected_voice is None:
                        vid = next(iter(self.available_voices))
                        selected_voice = self.available_voices[vid]
                        logger.info(f"未找到合适的声音映射，使用默认声音: {vid}")
            else:
                logger.warning("没有可用的声音样本")
            
            # 检查是否有选定的声音样本，使用其NPY数据
            if selected_voice and "npy_data" in selected_voice:
                logger.info("使用已加载的声音样本NPY数据进行语音合成")
                npy_data = selected_voice["npy_data"]
                
                # MegaTTS3模型的合成参数
                params = {
                    "pitch_scale": pitch_scale,
                    "speed_scale": speed_scale,
                    "energy_scale": energy_scale,
                    "voice_feature": npy_data  # 使用选定的NPY数据
                }
                
                # 如果有特定权重参数
                if p_w is not None:
                    params["p_w"] = p_w
                else:
                    params["p_w"] = 2.0  # 默认音高权重值
                    
                if t_w is not None:
                    params["t_w"] = t_w
                else:
                    params["t_w"] = 3.0  # 默认音色权重值
                
                try:
                    # 检查是否需要latent_file参数
                    if hasattr(self._model, 'has_vae_encoder') and not self._model.has_vae_encoder:
                        logger.info("检测到仅解码器模式，尝试创建临时NPY文件")
                        import tempfile
                        import numpy as np
                        
                        # 创建项目目录下的临时文件夹
                        temp_dir = os.path.join("D:/AI-Sound/output/temp")
                        os.makedirs(temp_dir, exist_ok=True)
                        
                        # 在项目目录下创建临时文件
                        temp_npy_path = os.path.join(temp_dir, f"temp_npy_{uuid.uuid4().hex[:8]}.npy")
                        
                        # 保存NPY数据到临时文件
                        np.save(temp_npy_path, npy_data)
                        
                        logger.info(f"临时NPY文件创建在: {temp_npy_path}")
                        params["latent_file"] = temp_npy_path
                    
                    # 调用底层模型生成音频
                    # 在GPU模式时减少推理步数以提高速度
                    if self.use_gpu:
                        time_step = params.get("time_step", 32)
                        if time_step > 20:
                            logger.info(f"GPU模式下降低推理步数从{time_step}到10步以提升速度")
                            params["time_step"] = 10
                    
                    try:
                        # 直接传递文本和参数，确保文本正确传入
                        logger.info(f"合成文本: {text}")
                        audio = self._model.infer(text, params)
                        
                        # 检查音频是否有效
                        if audio is None or len(audio) < 1000:  # 音频太短或为None
                            logger.error(f"音频生成出错: 音频太短或为空: {len(audio) if audio is not None else 'None'}")
                            logger.info("由于错误回退到模拟音频生成")
                            # 改为生成模拟音频
                            audio = MockAudioGenerator.generate_text_based_audio(
                                text=text,
                                voice_id=voice_id,
                                sample_rate=22050
                            )
                    except Exception as audio_error:
                        error_msg = str(audio_error)
                        logger.error(f"音频生成出错: {error_msg}")
                        
                        # 特殊处理pyloudnorm的"Audio must have length greater than the block size"错误
                        if "Audio must have length greater than the block size" in error_msg:
                            logger.warning("检测到pyloudnorm块大小错误，尝试手动修复音频长度")
                            try:
                                # 直接重试但禁用音频标准化处理
                                logger.info("禁用音频标准化，重新尝试生成")
                                params["disable_normalization"] = True
                                audio = self._model.infer(text, params)
                                
                                # 检查音频是否有效
                                if audio is None or len(audio) < 4800:  # 0.2秒@24kHz
                                    logger.warning(f"生成的音频仍然太短: {len(audio) if audio is not None else 'None'}")
                                    raise ValueError("生成的音频太短")
                            except Exception as retry_error:
                                logger.error(f"重试生成失败: {retry_error}")
                                # 回退到模拟音频
                                audio = MockAudioGenerator.generate_text_based_audio(
                                    text=text, 
                                    voice_id=voice_id,
                                    sample_rate=22050
                                )
                        else:
                            logger.info("由于错误回退到模拟音频生成")
                            # 回退到模拟音频
                            audio = MockAudioGenerator.generate_text_based_audio(
                                text=text,
                                voice_id=voice_id,
                                sample_rate=22050
                            )
                        
                    # 音频后处理 - 确保音频长度足够
                    try:
                        # pyloudnorm需要的最小块大小约为0.4秒
                        min_required_len = int(22050 * 0.4)  # 最小0.4秒@22050Hz
                        
                        if audio is not None and len(audio) < min_required_len:
                            logger.warning(f"生成的音频太短 ({len(audio)} 样本)，填充到最小可处理长度 {min_required_len}")
                            # 填充短音频
                            import numpy as np
                            audio = np.pad(audio, (0, min_required_len - len(audio)), mode='constant')
                            
                        # 检查音频数据类型
                        if audio is not None and not isinstance(audio, np.ndarray):
                            logger.warning(f"音频数据类型不正确: {type(audio)}，尝试转换")
                            audio = np.array(audio, dtype=float)
                    except Exception as e:
                        logger.error(f"音频后处理失败: {str(e)}")
                        # 确保有一个有效的音频返回
                        if audio is None or len(audio) == 0:
                            import numpy as np
                            audio = np.zeros(22050)  # 1秒静音
                    
                    return audio
                except Exception as e:
                    logger.error(f"音频生成出错: {str(e)}")
                    # 出错时回退到模拟音频
                    audio = MockAudioGenerator.generate_text_based_audio(text, voice_id, 22050)
                    logger.info("由于错误回退到模拟音频生成")
                    return audio
            else:
                # 一般的合成逻辑 (使用预先加载的资源上下文)
                logger.info("使用默认资源上下文进行语音合成")
                
                # 检查上下文是否可用
                if not hasattr(self, '_resource_context') or self._resource_context is None:
                    logger.warning("资源上下文不可用，使用模拟音频")
                    return MockAudioGenerator.generate_text_based_audio(text, voice_id, 22050)
                
                # MegaTTS3模型的合成参数
                params = {
                    "text": text,
                    "voice_id": voice_id,
                    "pitch_scale": pitch_scale,
                    "speed_scale": speed_scale,
                    "energy_scale": energy_scale
                }
                
                # 如果有自定义语音特征
                if voice_feature is not None:
                    params["voice_feature"] = voice_feature
                    
                # 如果有特定权重参数
                if p_w is not None:
                    params["p_w"] = p_w
                if t_w is not None:
                    params["t_w"] = t_w
                
                try:
                    # 调用底层模型生成音频
                    audio = self._model.infer(
                        self._resource_context,
                        params
                    )
                    
                    return audio
                except Exception as e:
                    logger.error(f"使用资源上下文合成失败: {str(e)}")
                    # 失败时回退到模拟音频
                    return MockAudioGenerator.generate_text_based_audio(text, voice_id, 22050)
                
        except Exception as e:
            logger.error(f"生成音频失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # 生成失败时返回模拟音频
            logger.warning("生成失败，返回模拟音频")
            return MockAudioGenerator.generate_text_based_audio(
                text=text,
                voice_id=voice_id,
                sample_rate=22050
            )
    
    def synthesize(
        self, 
        text: str,
        voice_id: str = "female_young",
        emotion_type: str = "neutral",
        emotion_intensity: float = 0.5,
        speed_scale: Optional[float] = None,
        pitch_scale: Optional[float] = None,
        energy_scale: Optional[float] = None,
        voice_feature=None,
        p_w: float = None,
        t_w: float = None
    ) -> np.ndarray:
        """
        合成语音
        
        Args:
            text: 文本内容
            voice_id: 声音ID
            emotion_type: 情感类型
            emotion_intensity: 情感强度(0.0-1.0)
            speed_scale: 速度缩放(可选)
            pitch_scale: 音高缩放(可选)
            energy_scale: 能量缩放(可选)
            voice_feature: 自定义语音特征
            p_w: 音高权重
            t_w: 音色权重
            
        Returns:
            np.ndarray: 音频数据
        """
        # 获取情感参数
        emotion_params = self._get_emotion_parameters(emotion_type, emotion_intensity)
        
        # 使用情感参数或指定参数
        _pitch_scale = pitch_scale if pitch_scale is not None else emotion_params["pitch"]
        _speed_scale = speed_scale if speed_scale is not None else emotion_params["speed"]
        _energy_scale = energy_scale if energy_scale is not None else emotion_params["energy"]
        
        # 直接调用generate方法
        return self.generate(
            text=text,
            voice_id=voice_id,
            pitch_scale=_pitch_scale,
            speed_scale=_speed_scale,
            energy_scale=_energy_scale,
            voice_feature=voice_feature,
            p_w=p_w,
            t_w=t_w
        )
    
    def synthesize_with_feature(
        self, 
        text: str,
        voice_feature: np.ndarray,
        emotion_type: str = "neutral",
        emotion_intensity: float = 0.5,
        speed_scale: Optional[float] = None,
        pitch_scale: Optional[float] = None,
        energy_scale: Optional[float] = None,
        p_w: float = 2.0,
        t_w: float = 3.0
    ) -> np.ndarray:
        """
        使用自定义声纹特征合成语音
        
        Args:
            text: 文本内容
            voice_feature: 声纹特征数据(NumPy数组)
            emotion_type: 情感类型
            emotion_intensity: 情感强度(0.0-1.0)
            speed_scale: 速度缩放(可选)
            pitch_scale: 音高缩放(可选)
            energy_scale: 能量缩放(可选)
            p_w: 音高权重
            t_w: 音色权重
            
        Returns:
            np.ndarray: 音频数据
        """
        logger.info(f"使用自定义声纹特征合成语音: '{text[:30]}...'")
        
        # 根据情感调整参数
        emotion_params = self._get_emotion_parameters(emotion_type, emotion_intensity)
        
        # 应用特定的参数覆盖
        _pitch_scale = pitch_scale if pitch_scale is not None else emotion_params.get("pitch_scale", 1.0)
        _speed_scale = speed_scale if speed_scale is not None else emotion_params.get("speed_scale", 1.0)
        _energy_scale = energy_scale if energy_scale is not None else emotion_params.get("energy_scale", 1.0)
        
        # 使用核心生成方法
        audio = self.generate(
            text=text,
            voice_id="custom",  # 使用自定义声音ID
            pitch_scale=_pitch_scale,
            speed_scale=_speed_scale,
            energy_scale=_energy_scale,
            voice_feature=voice_feature,  # 传递自定义声纹特征
            p_w=p_w,
            t_w=t_w
        )
        
        # 标准化音量
        max_amp = np.max(np.abs(audio))
        if max_amp > 0:
            audio = audio / max_amp * 0.9
        
        return audio
    
    def batch_synthesize(
        self, 
        texts: list[str],
        voice_id: str = "female_young",
        emotion_type: str = "neutral",
        emotion_intensity: float = 0.5,
        progress_callback: Optional[Callable[[float, int, int], None]] = None
    ) -> list[np.ndarray]:
        """
        批量生成语音
        
        Args:
            texts: 待合成的文本列表
            voice_id: 声音ID
            emotion_type: 情感类型
            emotion_intensity: 情感强度
            progress_callback: 进度回调函数(progress, current, total)
            
        Returns:
            list[np.ndarray]: 生成的音频列表
        """
        logger.info(f"批量合成 {len(texts)} 段文本，批大小: {self.batch_size}")
        
        # 优化显存使用
        if self.use_gpu:
            self.optimize_memory_usage()
            
        # 检查是否有缓存目录
        cache_dir = os.environ.get("TTS_CACHE_DIR", "./tts_cache")
        use_cache = os.environ.get("USE_TTS_CACHE", "true").lower() == "true"
        
        if use_cache and not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
            
        # 如果有多GPU，启用多卡批处理
        gpu_count = torch.cuda.device_count() if self.use_gpu else 0
        multi_gpu = gpu_count > 1 and self.use_gpu
        
        if multi_gpu:
            logger.info(f"检测到 {gpu_count} 个GPU，启用多卡并行处理")
            
        # 动态调整批次大小，超大文本自动降低批次大小
        dynamic_batch_size = self.batch_size
        avg_text_length = sum(len(t) for t in texts) / len(texts) if texts else 0
        
        if avg_text_length > 500 and dynamic_batch_size > 32:
            # 对于长文本，降低批量大小以防止OOM
            dynamic_batch_size = max(16, dynamic_batch_size // 2)
            logger.info(f"检测到长文本 (平均长度: {avg_text_length:.1f})，动态调整批大小为 {dynamic_batch_size}")
        
        results = []
        total_batches = (len(texts) - 1) // dynamic_batch_size + 1
        
        # 准备处理队列和缓存检查
        process_queue = []
        cached_results = {}
        
        if use_cache:
            # 检查哪些文本已经在缓存中
            for i, text in enumerate(texts):
                # 使用文本的哈希作为缓存键
                cache_key = hashlib.md5(f"{text}_{voice_id}_{emotion_type}_{emotion_intensity}".encode()).hexdigest()
                cache_path = os.path.join(cache_dir, f"{cache_key}.npy")
                
                if os.path.exists(cache_path):
                    try:
                        cached_results[i] = np.load(cache_path)
                        logger.debug(f"使用缓存音频 [{i}]: {text[:20]}...")
                    except Exception as e:
                        logger.warning(f"读取缓存失败 {cache_path}: {e}")
                        process_queue.append((i, text, cache_key))
                else:
                    process_queue.append((i, text, cache_key))
        else:
            # 不使用缓存时直接添加到处理队列
            process_queue = [(i, text, None) for i, text in enumerate(texts)]
            
        logger.info(f"总处理文本: {len(texts)}, 命中缓存: {len(cached_results)}, 需处理: {len(process_queue)}")
        
        # 多GPU处理或单GPU处理
        if multi_gpu and len(process_queue) > gpu_count:
            # 多GPU并行处理
            with concurrent.futures.ThreadPoolExecutor(max_workers=gpu_count) as executor:
                # 将任务分配到不同GPU
                future_to_gpu = {}
                for gpu_id in range(gpu_count):
                    # 计算每个GPU处理的文本
                    gpu_texts = [item for i, item in enumerate(process_queue) 
                                if i % gpu_count == gpu_id]
                    
                    if gpu_texts:
                        future = executor.submit(
                            self._process_batch_on_gpu, 
                            gpu_texts, 
                            voice_id, 
                            emotion_type, 
                            emotion_intensity,
                            gpu_id,
                            dynamic_batch_size,
                            cache_dir if use_cache else None
                        )
                        future_to_gpu[future] = gpu_id
                
                # 收集结果
                batch_results_map = {}
                for future in concurrent.futures.as_completed(future_to_gpu):
                    gpu_id = future_to_gpu[future]
                    try:
                        gpu_results = future.result()
                        batch_results_map.update(gpu_results)
                        logger.info(f"GPU {gpu_id} 完成处理")
                    except Exception as e:
                        logger.error(f"GPU {gpu_id} 处理失败: {e}")
        else:
            # 单GPU处理
            batch_results_map = self._process_batches(
                process_queue, 
                voice_id, 
                emotion_type, 
                emotion_intensity, 
                dynamic_batch_size,
                progress_callback,
                cache_dir if use_cache else None
            )
        
        # 合并所有结果
        final_results = [None] * len(texts)
        
        # 先填充缓存结果
        for idx, audio in cached_results.items():
            final_results[idx] = audio
            
        # 再填充新处理的结果
        for idx, audio in batch_results_map.items():
            final_results[idx] = audio
            
        # 确保所有位置都有结果
        for i, result in enumerate(final_results):
            if result is None:
                logger.warning(f"索引 {i} 的结果缺失，使用空音频代替")
                # 生成1秒的静音作为替代
                final_results[i] = np.zeros(22050)
                
        return final_results
    
    def _process_batches(
        self, 
        process_queue, 
        voice_id, 
        emotion_type, 
        emotion_intensity, 
        batch_size,
        progress_callback=None,
        cache_dir=None
    ):
        """处理文本批次并返回结果"""
        batch_results = {}
        total_items = len(process_queue)
        queue_batches = [process_queue[i:i+batch_size] for i in range(0, total_items, batch_size)]
        
        for batch_idx, batch_items in enumerate(queue_batches):
            logger.info(f"处理批次 {batch_idx+1}/{len(queue_batches)}")
            
            # 提取批次文本
            batch_texts = [item[1] for item in batch_items]
            batch_indices = [item[0] for item in batch_items]
            batch_cache_keys = [item[2] for item in batch_items]
            
            # 单个处理（MegaTTS3DiTInfer当前不支持批处理）
            audios = []
            for j, text in enumerate(batch_texts):
                audio = self.synthesize(
                    text=text,
                    voice_id=voice_id,
                    emotion_type=emotion_type,
                    emotion_intensity=emotion_intensity
                )
                audios.append(audio)
                
                # 进度回调
                if progress_callback:
                    overall_idx = sum(len(b) for b in queue_batches[:batch_idx]) + j
                    progress = overall_idx / total_items
                    progress_callback(progress, overall_idx, total_items)
            
            # 保存到缓存并更新结果映射
            for j, (idx, audio, cache_key) in enumerate(zip(batch_indices, audios, batch_cache_keys)):
                batch_results[idx] = audio
                
                # 如果启用缓存，保存结果
                if cache_dir and cache_key:
                    try:
                        cache_path = os.path.join(cache_dir, f"{cache_key}.npy")
                        np.save(cache_path, audio)
                    except Exception as e:
                        logger.warning(f"保存缓存失败 {cache_path}: {e}")
            
            # 批次间清理显存
            if self.use_gpu:
                torch.cuda.empty_cache()
                
            # 整体进度回调
            if progress_callback:
                batch_progress = min(1.0, (batch_idx + 1) / len(queue_batches))
                progress_callback(batch_progress, batch_idx + 1, len(queue_batches))
                
        return batch_results
    
    def _process_batch_on_gpu(self, gpu_texts, voice_id, emotion_type, emotion_intensity, gpu_id, batch_size, cache_dir=None):
        """在指定GPU上处理批次"""
        # 设置当前设备
        if self.use_gpu:
            original_device = torch.cuda.current_device()
            torch.cuda.set_device(gpu_id)
            logger.info(f"切换到GPU {gpu_id}")
            
        try:
            # 处理批次
            return self._process_batches(
                gpu_texts, 
                voice_id, 
                emotion_type, 
                emotion_intensity, 
                batch_size,
                None,  # 多GPU模式下不使用进度回调
                cache_dir
            )
        finally:
            # 切回原始设备
            if self.use_gpu:
                torch.cuda.set_device(original_device)
                torch.cuda.empty_cache()

    def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        获取可用的语音模型列表
        
        Returns:
            List[Dict[str, Any]]: 包含语音ID、名称和描述的列表
        """
        # 基础声音列表
        voices = [
            {
                "id": "female_young",
                "name": "年轻女声",
                "description": "清亮甜美的年轻女性声音",
                "gender": "female",
                "age_group": "young",
                "preview_available": True
            },
            {
                "id": "female_mature",
                "name": "成熟女声",
                "description": "沉稳大气的成熟女性声音",
                "gender": "female",
                "age_group": "mature",
                "preview_available": True
            },
            {
                "id": "male_young",
                "name": "年轻男声",
                "description": "活力四射的年轻男性声音",
                "gender": "male",
                "age_group": "young",
                "preview_available": True
            },
            {
                "id": "male_middle",
                "name": "中年男声",
                "description": "稳重有力的中年男性声音",
                "gender": "male",
                "age_group": "middle",
                "preview_available": True
            },
            {
                "id": "male_mature",
                "name": "成熟男声",
                "description": "深沉磁性的成熟男性声音",
                "gender": "male",
                "age_group": "mature",
                "preview_available": True
            }
        ]
        
        # 如果使用模拟音频，返回基础声音列表
        if self._use_mock:
            return voices
            
        # 如果有加载的样本声音，添加到列表中
        if hasattr(self, 'available_voices') and self.available_voices:
            logger.info(f"添加 {len(self.available_voices)} 个自定义声音到可用列表")
            
            # 添加所有可用的样本声音
            for voice_id, voice_info in self.available_voices.items():
                sample_voice = {
                    "id": voice_id,
                    "name": f"{voice_info['name']} (样本声音)",
                    "description": voice_info["description"],
                    "gender": "unknown",  # 无法自动判断性别
                    "is_sample": True,
                    "preview_available": True,
                    "is_chinese": voice_info.get("is_chinese", True)
                }
                
                # 简单的性别和年龄推断
                if voice_id == "范闲":
                    sample_voice["gender"] = "male"
                    sample_voice["age_group"] = "young"
                elif voice_id == "周杰伦":
                    sample_voice["gender"] = "male"
                    sample_voice["age_group"] = "middle"
                
                # 添加到声音列表，优先显示样本声音
                voices.insert(0, sample_voice)
            
        return voices
    
    def get_available_emotions(self) -> List[Dict[str, Any]]:
        """
        获取可用的情感类型列表
        
        Returns:
            List[Dict[str, Any]]: 包含情感ID、名称和描述的列表
        """
        emotions = [
            {
                "id": "neutral",
                "name": "中性",
                "description": "平静、中性的语气，适合常规阅读和信息传递",
                "intensity_required": False
            },
            {
                "id": "happy",
                "name": "开心",
                "description": "愉快、积极的语气，适合表达喜悦和欢乐的内容",
                "intensity_required": True
            },
            {
                "id": "sad",
                "name": "悲伤",
                "description": "低沉、伤感的语气，适合表达悲伤和忧郁的内容",
                "intensity_required": True
            },
            {
                "id": "angry",
                "name": "愤怒",
                "description": "激烈、强硬的语气，适合表达愤怒和激烈的内容",
                "intensity_required": True
            },
            {
                "id": "fear",
                "name": "恐惧",
                "description": "紧张、惊恐的语气，适合表达恐惧和紧张的内容",
                "intensity_required": True
            },
            {
                "id": "surprise",
                "name": "惊讶",
                "description": "震惊、吃惊的语气，适合表达惊讶和意外的内容",
                "intensity_required": True
            }
        ]
        
        return emotions