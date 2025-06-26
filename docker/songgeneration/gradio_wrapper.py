#!/usr/bin/env python3
"""
SongGeneration官方Gradio界面启动包装脚本
解决端口、路径和依赖问题
"""
import sys
import os
import subprocess

def main():
    # 设置工作目录
    work_dir = "/workspace/SongGeneration"
    gradio_dir = "/workspace/SongGeneration/tools/gradio"
    ckpt_dir = "/workspace/SongGeneration/ckpt"
    
    print("🎨 启动SongGeneration官方Gradio界面...")
    print(f"📁 工作目录: {work_dir}")
    print(f"🎨 Gradio目录: {gradio_dir}")
    print(f"🤖 模型目录: {ckpt_dir}")
    
    # 检查必要文件
    app_py = os.path.join(gradio_dir, "app.py")
    if not os.path.exists(app_py):
        print(f"❌ Gradio应用文件不存在: {app_py}")
        return 1
    
    if not os.path.exists(ckpt_dir):
        print(f"❌ 模型目录不存在: {ckpt_dir}")
        return 1
    
    # 检查关键依赖
    try:
        import gradio
        print(f"✅ Gradio版本: {gradio.__version__}")
    except ImportError:
        print("❌ Gradio未安装")
        return 1
    
    try:
        import yaml
        print("✅ YAML支持正常")
    except ImportError:
        print("❌ PyYAML未安装")
        return 1
    
    # 切换到Gradio目录
    os.chdir(gradio_dir)
    print(f"📍 切换到目录: {os.getcwd()}")
    
    # 修改官方app.py的启动参数
    print("🔧 修复启动配置...")
    
    # 读取原始app.py
    with open("app.py", "r", encoding="utf-8") as f:
        app_content = f.read()
    
    # 修复端口配置
    app_content = app_content.replace(
        'demo.launch(server_name="0.0.0.0", server_port=8081)',
        'demo.launch(server_name="0.0.0.0", server_port=7862, share=False)'
    )
    
    # 写入修复后的文件
    with open("app_fixed.py", "w", encoding="utf-8") as f:
        f.write(app_content)
    
    print("✅ 配置修复完成")
    
    # 启动Gradio界面
    print("🚀 启动Gradio界面 (端口7862)...")
    try:
        # 传入ckpt目录作为参数
        cmd = [sys.executable, "app_fixed.py", ckpt_dir]
        print(f"🔧 执行命令: {' '.join(cmd)}")
        
        # 启动进程
        process = subprocess.run(cmd, cwd=gradio_dir)
        return process.returncode
        
    except KeyboardInterrupt:
        print("\n🛑 Gradio界面已停止")
        return 0
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 