import gradio as gr
from espnet2.bin.tts_inference import Text2Speech
import torch
import soundfile as sf
import numpy as np
import tempfile
import argparse

# 用本地模型
text2speech = Text2Speech(
    train_config="exp/tts_train_raw_phn_pypinyin_g2p_phone/config.yaml",
    model_file="exp/tts_train_raw_phn_pypinyin_g2p_phone/valid.acc.ave.pth",
    device="cuda" if torch.cuda.is_available() else "cpu"
)

def tts_fn(text):
    if not text or not text.strip():
        return None, "请输入要合成的文本"
    result = text2speech(text)
    wav = result["wav"].view(-1).cpu().numpy()
    # 保存到临时文件
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, wav, 24000)
        return f.name, None

iface = gr.Interface(
    fn=tts_fn,
    inputs=gr.Textbox(label="输入文本", lines=5, placeholder="请输入要合成的中文文本..."),
    outputs=[gr.Audio(label="合成音频"), gr.Textbox(label="提示信息")],
    title="ESPnet TTS 简易Web界面",
    description="输入中文文本，点击按钮即可合成语音并在线试听。"
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5001, help="服务端口，默认5001")
    args = parser.parse_args()
    iface.launch(server_name="0.0.0.0", server_port=args.port)
