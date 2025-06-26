import gradio as gr
import argparse

def test_function(text):
    return f"您输入了: {text}"

# 启动应用
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--server_port', type=int, default=8889, help='Server port')
    parser.add_argument('--server_name', default="127.0.0.1", help='Server name')
    args = parser.parse_args()
    
    # 创建简单的Gradio界面
    demo = gr.Interface(
        fn=test_function,
        inputs=gr.Textbox(label="测试输入", placeholder="输入一些文字..."),
        outputs=gr.Textbox(label="输出结果"),
        title="简单测试页面",
        description="测试Gradio是否能正常工作"
    )
    
    print(f"正在启动测试应用，地址: http://{args.server_name}:{args.server_port}")
    try:
        demo.launch(
            server_name=args.server_name, 
            server_port=args.server_port,
            share=False,
            debug=True,
            prevent_thread_lock=False
        )
    except Exception as e:
        print(f"启动失败: {e}")
        print("尝试不同的配置...")
        demo.launch(
            server_name="0.0.0.0", 
            server_port=args.server_port,
            share=False
        ) 