#!/usr/bin/env python3
"""
测试MegaTTS3模块的导入和基本功能
"""

import os
import sys
import torch

# 添加路径
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "MegaTTS3"))

print(f"当前工作目录: {os.getcwd()}")
print(f"Python路径: {sys.path}")

try:
    # 测试导入
    print("测试导入tn模块...")
    from MegaTTS3.tn.chinese.normalizer import Normalizer as ZhNormalizer
    from MegaTTS3.tn.english.normalizer import Normalizer as EnNormalizer
    print("成功导入tn模块")
    
    # 测试normalizer
    zh_normalizer = ZhNormalizer()
    text = "测试文本123"
    print(f"原始文本: {text}")
    normalized = zh_normalizer.normalize(text)
    print(f"归一化后: {normalized}")
    
    try:
        print("\n测试导入MegaTTS3DiTInfer...")
        from MegaTTS3.tts.infer_cli import MegaTTS3DiTInfer
        print("成功导入MegaTTS3DiTInfer")
        
        # 检查是否存在所需的配置文件
        ckpt_root = "D:/AI-Sound/data/checkpoints"
        required_files = [
            os.path.join(ckpt_root, "duration_lm", "config.yaml"),
            os.path.join(ckpt_root, "duration_lm", "model_only_last.ckpt"),
            os.path.join(ckpt_root, "wavvae", "config.yaml"),
            os.path.join(ckpt_root, "wavvae", "model_only_last.ckpt"),
            os.path.join(ckpt_root, "diffusion_transformer", "model_only_last.ckpt"),
            os.path.join(ckpt_root, "aligner_lm", "model_only_last.ckpt"),
            os.path.join(ckpt_root, "voice_samples", "范闲.wav")
        ]
        
        for file_path in required_files:
            print(f"检查文件: {file_path}, 是否存在: {os.path.exists(file_path)}")
    except Exception as e:
        print(f"导入或检查MegaTTS3DiTInfer失败: {str(e)}")
except Exception as e:
    print(f"导入失败: {str(e)}") 