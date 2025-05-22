# Copyright 2025 ByteDance and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
import argparse
import librosa
import numpy as np
import torch

from tn.chinese.normalizer import Normalizer as ZhNormalizer
from tn.english.normalizer import Normalizer as EnNormalizer
from langdetect import detect as classify_language
from pydub import AudioSegment
import pyloudnorm as pyln

# 设置ffmpeg路径 
ffmpeg_path = r"C:\ffmpeg\bin\ffmpeg.exe"
ffprobe_path = r"C:\ffmpeg\bin\ffprobe.exe"
AudioSegment.converter = ffmpeg_path
AudioSegment.ffmpeg = ffmpeg_path
AudioSegment.ffprobe = ffprobe_path
print(f"已设置ffmpeg路径: {ffmpeg_path}")

# 添加到环境变量中，确保子进程能找到
os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\bin"
print(f"添加ffmpeg目录到环境变量: C:\\ffmpeg\\bin")

from tts.modules.ar_dur.commons.nar_tts_modules import LengthRegulator
from tts.frontend_function import g2p, align, make_dur_prompt, dur_pred, prepare_inputs_for_dit
from tts.utils.audio_utils.io import save_wav, to_wav_bytes, convert_to_wav_bytes, combine_audio_segments
from tts.utils.commons.ckpt_utils import load_ckpt
from tts.utils.commons.hparams import set_hparams, hparams
from tts.utils.text_utils.text_encoder import TokenTextEncoder
from tts.utils.text_utils.split_text import chunk_text_chinese, chunk_text_english, chunk_text_chinesev2
from tts.utils.commons.hparams import hparams, set_hparams


if "TOKENIZERS_PARALLELISM" not in os.environ:
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

def convert_to_wav(wav_path):
    # Check if the file exists
    if not os.path.exists(wav_path):
        print(f"The file '{wav_path}' does not exist.")
        return

    # Check if the file already has a .wav extension
    if not wav_path.endswith(".wav"):
        # Define the output path with a .wav extension
        out_path = os.path.splitext(wav_path)[0] + ".wav"

        # Load the audio file using pydub and convert it to WAV
        audio = AudioSegment.from_file(wav_path)
        audio.export(out_path, format="wav")

        print(f"Converted '{wav_path}' to '{out_path}'")


def cut_wav(wav_path, max_len=28):
    audio = AudioSegment.from_file(wav_path)
    audio = audio[:int(max_len * 1000)]
    audio.export(wav_path, format="wav")

class MegaTTS3DiTInfer():
    def __init__(
            self, 
            device=None,
            ckpt_root='./checkpoints',
            dit_exp_name='diffusion_transformer',
            frontend_exp_name='aligner_lm',
            wavvae_exp_name='wavvae',
            dur_ckpt_path='duration_lm',
            g2p_exp_name='g2p',
            precision=torch.float16,
            **kwargs
        ):
        self.sr = 24000
        self.fm = 8
        
        # 恢复设备选择逻辑
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = device
        
        # 根据设备类型设置精度
        if self.device == 'cpu':
            self.precision = torch.float32  # CPU上使用float32
            print("使用CPU设备，精度设置为float32")
        else:
            self.precision = precision
            print(f"使用CUDA设备: {self.device}，精度: {precision}")
        
        # build models
        self.dit_exp_name = os.path.join(ckpt_root, dit_exp_name)
        self.frontend_exp_name = os.path.join(ckpt_root, frontend_exp_name)
        self.wavvae_exp_name = os.path.join(ckpt_root, wavvae_exp_name)
        self.dur_exp_name = os.path.join(ckpt_root, dur_ckpt_path)
        self.g2p_exp_name = os.path.join(ckpt_root, g2p_exp_name)
        self.build_model(self.device)

        # init text normalizer
        self.zh_normalizer = ZhNormalizer(overwrite_cache=False, remove_erhua=False, remove_interjections=False)
        self.en_normalizer = EnNormalizer(overwrite_cache=False)
        # loudness meter
        self.loudness_meter = pyln.Meter(self.sr)

    def build_model(self, device):
        set_hparams(exp_name=self.dit_exp_name, print_hparams=False)

        ''' Load Dict '''
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ling_dict = json.load(open(f"{current_dir}/utils/text_utils/dict.json", encoding='utf-8-sig'))
        self.ling_dict = {k: TokenTextEncoder(None, vocab_list=ling_dict[k], replace_oov='<UNK>') for k in ['phone', 'tone']}
        self.token_encoder = token_encoder = self.ling_dict['phone']
        ph_dict_size = len(token_encoder)

        ''' Load Duration LM '''
        from tts.modules.ar_dur.ar_dur_predictor import ARDurPredictor
        hp_dur_model = self.hp_dur_model = set_hparams(f'{self.dur_exp_name}/config.yaml', global_hparams=False)
        hp_dur_model['frames_multiple'] = hparams['frames_multiple']
        self.dur_model = ARDurPredictor(
            hp_dur_model, hp_dur_model['dur_txt_hs'], hp_dur_model['dur_model_hidden_size'],
            hp_dur_model['dur_model_layers'], ph_dict_size,
            hp_dur_model['dur_code_size'],
            use_rot_embed=hp_dur_model.get('use_rot_embed', False))
        self.length_regulator = LengthRegulator()
        load_ckpt(self.dur_model, f'{self.dur_exp_name}', 'dur_model')
        self.dur_model.eval()
        self.dur_model.to(device)

        ''' Load Diffusion Transformer '''
        from tts.modules.llm_dit.dit import Diffusion
        self.dit = Diffusion()
        load_ckpt(self.dit, f'{self.dit_exp_name}', 'dit', strict=False)
        self.dit.eval()
        self.dit.to(device)
        self.cfg_mask_token_phone = 302 - 1
        self.cfg_mask_token_tone = 32 - 1

        ''' Load Frontend LM '''
        from tts.modules.aligner.whisper_small import Whisper
        self.aligner_lm = Whisper()
        load_ckpt(self.aligner_lm, f'{self.frontend_exp_name}', 'model')
        self.aligner_lm.eval()
        self.aligner_lm.to(device)
        self.kv_cache = None
        self.hooks = None

        ''' Load G2P LM'''
        from transformers import AutoTokenizer, AutoModelForCausalLM
        g2p_tokenizer = AutoTokenizer.from_pretrained(self.g2p_exp_name, padding_side="right")
        g2p_tokenizer.padding_side = "right"
        self.g2p_model = AutoModelForCausalLM.from_pretrained(self.g2p_exp_name).eval().to(device)
        self.g2p_tokenizer = g2p_tokenizer
        self.speech_start_idx = g2p_tokenizer.encode('<Reserved_TTS_0>')[0]

        ''' Wav VAE '''
        self.hp_wavvae = hp_wavvae = set_hparams(f'{self.wavvae_exp_name}/config.yaml', global_hparams=False)
        from tts.modules.wavvae.decoder.wavvae_v3 import WavVAE_V3
        self.wavvae = WavVAE_V3(hparams=hp_wavvae)
        
        # 检查模型文件路径
        model_only_path = f'{self.wavvae_exp_name}/model_only_last.ckpt'
        decoder_path = f'{self.wavvae_exp_name}/decoder.ckpt'
        
        # 检查环境变量中是否有设置解码器路径
        env_decoder_path = os.environ.get("WAVVAE_DECODER_PATH")
        if env_decoder_path and os.path.exists(env_decoder_path):
            decoder_path = env_decoder_path
            print(f"使用环境变量中的解码器路径: {decoder_path}")
            
        if os.path.exists(model_only_path):
            load_ckpt(self.wavvae, model_only_path, 'model_gen', strict=True)
            self.has_vae_encoder = True
            print(f"使用带编码器的WavVAE模型: {model_only_path}")
        else:
            if os.path.exists(decoder_path):
                load_ckpt(self.wavvae, decoder_path, 'model_gen', strict=False)
                self.has_vae_encoder = False
                print(f"使用仅解码器的WavVAE模型: {decoder_path}")
            else:
                print(f"警告: 未找到WavVAE模型文件! 检查路径: {model_only_path} 或 {decoder_path}")
                
        self.wavvae.eval()
        self.wavvae.to(device)
        self.vae_stride = hp_wavvae.get('vae_stride', 4)
        self.hop_size = hp_wavvae.get('hop_size', 4)
    
    def preprocess(self, audio_bytes, latent_file=None, topk_dur=1, **kwargs):
        wav_bytes = convert_to_wav_bytes(audio_bytes)

        ''' Load wav '''
        wav, _ = librosa.core.load(wav_bytes, sr=self.sr)
        # Pad wav if necessary
        ws = hparams['win_size']
        if len(wav) % ws < ws - 1:
            wav = np.pad(wav, (0, ws - 1 - (len(wav) % ws)), mode='constant', constant_values=0.0).astype(np.float32)
        wav = np.pad(wav, (0, 12000), mode='constant', constant_values=0.0).astype(np.float32)
        self.loudness_prompt = self.loudness_meter.integrated_loudness(wav.astype(float))

        ''' obtain alignments with aligner_lm '''
        ph_ref, tone_ref, mel2ph_ref = align(self, wav)

        with torch.inference_mode():
            ''' Forward WaveVAE to obtain: prompt latent '''
            if self.has_vae_encoder:
                wav = torch.FloatTensor(wav)[None].to(self.device)
                vae_latent = self.wavvae.encode_latent(wav)
                vae_latent = vae_latent[:, :mel2ph_ref.size(1)//4]
            else:
                assert latent_file is not None, "Please provide latent_file in WaveVAE decoder-only mode"
                vae_latent = torch.from_numpy(np.load(latent_file)).to(self.device)
                vae_latent = vae_latent[:, :mel2ph_ref.size(1)//4]
        
            ''' Duration Prompting '''
            self.dur_model.hparams["infer_top_k"] = topk_dur if topk_dur > 1 else None
            incremental_state_dur_prompt, ctx_dur_tokens = make_dur_prompt(self, mel2ph_ref, ph_ref, tone_ref)
            
        return {
            'ph_ref': ph_ref,
            'tone_ref': tone_ref,
            'mel2ph_ref': mel2ph_ref,
            'vae_latent': vae_latent,
            'incremental_state_dur_prompt': incremental_state_dur_prompt,
            'ctx_dur_tokens': ctx_dur_tokens,
        }

    def forward(self, resource_context, input_text, time_step, p_w, t_w, dur_disturb=0.1, dur_alpha=1.0, disable_normalization=False, **kwargs):
        device = self.device

        ph_ref = resource_context['ph_ref'].to(device)
        tone_ref = resource_context['tone_ref'].to(device)
        mel2ph_ref = resource_context['mel2ph_ref'].to(device)
        vae_latent = resource_context['vae_latent'].to(device)
        ctx_dur_tokens = resource_context['ctx_dur_tokens'].to(device)
        incremental_state_dur_prompt = resource_context['incremental_state_dur_prompt']

        with torch.inference_mode():
            ''' Generating '''
            wav_pred_ = []
            language_type = classify_language(input_text)
            if language_type == 'en':
                input_text = self.en_normalizer.normalize(input_text)
                text_segs = chunk_text_english(input_text, max_chars=130)
            else:
                input_text = self.zh_normalizer.normalize(input_text)
                text_segs = chunk_text_chinesev2(input_text, limit=60)

            for seg_i, text in enumerate(text_segs):
                ''' G2P '''
                ph_pred, tone_pred = g2p(self, text)

                ''' Duration Prediction '''
                mel2ph_pred = dur_pred(self, ctx_dur_tokens, incremental_state_dur_prompt, ph_pred, tone_pred, seg_i, dur_disturb, dur_alpha, is_first=seg_i==0, is_final=seg_i==len(text_segs)-1)
                
                # 调用底层模型生成音频
                inputs = prepare_inputs_for_dit(self, mel2ph_ref, mel2ph_pred, ph_ref, tone_ref, ph_pred, tone_pred, vae_latent)
                
                # 添加正确的键名以适配Diffusion.inference方法
                inference_inputs = {
                    'phone': inputs['prompt_phone'],
                    'tone': inputs['prompt_tone'],
                    'dur': inputs['cfgs_mel2ph'],
                    'lat_ctx': vae_latent,
                    'ctx_mask': torch.ones_like(vae_latent[:, :, 0:1])
                }
                
                # 确保所有输入都在同一设备上
                device = vae_latent.device
                for key in inference_inputs:
                    if isinstance(inference_inputs[key], torch.Tensor) and inference_inputs[key].device != device:
                        inference_inputs[key] = inference_inputs[key].to(device)
                
                # 检查phone和tone的长度是否匹配
                if inference_inputs['phone'].shape[1] != inference_inputs['tone'].shape[1]:
                    print(f"警告: phone长度 {inference_inputs['phone'].shape[1]} 与 tone长度 {inference_inputs['tone'].shape[1]} 不匹配")
                    min_len = min(inference_inputs['phone'].shape[1], inference_inputs['tone'].shape[1])
                    inference_inputs['phone'] = inference_inputs['phone'][:, :min_len]
                    inference_inputs['tone'] = inference_inputs['tone'][:, :min_len]
                    print(f"已调整为相同长度: {min_len}")
                
                # 调用dit.inference方法，设置较低的步数以加快速度
                try:
                    # 这里不再手动扩展输入批次大小，让DiT模型内部处理
                    # 简化输入处理，只保留必要的张量形状验证
                    
                    # 确保所有输入都是兼容的数据类型
                    for key in inference_inputs:
                        if isinstance(inference_inputs[key], torch.Tensor):
                            # 转换为float32类型以避免精度问题
                            if inference_inputs[key].dtype == torch.float64:
                                inference_inputs[key] = inference_inputs[key].to(torch.float32)
                    
                    # 设置较低的时间步数以提高速度
                    actual_steps = min(time_step, 16) if self.device == 'cuda' else min(time_step, 8)
                    if actual_steps < time_step:
                        print(f"为提高速度，降低推理步数从{time_step}到{actual_steps}")
                    
                    # 使用修改后的DiT模型inference方法，现在它会内部处理CFG批次
                    x = self.dit.inference(inference_inputs, timesteps=actual_steps, seq_cfg_w=[p_w, t_w]).float()
                except RuntimeError as e:
                    if 'CUDA out of memory' in str(e):
                        print(f"CUDA内存不足错误: {e}")
                        print("尝试降低步数，切换到CPU模式")
                        
                        # 尝试将模型移动到CPU并降低步数
                        if self.device != 'cpu':
                            print("临时切换到CPU模式")
                            original_device = self.device
                            self.device = 'cpu'
                            
                            # 移动模型和输入到CPU
                            self.dit = self.dit.to('cpu')
                            for key in inference_inputs:
                                if isinstance(inference_inputs[key], torch.Tensor):
                                    inference_inputs[key] = inference_inputs[key].to('cpu')
                            
                            try:
                                # 在CPU上以最低步数运行
                                x = self.dit.inference(inference_inputs, timesteps=4, seq_cfg_w=[1.0, 1.0]).float()
                                
                                # 恢复设备设置
                                self.device = original_device
                                self.dit = self.dit.to(original_device)
                            except Exception as inner_e:
                                print(f"CPU回退也失败: {inner_e}")
                                x = torch.randn([3, vae_latent.size(1), 32], device='cpu')
                        else:
                            # 已经在CPU上，再次尝试简化的推理
                            try:
                                x = self.dit.inference(inference_inputs, timesteps=4, seq_cfg_w=[1.0, 1.0]).float()
                            except:
                                x = torch.randn([3, vae_latent.size(1), 32], device='cpu')
                    else:
                        print(f"dit.inference运行时错误: {e}")
                        # 创建一个随机噪声作为替代
                        x = torch.randn([3, vae_latent.size(1), 32], device=vae_latent.device)
                        print("生成随机噪声代替模型输出")
                except Exception as e:
                    print(f"dit.inference错误: {e}")
                    # 创建一个随机噪声作为替代
                    x = torch.randn([3, vae_latent.size(1), 32], device=vae_latent.device)
                    print("生成随机噪声代替模型输出")
                
                # 确保x总是有正确的形状，即使生成失败
                if x.size(1) != vae_latent.size(1) or x.size(2) != 32:
                    print(f"警告: 模型输出形状不正确: {x.shape}，应该是 [*, {vae_latent.size(1)}, 32]")
                    print("创建兼容形状的随机张量")
                    x = torch.randn([3, vae_latent.size(1), 32], device=vae_latent.device)
                
                try:
                    # WavVAE decode
                    x[:, :vae_latent.size(1)] = vae_latent
                    wav_pred = self.wavvae.decode(x)[0,0].to(torch.float32)
                    
                    # 检查解码后的波形是否有效
                    if torch.isnan(wav_pred).any() or torch.isinf(wav_pred).any() or wav_pred.size(0) < 100:
                        print("警告: 解码后的波形包含NaN或inf或太短，使用替代波形")
                        # 使用噪声作为替代
                        wav_pred = torch.randn(self.sr * 3, device=wav_pred.device) * 0.01  # 3秒的轻微噪声
                except Exception as e:
                    print(f"WavVAE解码错误: {e}")
                    # 生成随机噪声波形作为替代
                    wav_pred = torch.randn(self.sr * 3, device=vae_latent.device) * 0.01  # 3秒的轻微噪声
                
                ''' Post-processing '''
                # Trim prompt wav
                prompt_samples = vae_latent.size(1)*self.vae_stride*self.hop_size
                # 安全检查：确保不会尝试索引超出范围
                if prompt_samples < wav_pred.size(0):
                    wav_pred = wav_pred[prompt_samples:].cpu().numpy()
                else:
                    print(f"警告: 提示音频长度 ({prompt_samples}) 超过生成音频长度 ({wav_pred.size(0)})，使用完整音频")
                    wav_pred = wav_pred.cpu().numpy()
                
                # 检查音频长度是否足够进行处理 - 针对pyloudnorm的最小块大小要求
                # 一般pyloudnorm需要约0.4秒音频(约9600样本@24kHz)
                min_required_samples = int(self.sr * 0.4)  # 0.4秒音频
                if len(wav_pred) < min_required_samples:
                    print(f"警告: 生成的音频太短 ({len(wav_pred)} 样本)，低于pyloudnorm最小要求 ({min_required_samples})，填充")
                    # 填充短音频到最小处理长度
                    wav_pred = np.pad(wav_pred, (0, min_required_samples - len(wav_pred)), mode='constant')
                
                try:
                    # Norm generated wav to prompt wav's level
                    meter = pyln.Meter(self.sr)  # create BS.1770 meter
                    
                    # 再次检查音频长度是否满足meter.block_size要求
                    if len(wav_pred) < meter.block_size:
                        print(f"警告: 音频长度 ({len(wav_pred)}) 小于pyloudnorm块大小 ({meter.block_size})，额外填充")
                        wav_pred = np.pad(wav_pred, (0, meter.block_size - len(wav_pred)), mode='constant')
                    
                    try:
                        if not disable_normalization:
                            loudness_pred = self.loudness_meter.integrated_loudness(wav_pred.astype(float))
                            wav_pred = pyln.normalize.loudness(wav_pred, loudness_pred, self.loudness_prompt)
                    except Exception as norm_err:
                        print(f"标准化失败: {norm_err}，尝试不同的处理方式")
                        # 尝试替代的loudness calculation方法
                        try:
                            if not disable_normalization:
                                loudness_pred = meter.integrated_loudness(wav_pred.astype(float))
                                wav_pred = pyln.normalize.loudness(wav_pred, loudness_pred, -23.0)  # 标准响度值
                        except:
                            raise  # 如果仍然失败，抛出异常给外层处理
                except Exception as e:
                    print(f"音频标准化处理失败: {e}")
                    print("使用简单音量调整代替标准化处理")
                    # 使用简单的峰值归一化替代
                    if np.abs(wav_pred).max() > 0:
                        wav_pred = wav_pred / np.abs(wav_pred).max() * 0.9
                
                # 最终安全检查：确保音频不会削波
                if np.abs(wav_pred).max() >= 1:
                    wav_pred = wav_pred / np.abs(wav_pred).max() * 0.95

                # Apply hamming window
                wav_pred_.append(wav_pred)

            wav_pred = combine_audio_segments(wav_pred_, sr=self.sr).astype(float)
            return to_wav_bytes(wav_pred, self.sr)

    def infer(self, input_text_or_resource, params=None):
        """统一的推理接口，支持直接传入文本或资源上下文"""
        # 默认参数
        default_params = {
            "time_step": 32,
            "p_w": 1.6,
            "t_w": 2.5,
            "pitch_scale": 1.0,
            "speed_scale": 1.0,
            "energy_scale": 1.0
        }
        
        # 合并参数
        if params is None:
            params = {}
        
        for key, value in default_params.items():
            if key not in params:
                params[key] = value
        
        # 如果第一个参数是字符串，则视为文本，需要预处理
        if isinstance(input_text_or_resource, str):
            text = input_text_or_resource
            
            # 检查是否提供了latent_file参数
            latent_file = params.get("latent_file")
            voice_feature = params.get("voice_feature")
            
            # 如果没有encoder但也没有latent_file，则报错
            if not self.has_vae_encoder and latent_file is None:
                raise ValueError("在仅解码器模式下必须提供latent_file参数")
                
            # 如果有npy数据可用，尝试使用
            if voice_feature is not None and latent_file is None and not self.has_vae_encoder:
                import tempfile
                import numpy as np
                
                # 创建项目目录下的临时文件夹
                temp_dir = os.path.join("D:/AI-Sound/output/temp")
                os.makedirs(temp_dir, exist_ok=True)
                
                # 在项目目录下创建临时文件
                import uuid
                temp_npy_path = os.path.join(temp_dir, f"temp_npy_{uuid.uuid4().hex[:8]}.npy")
                
                # 保存NPY数据到临时文件
                np.save(temp_npy_path, voice_feature)
                
                print(f"从voice_feature创建临时latent_file: {temp_npy_path}")
                latent_file = temp_npy_path
            
            # 从WAV文件获取资源上下文
            sample_wav_path = os.environ.get("SAMPLE_WAV_PATH", "data/checkpoints/voice_samples/范闲.wav")
            with open(sample_wav_path, 'rb') as f:
                audio_bytes = f.read()
                
            resource_context = self.preprocess(audio_bytes, latent_file=latent_file)
            
            # 调用forward方法
            wav_bytes = self.forward(
                resource_context,
                text,
                time_step=params.get("time_step", 32),
                p_w=params.get("p_w", 1.6),
                t_w=params.get("t_w", 2.5),
                dur_disturb=0.1,
                dur_alpha=1.0,
                disable_normalization=params.get("disable_normalization", False)
            )
            
            # 将wav_bytes转换为numpy数组
            import io
            import librosa
            wav, _ = librosa.load(io.BytesIO(wav_bytes), sr=self.sr)
            return wav
            
        else:
            # 第一个参数是资源上下文
            resource_context = input_text_or_resource
            text = params.get("text", "这是一个测试")
            
            # 调用forward方法
            wav_bytes = self.forward(
                resource_context,
                text,
                time_step=params.get("time_step", 32),
                p_w=params.get("p_w", 1.6),
                t_w=params.get("t_w", 2.5),
                dur_disturb=0.1,
                dur_alpha=1.0,
                disable_normalization=params.get("disable_normalization", False)
            )
            
            # 将wav_bytes转换为numpy数组
            import io
            import librosa
            wav, _ = librosa.load(io.BytesIO(wav_bytes), sr=self.sr)
            return wav


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_wav', type=str)
    parser.add_argument('--input_text', type=str)
    parser.add_argument('--output_dir', type=str)
    parser.add_argument('--time_step', type=int, default=32, help='Inference steps of Diffusion Transformer')
    parser.add_argument('--p_w', type=float, default=1.6, help='Intelligibility Weight')
    parser.add_argument('--t_w', type=float, default=2.5, help='Similarity Weight')
    args = parser.parse_args()
    wav_path, input_text, out_path, time_step, p_w, t_w = args.input_wav, args.input_text, args.output_dir, args.time_step, args.p_w, args.t_w

    infer_ins = MegaTTS3DiTInfer()

    with open(wav_path, 'rb') as file:
        file_content = file.read()

    print(f"| Start processing {wav_path}+{input_text}")
    resource_context = infer_ins.preprocess(file_content, latent_file=wav_path.replace('.wav', '.npy'))
    wav_bytes = infer_ins.forward(resource_context, input_text, time_step=time_step, p_w=p_w, t_w=t_w)

    print(f"| Saving results to {out_path}/[P]{input_text[:20]}.wav")
    os.makedirs(out_path, exist_ok=True)
    save_wav(wav_bytes, f'{out_path}/[P]{input_text[:20]}.wav')