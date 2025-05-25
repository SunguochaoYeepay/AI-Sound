#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
声音特征分析工具
分析并可视化声音样本的特征
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import librosa
import librosa.display
import soundfile as sf
from scipy.io import wavfile
import argparse
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("voice_feature_analyzer")

def load_npy_feature(file_path):
    """加载NPY格式的声音特征文件"""
    try:
        data = np.load(file_path)
        logger.info(f"已加载NPY文件: {file_path}")
        logger.info(f"数据形状: {data.shape}, 数据类型: {data.dtype}")
        
        # 处理不同维度的数据
        if len(data.shape) == 3:
            logger.info(f"3D数据: (batch_size={data.shape[0]}, seq_len={data.shape[1]}, features={data.shape[2]})")
            # 如果是3D数据，取第一个样本
            if data.shape[0] == 1:
                data = data[0]  # 转换为2D: (seq_len, features)
                logger.info(f"转换为2D数据: {data.shape}")
        elif len(data.shape) == 2:
            logger.info(f"2D数据: (seq_len={data.shape[0]}, features={data.shape[1]})")
        elif len(data.shape) == 1:
            logger.warning(f"1D数据: (length={data.shape[0]}), 可能不是有效的声音特征")
        
        return data
    except Exception as e:
        logger.error(f"加载NPY文件时出错: {str(e)}")
        return None

def load_audio_file(file_path):
    """加载音频文件并提取特征"""
    try:
        # 使用librosa加载音频
        y, sr = librosa.load(file_path, sr=None)
        logger.info(f"已加载音频文件: {file_path}")
        logger.info(f"采样率: {sr}Hz, 持续时间: {len(y)/sr:.2f}秒")
        
        # 提取基本特征
        features = {
            "waveform": y,
            "sample_rate": sr,
            "duration": len(y)/sr,
            # 添加更多特征提取
            "mfcc": librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20),
            "spectral_centroid": librosa.feature.spectral_centroid(y=y, sr=sr),
            "chroma": librosa.feature.chroma_stft(y=y, sr=sr),
            "zero_crossing_rate": librosa.feature.zero_crossing_rate(y)
        }
        
        return features
    except Exception as e:
        logger.error(f"处理音频文件时出错: {str(e)}")
        return None

def plot_npy_feature(data, output_dir, filename_prefix):
    """绘制NPY特征的可视化图表"""
    if data is None:
        return
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 绘制热图
    plt.figure(figsize=(12, 8))
    plt.imshow(data.T, aspect='auto', origin='lower')
    plt.colorbar(format='%+2.0f')
    plt.title(f'声音特征热图 ({data.shape[0]} frames, {data.shape[1]} features)')
    plt.xlabel('帧')
    plt.ylabel('特征维度')
    plt.tight_layout()
    
    # 保存热图
    heatmap_path = os.path.join(output_dir, f"{filename_prefix}_heatmap.png")
    plt.savefig(heatmap_path)
    plt.close()
    logger.info(f"已保存热图: {heatmap_path}")
    
    # 绘制每个特征维度的均值和方差
    mean_values = np.mean(data, axis=0)
    std_values = np.std(data, axis=0)
    
    plt.figure(figsize=(12, 6))
    plt.bar(range(len(mean_values)), mean_values, yerr=std_values, alpha=0.7)
    plt.title('特征维度均值和标准差')
    plt.xlabel('特征维度')
    plt.ylabel('均值 (+/- 标准差)')
    plt.tight_layout()
    
    # 保存统计图
    stats_path = os.path.join(output_dir, f"{filename_prefix}_stats.png")
    plt.savefig(stats_path)
    plt.close()
    logger.info(f"已保存统计图: {stats_path}")
    
    # 绘制特征随时间变化的趋势图 (选择前5个特征维度)
    plt.figure(figsize=(12, 8))
    for i in range(min(5, data.shape[1])):
        plt.plot(data[:, i], label=f'特征 #{i}')
    plt.title('特征随时间变化趋势 (前5个维度)')
    plt.xlabel('帧')
    plt.ylabel('特征值')
    plt.legend()
    plt.tight_layout()
    
    # 保存趋势图
    trend_path = os.path.join(output_dir, f"{filename_prefix}_trend.png")
    plt.savefig(trend_path)
    plt.close()
    logger.info(f"已保存趋势图: {trend_path}")
    
    return {
        "heatmap": heatmap_path,
        "stats": stats_path,
        "trend": trend_path
    }

def plot_audio_features(features, output_dir, filename_prefix):
    """绘制音频特征的可视化图表"""
    if features is None:
        return
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 波形图
    plt.figure(figsize=(12, 4))
    librosa.display.waveshow(features["waveform"], sr=features["sample_rate"])
    plt.title('波形图')
    plt.tight_layout()
    waveform_path = os.path.join(output_dir, f"{filename_prefix}_waveform.png")
    plt.savefig(waveform_path)
    plt.close()
    logger.info(f"已保存波形图: {waveform_path}")
    
    # 梅尔频谱图
    S = librosa.feature.melspectrogram(y=features["waveform"], sr=features["sample_rate"])
    S_dB = librosa.power_to_db(S, ref=np.max)
    plt.figure(figsize=(12, 4))
    librosa.display.specshow(S_dB, x_axis='time', y_axis='mel', sr=features["sample_rate"])
    plt.colorbar(format='%+2.0f dB')
    plt.title('梅尔频谱图')
    plt.tight_layout()
    mel_path = os.path.join(output_dir, f"{filename_prefix}_melspectrogram.png")
    plt.savefig(mel_path)
    plt.close()
    logger.info(f"已保存梅尔频谱图: {mel_path}")
    
    # MFCC特征
    plt.figure(figsize=(12, 4))
    librosa.display.specshow(features["mfcc"], x_axis='time')
    plt.colorbar()
    plt.title('MFCC特征')
    plt.tight_layout()
    mfcc_path = os.path.join(output_dir, f"{filename_prefix}_mfcc.png")
    plt.savefig(mfcc_path)
    plt.close()
    logger.info(f"已保存MFCC特征图: {mfcc_path}")
    
    # 色度图
    plt.figure(figsize=(12, 4))
    librosa.display.specshow(features["chroma"], y_axis='chroma', x_axis='time')
    plt.colorbar()
    plt.title('色度特征')
    plt.tight_layout()
    chroma_path = os.path.join(output_dir, f"{filename_prefix}_chroma.png")
    plt.savefig(chroma_path)
    plt.close()
    logger.info(f"已保存色度特征图: {chroma_path}")
    
    return {
        "waveform": waveform_path,
        "mel": mel_path,
        "mfcc": mfcc_path,
        "chroma": chroma_path
    }

def generate_html_report(results, output_dir):
    """生成HTML格式的分析报告"""
    html_path = os.path.join(output_dir, "voice_analysis_report.html")
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>声音特征分析报告</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; line-height: 1.6; }
                h1, h2, h3 { color: #333; }
                .container { max-width: 1200px; margin: 0 auto; }
                .sample { margin-bottom: 40px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
                .sample-header { display: flex; justify-content: space-between; align-items: center; }
                .image-container { margin-top: 20px; }
                .image-row { display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 20px; }
                .image-item { flex: 1; min-width: 300px; }
                img { max-width: 100%; height: auto; border: 1px solid #eee; }
                .stats { margin-top: 10px; }
                table { width: 100%; border-collapse: collapse; margin-top: 10px; }
                th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f2f2f2; }
                .footer { margin-top: 30px; text-align: center; color: #777; font-size: 0.9em; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>声音特征分析报告</h1>
                <p>生成时间: <script>document.write(new Date().toLocaleString())</script></p>
        """)
        
        # 为每个样本添加结果
        for sample_name, sample_data in results.items():
            f.write(f"""
                <div class="sample">
                    <div class="sample-header">
                        <h2>{sample_name}</h2>
                    </div>
                    
                    <div class="stats">
                        <h3>样本信息</h3>
                        <table>
                            <tr>
                                <th>属性</th>
                                <th>值</th>
                            </tr>
            """)
            
            # 添加样本信息
            if "file_type" in sample_data:
                f.write(f"""
                            <tr>
                                <td>文件类型</td>
                                <td>{sample_data["file_type"]}</td>
                            </tr>
                """)
                
            if "file_path" in sample_data:
                f.write(f"""
                            <tr>
                                <td>文件路径</td>
                                <td>{sample_data["file_path"]}</td>
                            </tr>
                """)
                
            if "shape" in sample_data:
                f.write(f"""
                            <tr>
                                <td>数据形状</td>
                                <td>{sample_data["shape"]}</td>
                            </tr>
                """)
                
            if "audio_info" in sample_data and sample_data["audio_info"]:
                audio_info = sample_data["audio_info"]
                if "duration" in audio_info:
                    f.write(f"""
                            <tr>
                                <td>持续时间</td>
                                <td>{audio_info["duration"]:.2f}秒</td>
                            </tr>
                    """)
                if "sample_rate" in audio_info:
                    f.write(f"""
                            <tr>
                                <td>采样率</td>
                                <td>{audio_info["sample_rate"]}Hz</td>
                            </tr>
                    """)
                    
            f.write("""
                        </table>
                    </div>
            """)
            
            # 添加NPY特征可视化
            if "npy_plots" in sample_data and sample_data["npy_plots"]:
                npy_plots = sample_data["npy_plots"]
                f.write("""
                    <div class="image-container">
                        <h3>NPY特征可视化</h3>
                        <div class="image-row">
                """)
                
                if "heatmap" in npy_plots:
                    rel_path = os.path.relpath(npy_plots["heatmap"], output_dir)
                    f.write(f"""
                            <div class="image-item">
                                <h4>特征热图</h4>
                                <img src="{rel_path}" alt="特征热图">
                            </div>
                    """)
                    
                if "stats" in npy_plots:
                    rel_path = os.path.relpath(npy_plots["stats"], output_dir)
                    f.write(f"""
                            <div class="image-item">
                                <h4>特征统计</h4>
                                <img src="{rel_path}" alt="特征统计">
                            </div>
                    """)
                    
                f.write("""
                        </div>
                        <div class="image-row">
                """)
                
                if "trend" in npy_plots:
                    rel_path = os.path.relpath(npy_plots["trend"], output_dir)
                    f.write(f"""
                            <div class="image-item">
                                <h4>特征趋势</h4>
                                <img src="{rel_path}" alt="特征趋势">
                            </div>
                    """)
                    
                f.write("""
                        </div>
                    </div>
                """)
                
            # 添加音频特征可视化
            if "audio_plots" in sample_data and sample_data["audio_plots"]:
                audio_plots = sample_data["audio_plots"]
                f.write("""
                    <div class="image-container">
                        <h3>音频特征可视化</h3>
                        <div class="image-row">
                """)
                
                if "waveform" in audio_plots:
                    rel_path = os.path.relpath(audio_plots["waveform"], output_dir)
                    f.write(f"""
                            <div class="image-item">
                                <h4>波形图</h4>
                                <img src="{rel_path}" alt="波形图">
                            </div>
                    """)
                    
                if "mel" in audio_plots:
                    rel_path = os.path.relpath(audio_plots["mel"], output_dir)
                    f.write(f"""
                            <div class="image-item">
                                <h4>梅尔频谱图</h4>
                                <img src="{rel_path}" alt="梅尔频谱图">
                            </div>
                    """)
                    
                f.write("""
                        </div>
                        <div class="image-row">
                """)
                
                if "mfcc" in audio_plots:
                    rel_path = os.path.relpath(audio_plots["mfcc"], output_dir)
                    f.write(f"""
                            <div class="image-item">
                                <h4>MFCC特征</h4>
                                <img src="{rel_path}" alt="MFCC特征">
                            </div>
                    """)
                    
                if "chroma" in audio_plots:
                    rel_path = os.path.relpath(audio_plots["chroma"], output_dir)
                    f.write(f"""
                            <div class="image-item">
                                <h4>色度特征</h4>
                                <img src="{rel_path}" alt="色度特征">
                            </div>
                    """)
                    
                f.write("""
                        </div>
                    </div>
                """)
                
            f.write("""
                </div>
            """)
            
        f.write("""
                <div class="footer">
                    <p>声音特征分析工具生成的报告</p>
                </div>
            </div>
        </body>
        </html>
        """)
        
    logger.info(f"已生成HTML报告: {html_path}")
    return html_path

def analyze_sample(file_path, output_dir, name_prefix=None):
    """分析单个声音样本文件"""
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return None
    
    # 确定文件类型和前缀
    file_ext = os.path.splitext(file_path)[1].lower()
    if name_prefix is None:
        name_prefix = os.path.splitext(os.path.basename(file_path))[0]
    
    result = {
        "file_path": file_path,
        "file_type": file_ext
    }
    
    # 根据文件类型进行处理
    if file_ext == '.npy':
        # 处理NPY声音特征文件
        data = load_npy_feature(file_path)
        if data is not None:
            result["shape"] = data.shape
            result["npy_plots"] = plot_npy_feature(data, output_dir, name_prefix)
    elif file_ext in ['.wav', '.mp3', '.flac', '.ogg']:
        # 处理音频文件
        features = load_audio_file(file_path)
        if features is not None:
            result["audio_info"] = {
                "duration": features["duration"],
                "sample_rate": features["sample_rate"]
            }
            result["audio_plots"] = plot_audio_features(features, output_dir, name_prefix)
    else:
        logger.warning(f"不支持的文件类型: {file_ext}")
        
    return result

def analyze_directory(directory, output_dir):
    """分析目录中的所有声音样本文件"""
    if not os.path.exists(directory):
        logger.error(f"目录不存在: {directory}")
        return None
    
    results = {}
    
    # 遍历目录中的文件
    for root, _, files in os.walk(directory):
        for file in files:
            file_ext = os.path.splitext(file)[1].lower()
            if file_ext in ['.npy', '.wav', '.mp3', '.flac', '.ogg']:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, directory)
                name_prefix = os.path.splitext(file)[0]
                
                logger.info(f"分析文件: {rel_path}")
                result = analyze_sample(file_path, output_dir, name_prefix)
                
                if result:
                    results[name_prefix] = result
    
    return results

def main():
    parser = argparse.ArgumentParser(description='声音特征分析工具')
    parser.add_argument('--input', '-i', required=True, help='输入文件或目录路径')
    parser.add_argument('--output', '-o', default='voice_analysis_output', help='输出目录路径')
    parser.add_argument('--sample-name', '-n', help='样本名称前缀（仅适用于单个文件分析）')
    
    args = parser.parse_args()
    
    # 确保输出目录存在
    os.makedirs(args.output, exist_ok=True)
    
    logger.info(f"=== 声音特征分析工具 ===")
    logger.info(f"输入: {args.input}")
    logger.info(f"输出目录: {args.output}")
    
    # 根据输入类型处理
    if os.path.isfile(args.input):
        # 分析单个文件
        logger.info(f"分析单个文件: {args.input}")
        result = analyze_sample(args.input, args.output, args.sample_name)
        
        if result:
            results = {args.sample_name or os.path.splitext(os.path.basename(args.input))[0]: result}
            report_path = generate_html_report(results, args.output)
            logger.info(f"分析完成，报告已保存到: {report_path}")
        else:
            logger.error("分析失败")
            
    elif os.path.isdir(args.input):
        # 分析目录
        logger.info(f"分析目录: {args.input}")
        results = analyze_directory(args.input, args.output)
        
        if results:
            report_path = generate_html_report(results, args.output)
            logger.info(f"分析完成，共分析了 {len(results)} 个文件")
            logger.info(f"报告已保存到: {report_path}")
        else:
            logger.error("没有找到可分析的文件或分析失败")
            
    else:
        logger.error(f"输入路径无效: {args.input}")
        
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc()) 