#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MegaTTS3 WebUI应用 - 微服务版本
基于原始gradio_api.py的微服务架构适配版本
"""

import gradio as gr
import requests
import os
import tempfile
import traceback

def create_api_demo_html():
    """创建API Demo的HTML内容"""
    html_content = """
    <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
        <h2>🔌 MegaTTS3 API Demo</h2>
        <p>基于微服务API接口的语音合成测试 - 验证与WebUI功能一致性</p>
        
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3>📋 使用说明</h3>
            <p>1. 上传参考音频文件 (.wav)</p>
            <p>2. 上传对应的Latent文件 (.npy, 可选)</p>
            <p>3. 输入要合成的文本</p>
            <p>4. 调整参数后点击合成</p>
        </div>
        
        <div style="background: #e7f3ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3>✅ 微服务架构优势</h3>
            <p>• 稳定可靠的API接口调用</p>
            <p>• 服务独立部署和扩展</p>
            <p>• 统一网关访问入口</p>
            <p>• 便于集成到其他应用中</p>
        </div>
    </div>
    """
    return html_content

def api_synthesize(audio_file, latent_file, text, time_step, p_w, t_w):
    """通过微服务API接口进行语音合成"""
    if not audio_file or not text.strip():
        return None, "❌ 请至少上传音频文件并输入文本！"
    
    try:
        # 获取API URL
        api_url = os.getenv('MEGATTS3_API_URL', 'http://localhost:8001')
        
        # 准备文件上传
        files = {
            'audio_file': open(audio_file, 'rb')
        }
        
        # 如果有latent文件，也上传
        if latent_file:
            files['latent_file'] = open(latent_file, 'rb')
        
        data = {
            'text': text,
            'time_step': int(time_step),
            'p_w': float(p_w),
            't_w': float(t_w)
        }
        
        print(f"正在调用API: {api_url}/api/v1/synthesize_file")
        print(f"参数: {data}")
        
        # 调用API
        response = requests.post(
            f'{api_url}/api/v1/synthesize_file',
            files=files,
            data=data,
            timeout=120
        )
        
        # 关闭文件
        files['audio_file'].close()
        if latent_file and 'latent_file' in files:
            files['latent_file'].close()
        
        if response.status_code == 200:
            # 保存返回的音频文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_file.write(response.content)
                return tmp_file.name, f"✅ 合成成功！音频长度: {len(response.content)} 字节"
        else:
            return None, f"❌ API调用失败: {response.status_code} - {response.text}"
            
    except Exception as e:
        error_msg = f"❌ 合成失败: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        return None, error_msg

def check_api_status():
    """检查API服务状态"""
    try:
        api_url = os.getenv('MEGATTS3_API_URL', 'http://localhost:8001')
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            model_status = "✅ 已加载" if data.get('model_loaded', False) else "❌ 未加载"
            return f"✅ API正常 - {data.get('service', 'unknown')} v{data.get('version', '0.0.0')} | 模型状态: {model_status}"
        else:
            return f"❌ API异常 - HTTP {response.status_code}"
    except Exception as e:
        return f"❌ 无法连接API - {str(e)}"

def get_model_info():
    """获取模型信息"""
    try:
        api_url = os.getenv('MEGATTS3_API_URL', 'http://localhost:8001')
        response = requests.get(f"{api_url}/api/v1/models", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = ", ".join(data.get('models', []))
            current = data.get('current_model', 'N/A')
            return f"可用模型: {models} | 当前模型: {current}"
        else:
            return "无法获取模型信息"
    except Exception as e:
        return f"获取失败: {str(e)}"

def create_interface():
    """创建Gradio界面"""
    
    with gr.Blocks(
        title="MegaTTS3 WebUI - 微服务版本",
        theme=gr.themes.Soft(),
        css=".gradio-container { max-width: 1200px; margin: auto; }"
    ) as demo:
        gr.Markdown("# 🎵 MegaTTS3 Text-to-Speech 微服务版本")
        gr.Markdown("## 基于微服务架构的语音合成平台")
        
        # 状态信息栏
        with gr.Row():
            with gr.Column(scale=2):
                status_text = gr.Textbox(
                    label="📊 API服务状态",
                    value="等待检查...",
                    interactive=False,
                    max_lines=1
                )
            with gr.Column(scale=2):
                model_text = gr.Textbox(
                    label="🤖 模型信息",
                    value="等待检查...",
                    interactive=False,
                    max_lines=1
                )
            with gr.Column(scale=1):
                check_status_btn = gr.Button("🔍 检查状态", variant="secondary")
        
        gr.HTML(create_api_demo_html())
        
        # 主要功能区域
        with gr.Row():
            with gr.Column():
                audio_input = gr.Audio(
                    type="filepath", 
                    label="📂 上传参考音频文件 (.wav)",
                    info="上传一个参考音频文件，用于声音克隆"
                )
                
                latent_input = gr.File(
                    type="filepath",
                    label="🗂️ 上传Latent文件 (.npy, 可选)",
                    info="如果有预计算的latent文件可以上传，否则会自动计算"
                )
                
                text_input = gr.Textbox(
                    label="📝 输入合成文本",
                    placeholder="请输入需要合成的文本内容...",
                    lines=4,
                    info="输入你想要合成的文本内容"
                )
            
            with gr.Column():
                time_step = gr.Number(
                    label="🎛️ 推理步数 (time_step)",
                    value=32,
                    minimum=1,
                    maximum=100,
                    step=1,
                    info="推理步数，越大质量越好但速度越慢"
                )
                
                p_w = gr.Number(
                    label="🎚️ 智能度权重 (p_w)",
                    value=1.4,
                    minimum=0,
                    maximum=5,
                    step=0.1,
                    info="控制语音的智能程度"
                )
                
                t_w = gr.Number(
                    label="🎚️ 相似度权重 (t_w)",
                    value=3.0,
                    minimum=0,
                    maximum=5,
                    step=0.1,
                    info="控制与参考音频的相似度"
                )
        
        # 合成按钮
        synthesize_btn = gr.Button(
            "🎵 开始语音合成",
            variant="primary",
            size="lg"
        )
        
        # 输出区域
        with gr.Row():
            with gr.Column():
                output_text = gr.Textbox(
                    label="📋 合成状态",
                    lines=3,
                    interactive=False
                )
            
            with gr.Column():
                output_audio = gr.Audio(
                    label="🎧 合成结果",
                    type="filepath"
                )
        
        # 事件绑定
        synthesize_btn.click(
            fn=api_synthesize,
            inputs=[audio_input, latent_input, text_input, time_step, p_w, t_w],
            outputs=[output_audio, output_text]
        )
        
        def check_both_status():
            api_status = check_api_status()
            model_info = get_model_info()
            return api_status, model_info
        
        check_status_btn.click(
            fn=check_both_status,
            outputs=[status_text, model_text]
        )
        
        # 页面加载时自动检查状态
        demo.load(
            fn=check_both_status,
            outputs=[status_text, model_text]
        )
    
    return demo

if __name__ == "__main__":
    host = os.getenv('GRADIO_SERVER_NAME', '0.0.0.0')
    port = int(os.getenv('GRADIO_SERVER_PORT', 8002))
    
    print(f"🚀 启动MegaTTS3 WebUI (微服务版本)...")
    print(f"📍 地址: http://{host}:{port}")
    print(f"🔗 API连接: {os.getenv('MEGATTS3_API_URL', 'http://localhost:8001')}")
    
    demo = create_interface()
    demo.launch(
        server_name=host,
        server_port=port,
        share=False,
        show_api=False
    ) 