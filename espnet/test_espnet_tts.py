import torch
from espnet2.bin.tts_inference import Text2Speech
import soundfile as sf

# 使用预训练的中文模型
text2speech = Text2Speech.from_pretrained(
    "kan-bayashi/csmsc_tts",  # 中文 TTS 模型标签
    device="cuda" if torch.cuda.is_available() else "cpu"
)

# 测试文本
text = "欢迎使用ESPnet语音合成系统。这是一个测试。"
print(f"正在合成文本：{text}")

# 生成语音
wav = text2speech(text)["wav"].view(-1).cpu().numpy()

# 保存音频
output_path = "output.wav"
sf.write(output_path, wav, 24000)
print(f"合成完成，已保存为：{output_path}")