import torchaudio
import os
import torch
from third_party.demucs.models.pretrained import get_model_from_yaml


class Separator(torch.nn.Module):
    def __init__(self, dm_model_path='third_party/demucs/ckpt/htdemucs.pth', dm_config_path='third_party/demucs/ckpt/htdemucs.yaml', gpu_id=0) -> None:
        super().__init__()
        if torch.cuda.is_available() and gpu_id < torch.cuda.device_count():
            self.device = torch.device(f"cuda:{gpu_id}")
        else:
            self.device = torch.device("cpu")
        self.demucs_model = self.init_demucs_model(dm_model_path, dm_config_path)

    def init_demucs_model(self, model_path, config_path):
        try:
            model = get_model_from_yaml(config_path, model_path)
            model.to(self.device)
            model.eval()
            print(f"✅ Demucs模型初始化成功，使用设备: {self.device}")
            return model
        except Exception as e:
            print(f"⚠️  Demucs模型初始化失败: {e}")
            print("⚠️  使用简化模式")
            return None
    
    def load_audio(self, f):
        a, fs = torchaudio.load(f)
        if (fs != 48000):
            a = torchaudio.functional.resample(a, fs, 48000)
        if a.shape[-1] >= 48000*10:
            a = a[..., :48000*10]
        else:
            a = torch.cat([a, a], -1)
        return a[:, 0:48000*10]
    
    def run(self, audio_path, output_dir='tmp', ext=".flac"):
        os.makedirs(output_dir, exist_ok=True)
        name, _ = os.path.splitext(os.path.split(audio_path)[-1])
        
        if self.demucs_model is None:
            # 简化模式：直接返回原始音频
            full_audio = self.load_audio(audio_path)
            vocal_audio = full_audio  # 暂时使用原始音频
            bgm_audio = torch.zeros_like(full_audio)  # 暂时使用静音
            print(f"⚠️  使用简化音频分离模式：{audio_path}")
            return full_audio, vocal_audio, bgm_audio
        
        # 完整模式：使用demucs进行音频分离
        try:
            output_paths = []
            for stem in self.demucs_model.sources:
                output_path = os.path.join(output_dir, f"{name}_{stem}{ext}")
                if os.path.exists(output_path):
                    output_paths.append(output_path)
            
            if len(output_paths) == 1:  # 4
                vocal_path = output_paths[0]
            else:
                drums_path, bass_path, other_path, vocal_path = self.demucs_model.separate(audio_path, output_dir, device=self.device)
                for path in [drums_path, bass_path, other_path]:
                    if os.path.exists(path):
                        os.remove(path)
            
            full_audio = self.load_audio(audio_path)
            vocal_audio = self.load_audio(vocal_path)
            bgm_audio = full_audio - vocal_audio
            print(f"✅ 音频分离完成：{audio_path}")
            return full_audio, vocal_audio, bgm_audio
            
        except Exception as e:
            print(f"⚠️  音频分离失败: {e}")
            # 回退到简化模式
            full_audio = self.load_audio(audio_path)
            vocal_audio = full_audio
            bgm_audio = torch.zeros_like(full_audio)
            return full_audio, vocal_audio, bgm_audio
