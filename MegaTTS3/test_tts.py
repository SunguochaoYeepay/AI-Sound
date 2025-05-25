import os
import sys
import numpy as np
import soundfile as sf
import torch

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 设置环境变量
os.environ["SAMPLE_WAV_PATH"] = os.path.abspath(os.path.join("..", "data", "checkpoints", "voice_samples", "范闲.wav"))

# 导入真实的MegaTTS3引擎
from tts.infer_cli import MegaTTS3DiTInfer
from tts.utils.audio_utils.io import to_wav_bytes, save_wav

def test_tts():
    # 初始化TTS引擎
    engine = MegaTTS3DiTInfer()
    
    # 测试文本
    test_texts = [
        "你好，这是一个测试。",
        "Hello, this is a test.",
        "今天天气真不错！",
        "让我们来测试一下中英文混合：Hello 世界！"
    ]
    
    # 创建输出目录
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 使用范闲的声音作为参考
    sample_wav_path = os.path.abspath(os.path.join("..", "data", "checkpoints", "voice_samples", "范闲.wav"))
    latent_file = sample_wav_path.replace('.wav', '.npy')
    print(f"使用参考音频: {sample_wav_path}")
    print(f"使用特征文件: {latent_file}")
    
    # 读取参考音频
    with open(sample_wav_path, 'rb') as f:
        audio_bytes = f.read()
    
    # 获取资源上下文
    resource_context = engine.preprocess(audio_bytes, latent_file=latent_file)
    
    # 测试不同的声音和参数
    for i, text in enumerate(test_texts):
        print(f"\n测试文本 {i+1}: {text}")
        
        # 生成语音
        output_path = os.path.join(output_dir, f"test_{i+1}.wav")
        
        # 直接使用forward方法生成语音
        wav_bytes = engine.forward(
            resource_context=resource_context,
            input_text=text,
            time_step=16,      # 扩散步数
            p_w=2.0,          # 音高权重
            t_w=3.0,          # 音色权重
            dur_disturb=0.2,  # 持续时间扰动
            dur_alpha=1.0,    # 语速控制
            disable_normalization=True  # 禁用音量标准化
        )
        
        # 保存音频
        save_wav(wav_bytes, output_path)
        print(f"已生成语音: {output_path}")

if __name__ == "__main__":
    print("开始MegaTTS3测试...")
    test_tts()
    print("\n测试完成！") 