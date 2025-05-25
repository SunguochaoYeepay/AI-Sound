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
        from tts.modules.llm_dit.config import config
        self.dit = Diffusion(in_channels=32, out_channels=32)  # 使用默认的通道数
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

    def preprocess(self, audio_bytes, latent_file=None):
        """
        预处理音频数据，提取特征
        """
        # 如果提供了特征文件，直接加载
        if latent_file and os.path.exists(latent_file):
            lat_ctx = np.load(latent_file)
            lat_ctx = torch.from_numpy(lat_ctx).float()
            print(f"参考VAE特征统计: mean={lat_ctx.mean():.4f}, std={lat_ctx.std():.4f}")
            return lat_ctx
        
        # 否则从音频中提取特征
        if not self.has_vae_encoder:
            raise ValueError("当前模型不包含编码器，无法从音频中提取特征。请提供预计算的特征文件。")
            
        # 将音频字节转换为numpy数组
        wav = convert_to_wav_bytes(audio_bytes)
        wav = wav.astype(np.float32) / 32768.0
        wav = torch.from_numpy(wav).float()
        
        # 提取特征
        with torch.no_grad():
            lat_ctx = self.wavvae.extract_latent(wav[None, :].to(self.device))
            lat_ctx = lat_ctx.cpu()
            
        print(f"提取的VAE特征统计: mean={lat_ctx.mean():.4f}, std={lat_ctx.std():.4f}")
        return lat_ctx

    def forward(self, resource_context, input_text, time_step=16, p_w=1.2, t_w=1.8, dur_disturb=0.1, dur_alpha=1.0, disable_normalization=False, **kwargs):
        """
        生成语音
        Args:
            resource_context: VAE特征
            input_text: 输入文本
            time_step: 扩散步数
            p_w: 音高权重
            t_w: 音色权重
            dur_disturb: 持续时间扰动
            dur_alpha: 语速控制
            disable_normalization: 是否禁用音量标准化
        """
        try:
            # 文本规范化
            print(f"规范化前文本: {input_text}")
            try:
                lang = classify_language(input_text)
            except:
                lang = 'zh'
                
            if lang == 'zh':
                input_text = self.zh_normalizer.normalize(input_text)
            else:
                input_text = self.en_normalizer.normalize(input_text)
            print(f"规范化后文本: {input_text}")
            
            # 准备输入
            inputs = prepare_inputs_for_dit(
                input_text, 
                self.g2p_model, 
                self.g2p_tokenizer, 
                self.speech_start_idx,
                self.aligner_lm,
                self.dur_model,
                self.ling_dict,
                self.device,
                dur_disturb=dur_disturb,
                dur_alpha=dur_alpha
            )
            
            # 添加上下文特征
            inputs['lat_ctx'] = resource_context.to(self.device)
            
            # DiT推理
            with torch.no_grad():
                # 设置CFG权重
                seq_cfg_w = [p_w, t_w]  # [phone_weight, tone_weight]
                print(f"使用CFG权重: phone_w={p_w}, tone_w={t_w}")
                
                # 执行DiT推理
                lat_pred = self.dit.inference(inputs, timesteps=time_step, seq_cfg_w=seq_cfg_w)
                print(f"DiT原始输出统计: mean={lat_pred.mean():.4f}, std={lat_pred.std():.4f}")
                
                # 应用CFG增强
                lat_pred = lat_pred * inputs['lat_ctx'].std() + inputs['lat_ctx'].mean()
                print(f"DiT增强后统计: mean={lat_pred.mean():.4f}, std={lat_pred.std():.4f}")
                
                # WavVAE解码
                print("\n开始WavVAE解码...")
                with torch.cuda.amp.autocast(enabled=False):  # 使用完整精度
                    wav_out = self.wavvae.decode(lat_pred)
                wav_out = wav_out.squeeze().cpu().float().numpy()
                print(f"WavVAE输出统计: mean={wav_out.mean():.4f}, std={wav_out.std():.4f}")
                
                # 音量标准化
                if not disable_normalization:
                    wav_out = pyln.normalize.peak(wav_out, -1.0)
                
                # 转换为音频字节
                wav_bytes = to_wav_bytes(wav_out, sr=self.sr)
                return wav_bytes
                
        except Exception as e:
            print(f"生成过程出错: {e}")
            return None

    def infer(self, input_text_or_resource, params=None):
        """
        推理接口
        Args:
            input_text_or_resource: 输入文本或资源上下文
            params: 参数字典
        """
        if params is None:
            params = {}
            
        # 如果输入是字符串，则作为文本处理
        if isinstance(input_text_or_resource, str):
            input_text = input_text_or_resource
            if not hasattr(self, 'resource_context'):
                raise ValueError("未设置资源上下文，请先调用preprocess方法")
            resource_context = self.resource_context
        else:
            # 否则作为资源上下文处理
            resource_context = input_text_or_resource
            input_text = params.get('text', '')
            
        # 生成语音
        return self.forward(resource_context, input_text, **params)