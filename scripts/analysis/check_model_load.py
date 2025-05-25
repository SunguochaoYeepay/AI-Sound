"""
模型加载测试脚本
检查MegaTTS3模型加载状态和声音特征文件可用性
"""

import os
import sys
import torch
import logging
import numpy as np

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("model_check")

def check_files_existence():
    """检查必要文件是否存在"""
    print("\n===== 检查文件 =====")
    
    # 模型文件
    model_paths = [
        "D:/AI-Sound/data/checkpoints/megatts3_base.pth",
        "./data/checkpoints/megatts3_base.pth", 
        "./checkpoints/megatts3_base.pth"
    ]
    
    found_model = False
    for path in model_paths:
        if os.path.exists(path):
            print(f"✅ 找到模型文件: {path}")
            found_model = True
        else:
            print(f"❌ 未找到模型文件: {path}")
    
    if not found_model:
        print("警告: 未找到主模型文件，TTS将使用模拟音频!")
    
    # 检查声音样本文件
    voice_sample_paths = [
        "./services/data/voice_features/",
        "D:/AI-Sound/services/data/voice_features/",
        "./test_voices/"
    ]
    
    found_samples = False
    for path in voice_sample_paths:
        if os.path.exists(path):
            print(f"✅ 找到声音样本目录: {path}")
            npy_files = [f for f in os.listdir(path) if f.endswith('.npy')]
            if npy_files:
                print(f"   包含 {len(npy_files)} 个NPY文件: {', '.join(npy_files[:3])}{'...' if len(npy_files) > 3 else ''}")
                found_samples = True
            else:
                print(f"   但目录中没有NPY文件")
        else:
            print(f"❌ 未找到声音样本目录: {path}")
    
    if not found_samples:
        print("警告: 未找到声音特征文件，这可能导致无法正确生成不同声音!")
    
    # 检查WaveVAE解码器文件
    wavvae_paths = [
        "D:/AI-Sound/data/checkpoints/wavvae/decoder.ckpt",
        "./data/checkpoints/wavvae/decoder.ckpt", 
        "./checkpoints/wavvae/decoder.ckpt"
    ]
    
    found_decoder = False
    for path in wavvae_paths:
        if os.path.exists(path):
            print(f"✅ 找到WaveVAE解码器: {path}")
            found_decoder = True
        else:
            print(f"❌ 未找到WaveVAE解码器: {path}")
    
    if not found_decoder:
        print("警告: 未找到WaveVAE解码器，这可能导致无法正确合成语音!")
    
    return found_model and found_samples and found_decoder

def check_python_paths():
    """检查Python路径和环境变量"""
    print("\n===== 检查环境 =====")
    
    # 检查PYTHONPATH
    pythonpath = os.environ.get('PYTHONPATH', '')
    print(f"PYTHONPATH: {pythonpath}")
    
    if 'MegaTTS3' not in pythonpath and 'D:\\AI-Sound\\MegaTTS3' not in pythonpath:
        print("❌ PYTHONPATH中缺少MegaTTS3路径")
    
    # 检查系统路径
    for path in sys.path:
        if 'MegaTTS3' in path:
            print(f"✅ 系统路径包含MegaTTS3: {path}")
            break
    else:
        print("❌ 系统路径中不包含MegaTTS3")
    
    # 检查CUDA可用性
    print(f"\n===== 检查CUDA =====")
    print(f"CUDA是否可用: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA设备数量: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"  设备 {i}: {torch.cuda.get_device_name(i)}")
    else:
        print("CUDA不可用，将使用CPU进行推理")

def try_load_model():
    """尝试加载MegaTTS3模型"""
    print("\n===== 尝试加载模型 =====")
    
    # 添加MegaTTS3到路径
    sys.path.insert(0, 'D:/AI-Sound/MegaTTS3')
    
    try:
        # 尝试导入MegaTTS3
        from MegaTTS3.tts.infer_cli import MegaTTS3DiTInfer
        print("✅ 成功导入MegaTTS3DiTInfer类")
        
        # 尝试创建模型实例
        model_paths = [
            "D:/AI-Sound/data/checkpoints",
            "./data/checkpoints", 
            "./checkpoints"
        ]
        
        loaded = False
        for model_path in model_paths:
            if os.path.exists(model_path):
                print(f"尝试从 {model_path} 加载模型...")
                try:
                    model = MegaTTS3DiTInfer(
                        device="cpu",
                        ckpt_root=model_path
                    )
                    print(f"✅ 成功从 {model_path} 加载模型")
                    loaded = True
                    break
                except Exception as e:
                    print(f"❌ 从 {model_path} 加载模型失败: {str(e)}")
        
        if not loaded:
            print("❌ 所有路径都无法加载模型")
        
        return loaded
    except ImportError as e:
        print(f"❌ 导入MegaTTS3模块失败: {str(e)}")
        print("请确保MegaTTS3已正确安装并添加到系统路径")
        return False
    except Exception as e:
        print(f"❌ 模型加载过程中发生错误: {str(e)}")
        return False

def check_mock_audio():
    """检查是否使用模拟音频"""
    print("\n===== 检查模拟音频状态 =====")
    
    try:
        from services.api.src.tts.engine import MEGATTS_AVAILABLE
        print(f"MEGATTS_AVAILABLE = {MEGATTS_AVAILABLE}")
        
        if MEGATTS_AVAILABLE:
            print("✅ 系统配置为使用真实TTS")
        else:
            print("❌ 系统配置为使用模拟音频")
            print("可能原因:")
            print("  1. 缺少必要依赖")
            print("  2. 未找到MegaTTS3模块")
            print("  3. 模型文件路径不正确")
    except ImportError:
        print("❌ 无法导入engine模块，请确保当前目录是项目根目录")

def main():
    """主函数"""
    print("===== MegaTTS3 模型诊断工具 =====")
    print(f"当前工作目录: {os.getcwd()}")
    
    files_ok = check_files_existence()
    check_python_paths()
    model_load_ok = try_load_model()
    check_mock_audio()
    
    print("\n===== 诊断结果 =====")
    if files_ok and model_load_ok:
        print("✅ 所有必要文件都存在且模型可以加载")
        print("建议操作: 修改engine.py，强制使用真实TTS模型而非模拟音频")
    else:
        if not files_ok:
            print("❌ 缺少必要文件")
            print("建议操作: 下载缺失的模型文件和声音特征文件")
        
        if not model_load_ok:
            print("❌ 模型加载失败")
            print("建议操作: 检查模型路径和依赖安装")
    
    print("\n完成诊断。")

if __name__ == "__main__":
    main() 