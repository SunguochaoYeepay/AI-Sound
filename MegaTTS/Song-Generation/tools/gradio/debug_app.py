import os
import sys
import json
import time
import traceback
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import gradio as gr
from levo_inference_lowmem import LeVoInference

def debug_generate_song(lyric, description=None, prompt_audio=None, genre=None, cfg_coef=1.5, temperature=0.9, top_k=50):
    """带详细调试信息的音乐生成函数"""
    try:
        print(f"[DEBUG] 开始生成音乐 - {datetime.now()}")
        print(f"[DEBUG] 输入参数:")
        print(f"  歌词长度: {len(lyric) if lyric else 0}")
        print(f"  描述: {description}")
        print(f"  提示音频: {prompt_audio}")
        print(f"  风格: {genre}")
        print(f"  CFG系数: {cfg_coef}")
        print(f"  温度: {temperature}")
        print(f"  Top-K: {top_k}")
        
        # 检查模型是否加载
        if not hasattr(debug_generate_song, 'model'):
            print("[ERROR] 模型未加载!")
            return None, json.dumps({"error": "模型未加载", "timestamp": datetime.now().isoformat()})
            
        model = debug_generate_song.model
        print(f"[DEBUG] 模型已加载: {type(model)}")
        
        # 简单的歌词验证
        if not lyric or len(lyric.strip()) < 10:
            error_msg = "歌词不能为空且长度必须大于10个字符"
            print(f"[ERROR] {error_msg}")
            return None, json.dumps({"error": error_msg, "timestamp": datetime.now().isoformat()})
        
        print("[DEBUG] 开始调用模型生成...")
        start_time = time.time()
        
        # 基础参数
        params = {
            'cfg_coef': cfg_coef,
            'temperature': temperature, 
            'top_k': top_k
        }
        
        # 调用模型
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ckpt", "ckpt", "prompt.pt")
        print(f"[DEBUG] Prompt路径: {prompt_path}")
        print(f"[DEBUG] Prompt文件存在: {os.path.exists(prompt_path)}")
        
        audio_data = model(lyric, description, prompt_audio, genre, prompt_path, params)
        
        if audio_data is None:
            error_msg = "模型返回空结果"
            print(f"[ERROR] {error_msg}")
            return None, json.dumps({"error": error_msg, "timestamp": datetime.now().isoformat()})
            
        print(f"[DEBUG] 模型生成完成，数据类型: {type(audio_data)}")
        print(f"[DEBUG] 数据形状: {audio_data.shape if hasattr(audio_data, 'shape') else 'N/A'}")
        
        # 转换音频数据
        sample_rate = model.cfg.sample_rate
        audio_numpy = audio_data.cpu().permute(1, 0).float().numpy()
        
        end_time = time.time()
        duration = end_time - start_time
        
        result_info = {
            "success": True,
            "duration": duration,
            "sample_rate": sample_rate,
            "audio_shape": list(audio_numpy.shape),
            "timestamp": datetime.now().isoformat(),
            "params": params
        }
        
        print(f"[DEBUG] 生成成功! 耗时: {duration:.2f}秒")
        return (sample_rate, audio_numpy), json.dumps(result_info, indent=2)
        
    except Exception as e:
        error_info = {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }
        print(f"[ERROR] 生成失败: {e}")
        print(f"[ERROR] 错误详情:\n{traceback.format_exc()}")
        return None, json.dumps(error_info, indent=2)

def load_model():
    """加载模型"""
    try:
        model_path = sys.argv[1] if len(sys.argv) > 1 else "../../ckpt/ckpt/songgeneration_base"
        print(f"[DEBUG] 加载模型: {model_path}")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型路径不存在: {model_path}")
            
        model = LeVoInference(model_path)
        debug_generate_song.model = model
        print(f"[DEBUG] 模型加载成功!")
        return True
    except Exception as e:
        print(f"[ERROR] 模型加载失败: {e}")
        print(f"[ERROR] 错误详情:\n{traceback.format_exc()}")
        return False

# 创建界面
with gr.Blocks(title="Song Generation Debug") as demo:
    gr.Markdown("# 🎵 Song Generation Debug Mode")
    gr.Markdown("调试版本，包含详细的错误信息和日志输出")
    
    with gr.Row():
        with gr.Column():
            lyric = gr.Textbox(
                label="歌词",
                lines=5,
                value="[verse]\n在这个疯狂的世界里\n谁不渴望一点改变\n在爱情面前\n我们都显得那么不安全\n\n[chorus]\n约定在那最后的夜晚\n不管命运如何摆布\n我们的心是否依然如初"
            )
            
            genre = gr.Radio(
                choices=["Pop", "R&B", "Dance", "Jazz", "Folk", "Rock"],
                label="风格",
                value="Pop"
            )
            
            description = gr.Textbox(
                label="描述（可选）",
                placeholder="female, bright, pop, happy, piano and drums, the bpm is 120.",
                lines=1
            )
            
            with gr.Row():
                cfg_coef = gr.Slider(0.1, 3.0, value=1.5, label="CFG系数")
                temperature = gr.Slider(0.1, 2.0, value=0.9, label="温度")
                top_k = gr.Slider(1, 100, value=50, label="Top-K")
            
            generate_btn = gr.Button("生成音乐", variant="primary")
        
        with gr.Column():
            output_audio = gr.Audio(label="生成的音乐")
            output_info = gr.JSON(label="生成信息")
    
    # 添加音频提示控件
    prompt_audio = gr.Audio(label="音频提示（可选）", type="filepath")
    
    generate_btn.click(
        fn=debug_generate_song,
        inputs=[lyric, description, prompt_audio, genre, cfg_coef, temperature, top_k],
        outputs=[output_audio, output_info]
    )

if __name__ == "__main__":
    print("[DEBUG] 启动调试应用...")
    if load_model():
        print("[DEBUG] 启动Gradio界面...")
        demo.launch(server_name="127.0.0.1", server_port=7862, debug=True)
    else:
        print("[ERROR] 模型加载失败，无法启动应用") 