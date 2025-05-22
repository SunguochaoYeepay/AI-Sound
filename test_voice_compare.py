#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
声音对比测试工具
生成不同声音ID和情感的音频样本，并进行比较和可视化
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
import argparse
import logging
import time
import json
from collections import defaultdict
import shutil
import hashlib
import concurrent.futures

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("voice_compare")

# 添加API路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "services", "api", "src"))

# 导入TTS引擎
from tts.engine import MegaTTSEngine

def save_audio_with_plot(audio, filename, sample_rate=22050, title=None):
    """保存音频并生成波形图"""
    # 确保输出目录存在
    output_dir = os.path.dirname(filename)
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存音频
    wavfile.write(filename, sample_rate, audio.astype(np.float32))
    
    # 生成波形图
    plt.figure(figsize=(10, 4))
    plt.plot(audio)
    plt.title(title or os.path.basename(filename))
    plt.xlabel('Sample')
    plt.ylabel('Amplitude')
    plt.tight_layout()
    
    # 保存波形图
    plot_filename = f"{os.path.splitext(filename)[0]}.png"
    plt.savefig(plot_filename)
    plt.close()
    
    return filename, plot_filename

def clean_directory(directory, confirm=True):
    """清理目录内容"""
    if os.path.exists(directory):
        if confirm:
            response = input(f"是否清空目录 {directory}? (y/n): ")
            if response.lower() != 'y':
                logger.info("操作已取消")
                return False
        
        # 清空目录
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
        logger.info(f"已清空目录: {directory}")
    else:
        # 创建目录
        os.makedirs(directory, exist_ok=True)
        logger.info(f"已创建目录: {directory}")
    
    return True

def generate_voice_samples(engine, test_config, output_dir, parallel=False):
    """生成语音样本"""
    results = defaultdict(dict)
    
    # 优先获取引擎支持的声音列表
    available_voices = engine.get_available_voices()
    voice_ids = [voice["id"] for voice in available_voices]
    logger.info(f"TTS引擎支持的声音: {voice_ids}")
    
    # 检查测试文本
    if not test_config["texts"]:
        logger.error("未提供测试文本")
        return None
    
    # 检查声音ID
    test_voices = test_config["voices"]
    if not test_voices:
        # 如果未指定，使用所有可用声音
        test_voices = voice_ids
        logger.info(f"使用所有可用声音进行测试: {test_voices}")
    else:
        # 验证声音ID是否可用
        invalid_voices = [v for v in test_voices if v not in voice_ids]
        if invalid_voices:
            logger.warning(f"以下声音ID不可用: {invalid_voices}，将被跳过")
            test_voices = [v for v in test_voices if v in voice_ids]
    
    # 检查情感类型
    available_emotions = engine.get_available_emotions()
    emotion_ids = [emotion["id"] for emotion in available_emotions]
    
    test_emotions = test_config["emotions"]
    if not test_emotions:
        # 如果未指定，使用中性情感
        test_emotions = [{"type": "neutral", "intensity": 0.5}]
    else:
        # 验证情感类型是否可用
        for emotion in test_emotions:
            if emotion["type"] not in emotion_ids:
                logger.warning(f"情感类型不可用: {emotion['type']}，将使用neutral替代")
                emotion["type"] = "neutral"
    
    # 创建总目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成音频
    total_samples = len(test_config["texts"]) * len(test_voices) * len(test_emotions)
    logger.info(f"计划生成 {total_samples} 个样本")
    
    sample_count = 0
    start_time = time.time()
    
    if parallel and len(test_config["texts"]) > 1:
        # 使用并行处理
        logger.info("使用并行处理加速生成")
        
        # 准备任务列表
        tasks = []
        
        for text_id, text in enumerate(test_config["texts"]):
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            text_dir = os.path.join(output_dir, f"text_{text_id}_{text_hash}")
            os.makedirs(text_dir, exist_ok=True)
            
            for voice_id in test_voices:
                for emotion in test_emotions:
                    emotion_type = emotion["type"]
                    emotion_intensity = emotion["intensity"]
                    
                    output_filename = f"{voice_id}_{emotion_type}_{int(emotion_intensity*100)}.wav"
                    output_path = os.path.join(text_dir, output_filename)
                    
                    # 添加到任务列表
                    tasks.append({
                        "text": text,
                        "text_id": text_id,
                        "text_hash": text_hash,
                        "voice_id": voice_id,
                        "emotion_type": emotion_type,
                        "emotion_intensity": emotion_intensity,
                        "output_path": output_path,
                        "text_dir": text_dir
                    })
        
        # 使用线程池并行处理
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # 提交任务
            future_to_task = {
                executor.submit(
                    process_sample, 
                    engine, 
                    task["text"],
                    task["voice_id"],
                    task["emotion_type"],
                    task["emotion_intensity"],
                    task["output_path"]
                ): task for task in tasks
            }
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    audio_file, plot_file = future.result()
                    
                    # 记录结果
                    text_key = f"text_{task['text_id']}_{task['text_hash']}"
                    if text_key not in results:
                        results[text_key] = {
                            "text": task["text"],
                            "samples": []
                        }
                    
                    results[text_key]["samples"].append({
                        "voice_id": task["voice_id"],
                        "emotion_type": task["emotion_type"],
                        "emotion_intensity": task["emotion_intensity"],
                        "audio_file": audio_file,
                        "plot_file": plot_file
                    })
                    
                    sample_count += 1
                    if sample_count % 10 == 0 or sample_count == total_samples:
                        elapsed = time.time() - start_time
                        logger.info(f"已生成 {sample_count}/{total_samples} 个样本，用时: {elapsed:.2f}秒")
                        
                except Exception as e:
                    logger.error(f"处理样本时出错: {str(e)}")
    else:
        # 顺序处理
        for text_id, text in enumerate(test_config["texts"]):
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            text_dir = os.path.join(output_dir, f"text_{text_id}_{text_hash}")
            os.makedirs(text_dir, exist_ok=True)
            
            text_key = f"text_{text_id}_{text_hash}"
            results[text_key] = {
                "text": text,
                "samples": []
            }
            
            for voice_id in test_voices:
                for emotion in test_emotions:
                    emotion_type = emotion["type"]
                    emotion_intensity = emotion["intensity"]
                    
                    logger.info(f"生成样本: 文本='{text[:30]}...', 声音={voice_id}, 情感={emotion_type}, 强度={emotion_intensity}")
                    
                    output_filename = f"{voice_id}_{emotion_type}_{int(emotion_intensity*100)}.wav"
                    output_path = os.path.join(text_dir, output_filename)
                    
                    try:
                        # 生成音频
                        audio = engine.synthesize(
                            text=text,
                            voice_id=voice_id,
                            emotion_type=emotion_type,
                            emotion_intensity=emotion_intensity
                        )
                        
                        # 保存音频和波形图
                        title = f"{voice_id} - {emotion_type} ({emotion_intensity})"
                        audio_file, plot_file = save_audio_with_plot(
                            audio, 
                            output_path, 
                            title=title
                        )
                        
                        # 记录结果
                        results[text_key]["samples"].append({
                            "voice_id": voice_id,
                            "emotion_type": emotion_type,
                            "emotion_intensity": emotion_intensity,
                            "audio_file": audio_file,
                            "plot_file": plot_file
                        })
                        
                        sample_count += 1
                        if sample_count % 5 == 0 or sample_count == total_samples:
                            elapsed = time.time() - start_time
                            logger.info(f"已生成 {sample_count}/{total_samples} 个样本，用时: {elapsed:.2f}秒")
                            
                    except Exception as e:
                        logger.error(f"生成样本时出错: {str(e)}")
    
    total_time = time.time() - start_time
    logger.info(f"样本生成完成，共 {sample_count} 个样本，总用时: {total_time:.2f}秒")
    
    # 保存配置和结果
    config_file = os.path.join(output_dir, "test_config.json")
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(test_config, f, ensure_ascii=False, indent=2)
    
    results_file = os.path.join(output_dir, "test_results.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    return results

def process_sample(engine, text, voice_id, emotion_type, emotion_intensity, output_path):
    """处理单个样本（用于并行处理）"""
    try:
        # 生成音频
        audio = engine.synthesize(
            text=text,
            voice_id=voice_id,
            emotion_type=emotion_type,
            emotion_intensity=emotion_intensity
        )
        
        # 保存音频和波形图
        title = f"{voice_id} - {emotion_type} ({emotion_intensity})"
        return save_audio_with_plot(audio, output_path, title=title)
    except Exception as e:
        logger.error(f"处理样本时出错: {str(e)}")
        return None, None

def generate_html_report(results, output_dir):
    """生成HTML格式的比较报告"""
    report_path = os.path.join(output_dir, "voice_compare_report.html")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>声音对比报告</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; line-height: 1.6; }
                h1, h2, h3 { color: #333; }
                .container { max-width: 1200px; margin: 0 auto; }
                .text-section { margin-bottom: 50px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
                .voice-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }
                .voice-item { border: 1px solid #eee; padding: 15px; border-radius: 5px; }
                .voice-item h4 { margin-top: 0; margin-bottom: 10px; }
                .controls { margin-top: 10px; }
                .wave-image { max-width: 100%; height: auto; margin-top: 10px; border: 1px solid #eee; }
                audio { width: 100%; margin-top: 5px; }
                .text-display { background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 15px 0; white-space: pre-wrap; }
                .nav { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }
                .nav a { padding: 8px 15px; background: #f2f2f2; text-decoration: none; color: #333; border-radius: 5px; }
                .nav a:hover { background: #e2e2e2; }
                .footer { margin-top: 30px; text-align: center; color: #777; font-size: 0.9em; }
                .filter-controls { margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 5px; }
                .filter-row { display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 10px; }
                .filter-group { flex: 1; min-width: 200px; }
                label { display: block; margin-bottom: 5px; font-weight: bold; }
                select, button { padding: 8px; width: 100%; }
                button { background: #4CAF50; color: white; border: none; cursor: pointer; border-radius: 4px; }
                button:hover { background: #45a049; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>声音对比报告</h1>
                <p>生成时间: <script>document.write(new Date().toLocaleString())</script></p>
                
                <div class="filter-controls">
                    <h3>筛选控制</h3>
                    <div class="filter-row">
                        <div class="filter-group">
                            <label for="voice-filter">声音:</label>
                            <select id="voice-filter">
                                <option value="all">所有声音</option>
                            </select>
                        </div>
                        <div class="filter-group">
                            <label for="emotion-filter">情感:</label>
                            <select id="emotion-filter">
                                <option value="all">所有情感</option>
                            </select>
                        </div>
                        <div class="filter-group">
                            <button id="apply-filter">应用筛选</button>
                        </div>
                    </div>
                </div>
                
                <div class="nav">
                    <a href="#" onclick="scrollToTop(); return false;">回到顶部</a>
        """)
        
        # 添加导航链接
        for text_key, text_data in results.items():
            text_id = text_key.split("_")[1]
            f.write(f'<a href="#{text_key}">{text_id}: {text_data["text"][:20]}...</a>\n')
        
        f.write("""
                </div>
        """)
        
        # 添加每个文本段的样本
        for text_key, text_data in results.items():
            f.write(f"""
                <div class="text-section" id="{text_key}">
                    <h2>文本 {text_key.split("_")[1]}</h2>
                    <div class="text-display">{text_data['text']}</div>
                    
                    <div class="voice-grid">
            """)
            
            # 添加每个样本
            for sample in text_data["samples"]:
                voice_id = sample["voice_id"]
                emotion_type = sample["emotion_type"]
                emotion_intensity = sample["emotion_intensity"]
                audio_file = sample["audio_file"]
                plot_file = sample["plot_file"]
                
                # 将绝对路径转换为相对路径
                rel_audio = os.path.relpath(audio_file, output_dir)
                rel_plot = os.path.relpath(plot_file, output_dir)
                
                f.write(f"""
                        <div class="voice-item" data-voice="{voice_id}" data-emotion="{emotion_type}">
                            <h4>{voice_id} - {emotion_type} ({emotion_intensity})</h4>
                            <div class="controls">
                                <audio controls src="{rel_audio}"></audio>
                            </div>
                            <img class="wave-image" src="{rel_plot}" alt="波形图">
                        </div>
                """)
            
            f.write("""
                    </div>
                </div>
            """)
        
        # 添加筛选功能的JavaScript
        f.write("""
                <div class="footer">
                    <p>声音对比测试工具生成的报告</p>
                </div>
            </div>
            
            <script>
                // 获取所有声音和情感类型
                const voiceItems = document.querySelectorAll('.voice-item');
                const voices = new Set();
                const emotions = new Set();
                
                voiceItems.forEach(item => {
                    voices.add(item.dataset.voice);
                    emotions.add(item.dataset.emotion);
                });
                
                // 填充筛选下拉框
                const voiceFilter = document.getElementById('voice-filter');
                const emotionFilter = document.getElementById('emotion-filter');
                
                voices.forEach(voice => {
                    const option = document.createElement('option');
                    option.value = voice;
                    option.textContent = voice;
                    voiceFilter.appendChild(option);
                });
                
                emotions.forEach(emotion => {
                    const option = document.createElement('option');
                    option.value = emotion;
                    option.textContent = emotion;
                    emotionFilter.appendChild(option);
                });
                
                // 应用筛选
                document.getElementById('apply-filter').addEventListener('click', function() {
                    const selectedVoice = voiceFilter.value;
                    const selectedEmotion = emotionFilter.value;
                    
                    voiceItems.forEach(item => {
                        const voice = item.dataset.voice;
                        const emotion = item.dataset.emotion;
                        
                        if ((selectedVoice === 'all' || selectedVoice === voice) && 
                            (selectedEmotion === 'all' || selectedEmotion === emotion)) {
                            item.style.display = '';
                        } else {
                            item.style.display = 'none';
                        }
                    });
                });
                
                // 滚动到顶部函数
                function scrollToTop() {
                    window.scrollTo({top: 0, behavior: 'smooth'});
                }
            </script>
        </body>
        </html>
        """)
    
    logger.info(f"已生成HTML报告: {report_path}")
    return report_path

def main():
    parser = argparse.ArgumentParser(description='声音对比测试工具')
    parser.add_argument('--config', '-c', help='测试配置JSON文件')
    parser.add_argument('--output', '-o', default='voice_compare_output', help='输出目录')
    parser.add_argument('--parallel', '-p', action='store_true', help='使用并行处理加速生成')
    parser.add_argument('--clean', action='store_true', help='清空输出目录')
    
    args = parser.parse_args()
    
    # 设置输出目录
    output_dir = args.output
    
    # 如果需要，清空输出目录
    if args.clean:
        if not clean_directory(output_dir):
            return
    else:
        os.makedirs(output_dir, exist_ok=True)
    
    # 加载测试配置
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r', encoding='utf-8') as f:
            test_config = json.load(f)
    else:
        # 使用默认配置
        logger.info("使用默认测试配置")
        test_config = {
            "texts": [
                "这是一段测试文本，用于测试不同声音和情感的语音合成效果。",
                "人工智能语音合成技术可以模拟不同说话人的声音特征，生成自然流畅的语音。",
                "未来，我们将看到更多基于AI的语音应用，使人机交互更加自然和智能。"
            ],
            "voices": [],  # 空列表表示使用所有可用声音
            "emotions": [
                {"type": "neutral", "intensity": 0.5},
                {"type": "happy", "intensity": 0.8},
                {"type": "sad", "intensity": 0.7},
                {"type": "angry", "intensity": 0.9},
                {"type": "surprise", "intensity": 0.8}
            ]
        }
    
    logger.info("=== 声音对比测试工具 ===")
    logger.info(f"测试文本数量: {len(test_config['texts'])}")
    logger.info(f"声音ID: {test_config['voices'] or '所有可用声音'}")
    logger.info(f"情感类型: {', '.join([e['type'] for e in test_config['emotions']])}")
    logger.info(f"输出目录: {output_dir}")
    logger.info(f"并行处理: {'启用' if args.parallel else '禁用'}")
    
    # 初始化TTS引擎
    logger.info("初始化TTS引擎...")
    engine = MegaTTSEngine()
    
    # 生成语音样本
    results = generate_voice_samples(engine, test_config, output_dir, args.parallel)
    
    if results:
        # 生成HTML报告
        report_path = generate_html_report(results, output_dir)
        logger.info(f"测试完成，报告已保存到: {report_path}")
    else:
        logger.error("测试失败")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("操作被用户取消")
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc()) 