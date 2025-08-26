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

import multiprocessing as mp
import torch
import os
from functools import partial
import gradio as gr
import traceback
import requests
import tempfile
from tts.infer_cli import MegaTTS3DiTInfer, convert_to_wav, cut_wav


def model_worker(input_queue, output_queue, device_id):
    device = None
    if device_id is not None:
        device = torch.device(f'cuda:{device_id}')
    infer_pipe = MegaTTS3DiTInfer(device=device)

    while True:
        task = input_queue.get()
        inp_audio_path, inp_npy_path, inp_text, infer_timestep, p_w, t_w = task
        try:
            convert_to_wav(inp_audio_path)
            wav_path = os.path.splitext(inp_audio_path)[0] + '.wav'
            cut_wav(wav_path, max_len=28)
            with open(wav_path, 'rb') as file:
                file_content = file.read()
            resource_context = infer_pipe.preprocess(file_content, latent_file=inp_npy_path)
            wav_bytes = infer_pipe.forward(resource_context, inp_text, time_step=infer_timestep, p_w=p_w, t_w=t_w)
            output_queue.put(wav_bytes)
        except Exception as e:
            traceback.print_exc()
            print(task, str(e))
            output_queue.put(None)


def main(inp_audio, inp_npy, inp_text, infer_timestep, p_w, t_w, processes, input_queue, output_queue):
    print("Push task to the inp queue |", inp_audio, inp_npy, inp_text, infer_timestep, p_w, t_w)
    input_queue.put((inp_audio, inp_npy, inp_text, infer_timestep, p_w, t_w))
    res = output_queue.get()
    if res is not None:
        return res
    else:
        print("")
        return None


def create_api_demo_html():
    """创建API Demo的HTML内容 - 不包含JavaScript"""
    html_content = """
    <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
        <h2>🔌 MegaTTS3 API Demo</h2>
        <p>基于API接口的语音合成测试 - 验证与WebUI功能一致性</p>
        
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3>📋 使用说明</h3>
            <p>1. 上传参考音频文件 (.wav)</p>
            <p>2. 上传对应的Latent文件 (.npy)</p>
            <p>3. 输入要合成的文本</p>
            <p>4. 调整参数后点击合成</p>
        </div>
        
        <div style="background: #e7f3ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3>✅ 优势</h3>
            <p>• 稳定可靠的API接口调用</p>
            <p>• 与原生WebUI功能完全一致</p>
            <p>• 支持批量处理和自动化</p>
            <p>• 便于集成到其他应用中</p>
        </div>
    </div>
    """
    return html_content


def api_synthesize(audio_file, latent_file, text, infer_timestep, p_w, t_w):
    """通过API接口进行语音合成"""
    if not audio_file or not latent_file or not text.strip():
        return None, "❌ 请完整填写所有字段！"
    
    try:
        # 准备文件上传
        files = {
            'audio_file': open(audio_file, 'rb'),
            'latent_file': open(latent_file, 'rb')
        }
        
        data = {
            'text': text,
            'infer_timestep': int(infer_timestep),
            'p_w': float(p_w),
            't_w': float(t_w)
        }
        
        # 调用API
        response = requests.post(
            'http://127.0.0.1:7929/api/v1/tts/synthesize_file',
            files=files,
            data=data,
            timeout=120
        )
        
        # 关闭文件
        files['audio_file'].close()
        files['latent_file'].close()
        
        if response.status_code == 200:
            # 保存返回的音频文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_file.write(response.content)
                return tmp_file.name, f"✅ 合成成功！音频长度: {len(response.content)} 字节"
        else:
            return None, f"❌ API调用失败: {response.status_code} - {response.text}"
            
    except Exception as e:
        return None, f"❌ 合成失败: {str(e)}"


if __name__ == '__main__':
    mp.set_start_method('spawn', force=True)
    mp_manager = mp.Manager()

    devices = os.environ.get('CUDA_VISIBLE_DEVICES', '')
    if devices != '':
        devices = os.environ.get('CUDA_VISIBLE_DEVICES', '').split(",")
    else:
        devices = None
    
    num_workers = 1
    input_queue = mp_manager.Queue()
    output_queue = mp_manager.Queue()
    processes = []

    print("Start open workers")
    
    # 创建界面（先不启动模型worker）
    with gr.Blocks(
        title="MegaTTS3 语音合成平台",
        theme=gr.themes.Soft(),  # 使用内置主题避免外部CSS
        css=".gradio-container { max-width: 1200px; margin: auto; }"  # 内联CSS
    ) as app:
        gr.Markdown("# 🎤 MegaTTS3 语音合成平台")
        gr.Markdown("基于API接口的语音合成 - **推荐使用**")
        
        with gr.Tabs():
            # API Demo作为主要标签页（默认选中）
            with gr.TabItem("🔌 API合成 (推荐)", id="api_demo"):
                gr.Markdown("### 通过REST API接口进行语音合成")
                gr.Markdown("**✅ 稳定可靠，推荐使用此方式**")
                gr.HTML(create_api_demo_html())
                
                # API Demo的Gradio组件
                with gr.Row():
                    with gr.Column():
                        api_audio = gr.Audio(type="filepath", label="📂 上传参考音频文件 (.wav)")
                        api_latent = gr.File(type="filepath", label="🗂️ 上传Latent文件 (.npy)")
                        api_text = gr.Textbox(label="📝 输入合成文本", placeholder="请输入需要合成的文本内容...", lines=3)
                        
                    with gr.Column():
                        api_timestep = gr.Number(label="推理步数", value=32, minimum=1, maximum=100)
                        api_p_w = gr.Number(label="清晰度权重", value=1.4, minimum=0, maximum=5, step=0.1)
                        api_t_w = gr.Number(label="相似度权重", value=3.0, minimum=0, maximum=5, step=0.1)
                
                api_synthesize_btn = gr.Button("🎵 开始API合成", variant="primary", size="lg")
                api_status = gr.Textbox(label="状态", interactive=False)
                api_output = gr.Audio(label="合成结果")
                
                # 绑定API合成事件
                api_synthesize_btn.click(
                    fn=api_synthesize,
                    inputs=[api_audio, api_latent, api_text, api_timestep, api_p_w, api_t_w],
                    outputs=[api_output, api_status]
                )
            
            # 原生WebUI作为备选标签页
            with gr.TabItem("🎯 原生模式 (实验性)", id="native_ui"):
                gr.Markdown("### 直接使用MegaTTS3模型进行语音合成")
                gr.Markdown("**⚠️ 模型加载较慢，如无响应请使用API模式**")
                
                # 添加启动模型的按钮
                start_model_btn = gr.Button("🚀 启动原生模型 (首次点击需等待2-3分钟)", variant="secondary")
                model_status = gr.Markdown("**状态**: 模型未启动")
                
                with gr.Row():
                    with gr.Column():
                        inp_audio = gr.Audio(type="filepath", label="Upload .wav")
                        inp_npy = gr.File(type="filepath", label="Upload .npy")
                        inp_text = gr.Textbox(label="Input Text")
                        
                    with gr.Column():
                        infer_timestep = gr.Number(label="infer timestep", value=32)
                        p_w = gr.Number(label="Intelligibility Weight", value=1.4)
                        t_w = gr.Number(label="Similarity Weight", value=3.0)
                
                output_audio = gr.Audio(label="Synthesized Audio")
                synthesize_btn = gr.Button("🎵 开始合成", variant="primary", interactive=False)
                
                # 延迟加载模型的函数
                def start_model():
                    try:
                        # 这里启动模型worker
                        for i in range(num_workers):
                            p = mp.Process(target=model_worker, args=(input_queue, output_queue, i % len(devices) if devices is not None else None))
                            p.start()
                            processes.append(p)
                        return "**状态**: ✅ 模型已启动，可以开始合成", gr.update(interactive=True)
                    except Exception as e:
                        return f"**状态**: ❌ 模型启动失败: {str(e)}", gr.update(interactive=False)
                
                # 绑定按钮事件
                start_model_btn.click(
                    fn=start_model,
                    outputs=[model_status, synthesize_btn]
                )
                
                synthesize_btn.click(
                    fn=partial(main, processes=processes, input_queue=input_queue, output_queue=output_queue),
                    inputs=[inp_audio, inp_npy, inp_text, infer_timestep, p_w, t_w],
                    outputs=output_audio
                )
    
    # 先启动Gradio界面，不加载模型
    app.launch(
        server_name='0.0.0.0', 
        server_port=7929, 
        debug=True,
        share=False,  # 禁用huggingface.co连接
        show_tips=False,  # 禁用提示
        enable_queue=True,  # 启用队列
        favicon_path=None,  # 禁用favicon
        app_kwargs={
            "docs_url": None,  # 禁用docs
            "redoc_url": None,  # 禁用redoc
        }
    )
