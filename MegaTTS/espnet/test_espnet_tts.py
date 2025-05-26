import torch
from espnet2.bin.tts_inference import Text2Speech
import soundfile as sf

# 用本地模型
text2speech = Text2Speech(
    train_config="exp/tts_train_raw_phn_pypinyin_g2p_phone/config.yaml",
    model_file="exp/tts_train_raw_phn_pypinyin_g2p_phone/valid.acc.ave.pth",
    device="cuda" if torch.cuda.is_available() else "cpu"
)

text = "欢迎使用ESPnet语音合成系统。这是一个测试。"
print(f"正在合成文本：{text}")

wav = text2speech(text)["wav"].view(-1).cpu().numpy()

output_path = "output.wav"
sf.write(output_path, wav, 24000)
print(f"合成完成，已保存为：{output_path}")
