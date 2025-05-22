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

import io
import os
import subprocess

import numpy as np
from scipy.io import wavfile
import pyloudnorm as pyln
from pydub import AudioSegment


def to_wav_bytes(wav, sr, norm=False):
    """将音频数组转换为wav字节流，支持音量标准化
    
    Args:
        wav: 音频数据
        sr: 采样率
        norm: 是否进行音量标准化
        
    Returns:
        bytes: wav格式的字节数据
    """
    wav = wav.astype(float)
    
    # pyloudnorm需要的最小块大小，一般为0.4秒音频（对于大多数采样率）
    min_block_size = int(0.4 * sr)
    
    # 确保音频至少有最小处理长度（pyloudnorm要求）
    if len(wav) < min_block_size:
        print(f"警告: 音频太短 ({len(wav)} 样本)，低于pyloudnorm最小块长度 {min_block_size}，填充到安全长度")
        # 填充到安全长度
        wav = np.pad(wav, (0, max(min_block_size - len(wav), 0)), mode='constant')
    
    if norm:
        try:
            meter = pyln.Meter(sr)  # create BS.1770 meter
            # 进一步检查音频长度是否大于block_size
            block_size = meter.block_size
            if len(wav) < block_size:
                print(f"填充后仍然太短，扩展到块大小: {block_size}")
                wav = np.pad(wav, (0, max(block_size - len(wav), 0)), mode='constant')
                
            loudness = meter.integrated_loudness(wav)
            wav = pyln.normalize.loudness(wav, loudness, -18.0)
        except Exception as e:
            print(f"音量标准化失败: {e}")
            # 使用简单的峰值归一化
            if np.abs(wav).max() > 0:
                wav = wav / np.abs(wav).max() * 0.95
    
    # 确保不会削波
    if np.abs(wav).max() >= 1:
        wav = wav / np.abs(wav).max() * 0.95
        
    # 转换为16位整数格式
    wav = wav * 32767
    bytes_io = io.BytesIO()
    wavfile.write(bytes_io, sr, wav.astype(np.int16))
    return bytes_io.getvalue()


def save_wav(wav_bytes, path):
    with open(path[:-4] + '.wav', 'wb') as file:
        file.write(wav_bytes)
    if path[-4:] == '.mp3':
        to_mp3(path[:-4])


def to_mp3(out_path):
    if out_path[-4:] == '.wav':
        out_path = out_path[:-4]
    subprocess.check_call(
        f'ffmpeg -threads 1 -loglevel error -i "{out_path}.wav" -vn -b:a 192k -y -hide_banner -async 1 "{out_path}.mp3"',
        shell=True, stdin=subprocess.PIPE)
    subprocess.check_call(f'rm -f "{out_path}.wav"', shell=True)


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


def convert_to_wav_bytes(audio_binary):
    # Load the audio binary using pydub and convert it to WAV
    audio = AudioSegment.from_file(io.BytesIO(audio_binary))
    wav_bytes = io.BytesIO()
    audio.export(wav_bytes, format="wav")
    wav_bytes.seek(0)
    return wav_bytes


''' Smoothly combine audio segments using crossfade transitions." '''
def combine_audio_segments(segments, crossfade_duration=0.16, sr=24000):
    # 检查输入是否有效
    if not segments or len(segments) == 0:
        print("警告: 没有音频片段可以合并，返回空音频")
        # 返回足够长的静音，保证能通过所有处理
        return np.zeros(int(sr * 1.0))  # 返回1秒的静音
    
    # 过滤掉空的或过短的片段
    min_seg_length = int(sr * 0.1)  # 每个片段至少0.1秒
    valid_segments = []
    
    for seg in segments:
        if seg is not None and len(seg) > 0:
            # 如果段落太短，填充到最小长度
            if len(seg) < min_seg_length:
                print(f"警告: 音频片段太短 ({len(seg)} 样本)，填充到 {min_seg_length} 样本")
                seg = np.pad(seg, (0, min_seg_length - len(seg)), mode='constant')
            valid_segments.append(seg)
    
    if not valid_segments:
        print("警告: 所有音频片段都无效，返回空音频")
        # 返回足够长的静音
        return np.zeros(int(sr * 1.0))  # 返回1秒的静音
    
    # 如果只有一个片段，确保它有足够的长度
    if len(valid_segments) == 1:
        seg = valid_segments[0]
        min_audio_length = int(sr * 0.5)  # 最小0.5秒
        if len(seg) < min_audio_length:
            print(f"警告: 单一音频片段太短 ({len(seg)} 样本)，填充到 {min_audio_length} 样本")
            seg = np.pad(seg, (0, min_audio_length - len(seg)), mode='constant')
        return seg
    
    # 检查音频片段长度，确保可以应用交叉淡入淡出
    window_length = int(sr * crossfade_duration)
    for i, seg in enumerate(valid_segments):
        if len(seg) < window_length:
            print(f"警告: 片段 {i} 太短 ({len(seg)} 样本)，无法应用 {crossfade_duration}s 的交叉淡入淡出")
            # 填充短片段
            valid_segments[i] = np.pad(seg, (0, window_length - len(seg)), mode='constant')
    
    hanning_window = np.hanning(2 * window_length)
    
    # Combine
    combined_audio = valid_segments[0]
    for i in range(1, len(valid_segments)):
        segment = valid_segments[i]
        
        # 确保片段长度足够
        if len(combined_audio) < window_length:
            combined_audio = np.pad(combined_audio, (0, window_length - len(combined_audio)), mode='constant')
        if len(segment) < window_length:
            segment = np.pad(segment, (0, window_length - len(segment)), mode='constant')
        
        overlap = combined_audio[-window_length:] * hanning_window[window_length:] + segment[:window_length] * hanning_window[:window_length]
        combined_audio = np.concatenate(
            [combined_audio[:-window_length], overlap, segment[window_length:]]
        )
    
    # 最终长度检查
    min_output_length = int(sr * 0.5)  # 至少0.5秒
    if len(combined_audio) < min_output_length:
        print(f"警告: 合并后的音频太短 ({len(combined_audio)} 样本)，填充到 {min_output_length} 样本")
        combined_audio = np.pad(combined_audio, (0, min_output_length - len(combined_audio)), mode='constant')
    
    return combined_audio