"""
直接使用TTS引擎测试脚本
不通过API，直接调用engine.py中的方法
"""

import os
import sys
import numpy as np
from scipy.io import wavfile
import logging

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("direct_tts_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("direct_tts_test")

# 添加src目录到系统路径
sys.path.append(os.path.join(os.getcwd(), "services", "api", "src"))
sys.path.append(os.path.join(os.getcwd(), "services", "api"))
sys.path.append(os.path.join(os.getcwd(), "MegaTTS3"))

# 确保输出目录存在
os.makedirs("direct_test_output", exist_ok=True)

def test_basic_tts():
    """基本TTS测试"""
    logger.info("开始基本TTS测试")
    
    try:
        # 导入TTS引擎
        from tts.engine import MegaTTSEngine, MEGATTS_AVAILABLE
        
        # 检查是否可用
        logger.info(f"MegaTTS3是否可用: {MEGATTS_AVAILABLE}")
        
        # 创建引擎实例
        logger.info("正在创建TTS引擎实例...")
        engine = MegaTTSEngine(
            model_path="D:/AI-Sound/data/checkpoints/megatts3_base.pth",
            use_gpu=False  # 使用CPU避免任何GPU问题
        )
        
        logger.info(f"TTS引擎创建完成，_use_mock={engine._use_mock}")
        
        # 获取可用的声音
        voices = engine.get_available_voices()
        logger.info(f"可用声音: {[v['id'] for v in voices]}")
        
        # 测试简短文本
        test_text = "这是一个测试，看看能否正常生成语音。"
        
        # 测试不同声音
        test_voices = ["范闲", "周杰伦", "english_talk"]
        
        for voice_id in test_voices:
            logger.info(f"测试声音: {voice_id}")
            try:
                # 生成音频
                logger.info(f"生成文本: {test_text}")
                audio = engine.synthesize(
                    text=test_text,
                    voice_id=voice_id
                )
                
                # 检查音频
                if audio is None:
                    logger.error("生成的音频为None")
                    continue
                    
                logger.info(f"生成的音频形状: {audio.shape}, 类型: {audio.dtype}")
                
                # 保存音频
                output_path = os.path.join("direct_test_output", f"{voice_id}_test.wav")
                wavfile.write(output_path, 22050, audio.astype(np.float32))
                logger.info(f"音频已保存到: {output_path}")
                
                # 检查文件大小
                file_size = os.path.getsize(output_path) / 1024  # KB
                logger.info(f"文件大小: {file_size:.2f} KB")
                
                # 判断是否为模拟音频
                if file_size < 10:
                    logger.warning(f"生成的可能是模拟音频 (大小: {file_size:.2f} KB)")
                else:
                    logger.info(f"生成的应该是真实音频 (大小: {file_size:.2f} KB)")
                
            except Exception as e:
                logger.error(f"测试声音 {voice_id} 时出错: {str(e)}", exc_info=True)
    
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}", exc_info=True)

def test_voice_features():
    """测试声音特征处理"""
    logger.info("\n开始测试声音特征处理")
    
    try:
        # 导入TTS引擎
        from tts.engine import MegaTTSEngine
        
        # 创建引擎实例
        engine = MegaTTSEngine(use_gpu=False)
        
        # 检查NPY文件目录
        voice_sample_dirs = [
            "D:/AI-Sound/data/checkpoints/voice_samples",
            "./data/checkpoints/voice_samples",
            "./voice_samples"
        ]
        
        for dir_path in voice_sample_dirs:
            if os.path.exists(dir_path):
                logger.info(f"找到声音样本目录: {dir_path}")
                npy_files = [f for f in os.listdir(dir_path) if f.endswith('.npy')]
                logger.info(f"NPY文件: {npy_files}")
                
                if npy_files:
                    # 加载一个NPY文件
                    npy_path = os.path.join(dir_path, npy_files[0])
                    logger.info(f"加载NPY文件: {npy_path}")
                    
                    try:
                        data = np.load(npy_path)
                        logger.info(f"NPY数据形状: {data.shape}, 类型: {data.dtype}")
                        
                        # 检查维度
                        if len(data.shape) == 3:
                            logger.info("✅ 正确的3D格式")
                        elif len(data.shape) == 2:
                            logger.warning(f"⚠️ 2D格式，需要转换为3D: {data.shape} -> [1, {data.shape[0]}, {data.shape[1]}]")
                            # 转换为3D
                            data = data.reshape(1, data.shape[0], data.shape[1])
                            logger.info(f"转换后的形状: {data.shape}")
                        
                        # 测试使用这个特征生成语音
                        test_text = "这是使用声音特征生成的语音测试。"
                        logger.info(f"使用NPY特征生成文本: {test_text}")
                        
                        try:
                            audio = engine.synthesize_with_feature(
                                text=test_text,
                                voice_feature=data
                            )
                            
                            # 保存音频
                            output_path = os.path.join("direct_test_output", f"feature_test_{os.path.basename(npy_path)}.wav")
                            wavfile.write(output_path, 22050, audio.astype(np.float32))
                            logger.info(f"使用特征生成的音频已保存到: {output_path}")
                            
                            # 检查文件大小
                            file_size = os.path.getsize(output_path) / 1024  # KB
                            logger.info(f"文件大小: {file_size:.2f} KB")
                            
                            # 判断是否为模拟音频
                            if file_size < 10:
                                logger.warning(f"生成的可能是模拟音频 (大小: {file_size:.2f} KB)")
                            else:
                                logger.info(f"生成的应该是真实音频 (大小: {file_size:.2f} KB)")
                                
                        except Exception as e:
                            logger.error(f"使用特征生成语音时出错: {str(e)}", exc_info=True)
                        
                    except Exception as e:
                        logger.error(f"加载NPY文件 {npy_path} 时出错: {str(e)}", exc_info=True)
                    
                    break
    
    except Exception as e:
        logger.error(f"测试声音特征时出错: {str(e)}", exc_info=True)

def main():
    """主函数"""
    logger.info("=== 开始直接TTS测试 ===")
    logger.info(f"当前工作目录: {os.getcwd()}")
    logger.info(f"Python路径: {sys.path}")
    
    # 基本TTS测试
    test_basic_tts()
    
    # 声音特征测试
    test_voice_features()
    
    logger.info("=== 测试完成 ===")

if __name__ == "__main__":
    main() 