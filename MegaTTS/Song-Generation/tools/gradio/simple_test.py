import gradio as gr
import argparse

def test_function(text):
    return f"您输入了: {text}"

# 创建简单的Gradio界面
with gr.Blocks(title="Simple Test") as demo:
    gr.Markdown("# 简单测试页面")
    
    with gr.Row():
        with gr.Column():
            input_text = gr.Textbox(
                label="测试输入",
                placeholder="输入一些文字...",
                lines=3
            )
            test_btn = gr.Button("测试", variant="primary")
        
        with gr.Column():
            output_text = gr.Textbox(label="输出结果")
    
    # 按钮点击事件
    test_btn.click(
        fn=test_function,
        inputs=[input_text],
        outputs=[output_text]
    )

# 启动应用
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--server_port', type=int, default=8888, help='Server port')
    parser.add_argument('--server_name', default="127.0.0.1", help='Server name')
    args = parser.parse_args()
    
    print(f"正在启动测试应用，地址: http://{args.server_name}:{args.server_port}")
    demo.launch(server_name=args.server_name, server_port=args.server_port) 