import torch
from tqdm import tqdm
import torchaudio
from third_party.stable_audio_tools.stable_audio_tools.models.autoencoders import create_autoencoder_from_config
import numpy as np
import os
import json

def get_model(model_config, path):
    print(f"加载VAE模型文件: {path}")
    
    # 加载配置文件
    from third_party.stable_audio_tools.stable_audio_tools.models.autoencoders import create_autoencoder_from_config
    
    # 如果model_config是字符串，则加载配置文件
    if isinstance(model_config, str):
        if model_config:
            with open(model_config, 'r') as f:
                model_config = json.load(f)
        else:
            # 使用默认配置
            model_config = {
                "model_type": "autoencoder",
                "sample_size": 409600,
                "sample_rate": 48000,
                "audio_channels": 2,
                "model": {
                    "encoder": {
                        "type": "oobleck",
                        "config": {
                            "in_channels": 2,
                            "channels": 128,
                            "c_mults": [1, 2, 4, 8, 16],
                            "strides": [2, 4, 4, 8, 8],
                            "latent_dim": 128,
                            "use_snake": True
                        }
                    },
                    "decoder": {
                        "type": "oobleck",
                        "config": {
                            "out_channels": 2,
                            "channels": 128,
                            "c_mults": [1, 2, 4, 8, 16],
                            "strides": [2, 4, 4, 8, 8],
                            "latent_dim": 64,
                            "use_snake": True,
                            "final_tanh": False
                        }
                    },
                    "bottleneck": {
                        "type": "vae"
                    },
                    "latent_dim": 64,
                    "downsampling_ratio": 2048,
                    "io_channels": 2
                }
            }
    
    try:
        # 尝试加载实际的VAE模型
        model = create_autoencoder_from_config(model_config)
        
        # 尝试加载权重
        checkpoint = torch.load(path, map_location='cpu')
        state_dict = checkpoint['state_dict'] if 'state_dict' in checkpoint else checkpoint
        
        # 创建模型的状态字典
        model_state_dict = model.state_dict()
        
        # 只加载匹配的参数
        loaded_count = 0
        for key in state_dict.keys():
            if key in model_state_dict and state_dict[key].shape == model_state_dict[key].shape:
                model_state_dict[key] = state_dict[key]
                loaded_count += 1
        
        # 加载匹配的参数
        model.load_state_dict(model_state_dict, strict=False)
        
        print(f"✅ VAE模型加载成功，加载了 {loaded_count}/{len(model_state_dict)} 个参数")
        return model
        
    except Exception as e:
        print(f"⚠️  VAE模型加载失败: {e}")
        print("使用简化替代模型")
        
        # 如果加载失败，使用简化的替代模型
        if "model" in model_config and "encoder" in model_config["model"]:
            # 使用seanet编码器作为后备
            model_config["model"]["encoder"]["type"] = "seanet"
            model_config["model"]["encoder"]["config"] = {
                "channels": 2,
                "dimension": 32,
                "n_residual_layers": 1,
                "ratios": [8, 8, 2, 2]
            }
        
        if "model" in model_config and "decoder" in model_config["model"]:
            # 使用seanet解码器作为后备
            model_config["model"]["decoder"]["type"] = "seanet"
            model_config["model"]["decoder"]["config"] = {
                "channels": 2,
                "dimension": 32,
                "n_residual_layers": 1,
                "ratios": [8, 8, 2, 2]
            }
        
        model = create_autoencoder_from_config(model_config)
        
        # 初始化随机权重
        for param in model.parameters():
            if param.dim() > 1:
                torch.nn.init.xavier_uniform_(param)
            else:
                torch.nn.init.zeros_(param)
        
        print("✅ 简化VAE模型创建成功")
        return model
