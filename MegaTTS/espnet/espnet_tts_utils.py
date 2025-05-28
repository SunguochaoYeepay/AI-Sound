import os
import inspect
from espnet2.bin.tts_inference import Text2Speech
import torch

MODEL_ROOT = "exp"
PARAMS = ["pitch", "energy", "speed", "spk_id"]

# 扫描模型目录，返回模型信息列表
def find_models():
    models = []
    for d in os.listdir(MODEL_ROOT):
        model_dir = os.path.join(MODEL_ROOT, d)
        if not os.path.isdir(model_dir):
            continue
        config_path = os.path.join(model_dir, "config.yaml")
        pth_files = [f for f in os.listdir(model_dir) if f.endswith(".pth")]
        if os.path.exists(config_path) and pth_files:
            models.append({
                "name": d,
                "config": config_path,
                "weight": os.path.join(model_dir, pth_files[0])
            })
    return models

# 创建 TTS 推理引擎
def create_tts(config_path, weight_path):
    return Text2Speech(
        train_config=config_path,
        model_file=weight_path,
        device="cuda" if torch.cuda.is_available() else "cpu"
    )

# 获取模型支持的参数
def get_supported_params(config_path, weight_path):
    tts = create_tts(config_path, weight_path)
    sig = inspect.signature(tts.__call__)
    return [p for p in PARAMS if p in sig.parameters]

# 获取所有模型及参数信息
def get_all_models_with_params():
    models = find_models()
    for m in models:
        m["supported_params"] = get_supported_params(m["config"], m["weight"])
    return models
