import requests
import time
import threading
import subprocess
import os

def monitor_gpu():
    """监控GPU使用情况"""
    print("=== GPU监控开始 ===")
    for i in range(60):  # 监控60秒
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used', '--format=csv,noheader,nounits'], 
                                 capture_output=True, text=True)
            if result.returncode == 0:
                gpu_util, mem_used = result.stdout.strip().split(',')
                print(f"时间: {i:2d}s | GPU使用率: {gpu_util.strip():>3}% | 显存: {mem_used.strip():>4}MB")
            else:
                print(f"时间: {i:2d}s | GPU监控失败")
        except Exception as e:
            print(f"时间: {i:2d}s | GPU监控错误: {e}")
        time.sleep(1)
    print("=== GPU监控结束 ===")

def send_tts_request():
    """发送TTS请求"""
    print("准备发送TTS请求...")
    
    # 文件路径 - 使用温柔女声
    audio_file = "./data/voice_profiles/温柔女声_5a0159820339423581502556bccc8b94.wav"
    latent_file = "./data/voice_profiles/温柔女声_0f6aa03fedf54a5caca91515b606e2ad.npy"
    
    # 检查文件是否存在
    if not os.path.exists(audio_file):
        print(f"❌ 音频文件不存在: {audio_file}")
        return
    if not os.path.exists(latent_file):
        print(f"❌ Latent文件不存在: {latent_file}")
        return
    
    print(f"✅ 音频文件: {audio_file} ({os.path.getsize(audio_file)} bytes)")
    print(f"✅ Latent文件: {latent_file} ({os.path.getsize(latent_file)} bytes)")
    
    # 长文本
    text = """在这个充满挑战和机遇的时代，我们每一个人都肩负着重要的使命。科技的飞速发展为我们带来了前所未有的便利，同时也提出了新的要求。人工智能、大数据、云计算等新兴技术正在深刻地改变着我们的生活方式和工作模式。在这样的背景下，我们必须保持学习的热情，不断更新自己的知识结构，才能在激烈的竞争中立于不败之地。教育的重要性在这个时代显得尤为突出，它不仅是个人成长的基石，更是国家发展的根本。我们要培养创新思维，敢于探索未知的领域，勇于挑战传统的观念。只有这样，我们才能在未来的道路上走得更远，飞得更高。"""
    
    print(f"📝 文本长度: {len(text)} 字符")
    print("🚀 开始发送TTS请求...")
    
    try:
        # 准备文件和数据
        with open(audio_file, 'rb') as af, open(latent_file, 'rb') as lf:
            files = {
                'audio_file': af,
                'latent_file': lf
            }
            data = {
                'text': text,
                'time_step': '20',
                'p_w': '1.0',
                't_w': '1.0'
            }
            
            start_time = time.time()
            response = requests.post(
                'http://localhost:7929/api/v1/tts/synthesize_file',
                files=files,
                data=data,
                timeout=300  # 5分钟超时
            )
            end_time = time.time()
            
            print(f"⏱️  请求耗时: {end_time - start_time:.2f} 秒")
            print(f"📊 响应状态: {response.status_code}")
            
            if response.status_code == 200:
                # 保存音频文件
                with open('test_output.wav', 'wb') as f:
                    f.write(response.content)
                print(f"✅ 合成成功! 音频保存为: test_output.wav ({len(response.content)} bytes)")
            else:
                print(f"❌ 合成失败: {response.text}")
                
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    print("=== MegaTTS3 GPU使用测试 ===")
    
    # 启动GPU监控线程
    gpu_thread = threading.Thread(target=monitor_gpu, daemon=True)
    gpu_thread.start()
    
    # 等待2秒让监控稳定
    time.sleep(2)
    
    # 发送TTS请求
    send_tts_request()
    
    # 等待一段时间让监控继续
    print("等待监控完成...")
    gpu_thread.join() 