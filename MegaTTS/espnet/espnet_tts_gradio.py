import gradio as gr
from espnet2.bin.tts_inference import Text2Speech
import torch
import soundfile as sf
import numpy as np
import tempfile
import argparse
import os
from glob import glob
import inspect

# 自动扫描模型目录
MODEL_ROOT = "exp"
def find_models():
    models = []
    for d in os.listdir(MODEL_ROOT):
        model_dir = os.path.join(MODEL_ROOT, d)
        if not os.path.isdir(model_dir):
            continue
        config_path = os.path.join(model_dir, "config.yaml")
        # 支持多种权重命名
        pth_files = [f for f in os.listdir(model_dir) if f.endswith(".pth")]
        if os.path.exists(config_path) and pth_files:
            models.append({
                "name": d,
                "config": config_path,
                "weight": os.path.join(model_dir, pth_files[0])
            })
    return models

MODELS = find_models()
MODEL_NAME2INFO = {m["name"]: m for m in MODELS}

# 判断模型类型（VITS 支持 pitch/energy/speed）
def is_vits_model(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()
    return "vits" in content.lower()

# 默认加载第一个模型
current_model = MODELS[0]
def create_tts(config_path, weight_path):
    return Text2Speech(
        train_config=config_path,
        model_file=weight_path,
        device="cuda" if torch.cuda.is_available() else "cpu"
    )

tts_engine = create_tts(current_model["config"], current_model["weight"])

# 检查模型支持哪些推理参数
PARAMS = ["pitch", "energy", "speed", "spk_id"]
def get_supported_params(config_path, weight_path):
    tts = create_tts(config_path, weight_path)
    sig = inspect.signature(tts.__call__)
    return [p for p in PARAMS if p in sig.parameters]

# Gradio 交互函数

def tts_fn(text, model_name, *args):
    global tts_engine, current_model
    model_info = MODEL_NAME2INFO[model_name]
    if current_model["name"] != model_name:
        tts_engine = create_tts(model_info["config"], model_info["weight"])
        current_model = model_info
    supported = get_supported_params(model_info["config"], model_info["weight"])
    kwargs = {}
    for i, param in enumerate(supported):
        kwargs[param] = args[i]
    try:
        result = tts_engine(text, **kwargs)
    except Exception as e:
        return None, f"合成失败: {e}"
    wav = result["wav"].view(-1).cpu().numpy()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, wav, 24000)
        return f.name, None

# 构建 Gradio 界面
model_names = [m["name"] for m in MODELS]
def build_interface():
    default_model = model_names[0]
    model_info = MODEL_NAME2INFO[default_model]
    supported_params = get_supported_params(model_info["config"], model_info["weight"])
    inputs = [
        gr.Textbox(label="输入文本", lines=5, placeholder="请输入要合成的中文文本..."),
        gr.Dropdown(choices=model_names, value=default_model, label="选择模型")
    ]
    param_indices = {}
    for param in supported_params:
        if param == "pitch":
            inputs.append(gr.Slider(0.5, 2.0, value=1.0, step=0.01, label="音高 pitch"))
            param_indices["pitch"] = len(inputs) - 1
        if param == "energy":
            inputs.append(gr.Slider(0.5, 2.0, value=1.0, step=0.01, label="能量 energy"))
            param_indices["energy"] = len(inputs) - 1
        if param == "speed":
            inputs.append(gr.Slider(0.5, 2.0, value=1.0, step=0.01, label="语速 speed"))
            param_indices["speed"] = len(inputs) - 1
        if param == "spk_id":
            inputs.append(gr.Number(value=0, label="说话人ID spk_id"))
            param_indices["spk_id"] = len(inputs) - 1
    outputs = [gr.Audio(label="合成音频"), gr.Textbox(label="提示信息")]
    return gr.Interface(
        fn=tts_fn,
        inputs=inputs,
        outputs=outputs,
        title="ESPnet TTS 多模型简易Web界面",
        description="自动扫描exp/下所有模型，支持一键切换和参数自适应。"
    )

iface = build_interface()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5001, help="服务端口，默认5001")
    args = parser.parse_args()
    iface.launch(server_name="0.0.0.0", server_port=args.port)
