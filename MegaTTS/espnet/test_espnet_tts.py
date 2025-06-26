import torch
from espnet2.bin.tts_inference import Text2Speech
import soundfile as sf

# 用本地模型
text2speech = Text2Speech(
    train_config="exp/tts_train_raw_phn_pypinyin_g2p_phone/config.yaml",
    model_file="exp/tts_train_raw_phn_pypinyin_g2p_phone/valid.acc.ave.pth",
    device="cuda" if torch.cuda.is_available() else "cpu"
)

text = "在人工智能的快速发展过程中，语音合成技术作为人机交互的重要桥梁，正变得越来越成熟和实用。无论是在智能客服、导航播报，还是在有声读物、辅助教育等领域，语音合成都展现出了巨大的应用价值。通过深度学习模型的不断优化，现代语音合成系统不仅能够实现高自然度的发音，还能根据不同场景和需求调整语速、语调和情感色彩。未来，随着多模态融合和个性化定制的推进，语音合成将为我们的生活和工作带来更多便利与创新。" * 3  # 约300字
print(f"正在合成文本：{text[:50]}...（共{len(text)}字）")

result = text2speech(text)
wav = result["wav"].view(-1).cpu().numpy()
print(f"合成音频长度: {len(wav)} 采样率: 24000")

output_path = "output_300chars.wav"
sf.write(output_path, wav, 24000)
print(f"合成完成，已保存为：{output_path}")
