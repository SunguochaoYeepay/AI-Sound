#!/bin/bash

# SongGeneration服务启动脚本
set -e

echo "🎵 SongGeneration本地模型服务启动中..."

# 🔑 在最开始就设置Python模块路径！
export PYTHONPATH="/workspace/SongGeneration:/workspace:$PYTHONPATH"
echo "🐍 设置Python路径: $PYTHONPATH"

# 检查必要的目录
echo "📁 检查目录结构..."
mkdir -p /workspace/output /workspace/temp /workspace/logs

# 检查本地模型是否存在（核心功能）
echo "🤖 检查SongGeneration本地模型..."

# 检查直接的模型文件（通过volume挂载）
CKPT_DIR="/workspace/SongGeneration/ckpt"
if [ -d "$CKPT_DIR" ]; then
    echo "✅ 模型目录已挂载: $CKPT_DIR"
    
    # 检查关键模型文件
    if [ -f "$CKPT_DIR/encode-s12k.pt" ]; then
        echo "✅ 编码器模型存在: encode-s12k.pt ($(du -h $CKPT_DIR/encode-s12k.pt | cut -f1))"
    else
        echo "⚠️  编码器模型缺失: encode-s12k.pt"
    fi
    
    if [ -d "$CKPT_DIR/songgeneration_base" ]; then
        echo "✅ 主生成模型存在: songgeneration_base/"
    else
        echo "⚠️  主生成模型缺失: songgeneration_base/"
    fi
    
    if [ -d "$CKPT_DIR/vae" ]; then
        echo "✅ VAE模型存在: vae/"
    else
        echo "⚠️  VAE模型缺失: vae/"
    fi
    
    if [ -d "$CKPT_DIR/models--tencent--SongGeneration" ]; then
        echo "✅ 腾讯SongGeneration模型存在"
    else
        echo "⚠️  腾讯SongGeneration模型缺失"
    fi
    
    # 显示模型目录大小
    CKPT_SIZE=$(du -sh "$CKPT_DIR" 2>/dev/null | cut -f1)
    echo "📊 模型目录总大小: $CKPT_SIZE"
    
else
    echo "❌ 模型目录不存在: $CKPT_DIR"
    echo "   请确保Docker volume挂载配置正确"
fi

# 检查核心生成脚本
echo "📜 检查生成脚本..."
if [ -f "/workspace/SongGeneration/generate_lowmem.py" ]; then
    echo "✅ 低显存生成脚本存在"
else
    echo "❌ 低显存生成脚本缺失: generate_lowmem.py"
fi

if [ -f "/workspace/SongGeneration/generate.py" ]; then
    echo "✅ 标准生成脚本存在"
else
    echo "❌ 标准生成脚本缺失: generate.py"
fi

# 检查codeclm模块
echo "🧩 检查SongGeneration核心模块..."
if [ -d "/workspace/SongGeneration/codeclm" ]; then
    echo "✅ CodeCLM模块目录存在"
    # 测试模块是否可以导入
    cd /workspace/SongGeneration
    if python -c "import codeclm" 2>/dev/null; then
        echo "✅ CodeCLM模块可以正常导入"
    else
        echo "⚠️  CodeCLM模块存在但无法导入，可能缺少__init__.py文件"
        # 确保所有子模块都有__init__.py
        for subdir in codeclm codeclm/models codeclm/modules codeclm/tokenizer codeclm/trainer codeclm/utils; do
            if [ -d "/workspace/SongGeneration/$subdir" ] && [ ! -f "/workspace/SongGeneration/$subdir/__init__.py" ]; then
                echo "# Package initialization" > "/workspace/SongGeneration/$subdir/__init__.py"
                echo "✅ 已创建 $subdir/__init__.py"
            fi
        done
        
        # 确保models模块正确导入类
        cat > "/workspace/SongGeneration/codeclm/models/__init__.py" << 'EOF'
# Package initialization
from .codeclm import CodecLM
from .levo import CausalLM

__all__ = ["CodecLM", "CausalLM"]
EOF
        
        # 确保trainer模块正确导入类
        cat > "/workspace/SongGeneration/codeclm/trainer/__init__.py" << 'EOF'
# Package initialization
from .codec_song_pl import CodecLM_PL

__all__ = ["CodecLM_PL"]
EOF
    fi
else
    echo "❌ CodeCLM模块缺失: codeclm/"
fi

# 检查Python依赖
echo "🐍 检查Python依赖..."
python -c "
import sys
try:
    import fastapi, uvicorn, httpx, pydantic
    print('✅ 核心API依赖检查通过')
except ImportError as e:
    print(f'❌ API依赖检查失败: {e}')
    sys.exit(1)

try:
    import torch, transformers, lightning
    print('✅ AI模型依赖检查通过')
except ImportError as e:
    print(f'❌ AI模型依赖检查失败: {e}')
    sys.exit(1)
"

# 检查音频处理依赖
echo "🎵 检查音频处理依赖..."
python -c "
try:
    import librosa, soundfile
    print('✅ 音频处理依赖检查通过')
except ImportError:
    print('⚠️  音频处理库未安装，将使用FFmpeg备选方案')
"

# 检查FFmpeg
echo "🔧 检查FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg可用"
else
    echo "❌ FFmpeg不可用，音频处理可能失败"
fi

# 设置权限
echo "🔐 设置文件权限..."
chown -R appuser:appuser /workspace/output /workspace/temp /workspace/logs 2>/dev/null || true

echo "🚀 启动SongGeneration本地模型服务..."

# 测试codeclm模块导入
echo "🧪 测试模块导入..."
cd /workspace/SongGeneration
python -c "
import sys
sys.path.insert(0, '/workspace/SongGeneration')
sys.path.insert(0, '/workspace')
try:
    import codeclm
    print('✅ codeclm模块导入成功')
except ImportError as e:
    print(f'❌ codeclm模块导入失败: {e}')
    print('📁 当前目录:', __import__('os').getcwd())
    print('📁 Python路径:', sys.path[:5])
    import os
    if os.path.exists('/workspace/SongGeneration/codeclm'):
        print('✅ codeclm目录存在')
        if os.path.exists('/workspace/SongGeneration/codeclm/__init__.py'):
            print('✅ __init__.py文件存在')
        else:
            print('❌ __init__.py文件缺失')
            # 创建__init__.py文件
            with open('/workspace/SongGeneration/codeclm/__init__.py', 'w') as f:
                f.write('# CodecLM module\\n')
            print('✅ 已创建__init__.py文件')
    else:
        print('❌ codeclm目录不存在')
"

# 如果没有指定命令，使用默认启动方式
if [ $# -eq 0 ]; then
    echo "🚀 启动模式选择..."
    
    # 查找实际的工作目录和模型路径
    echo "🔍 搜索实际的模型目录..."
    find /workspace -name "*.pt" -o -name "*.ckpt" -o -name "*.safetensors" 2>/dev/null | head -5
    
    if [ -d "/workspace/SongGeneration" ]; then
        cd /workspace/SongGeneration
        echo "✅ 切换到 /workspace/SongGeneration 目录"
    elif [ -d "/workspace" ]; then
        cd /workspace
        echo "✅ 切换到 /workspace 目录"
    else
        echo "⚠️ 使用当前目录: $(pwd)"
    fi
    
    # 检查是否有官方Gradio界面
    if [ -f "/workspace/SongGeneration/tools/gradio/app_fixed.py" ]; then
        echo "🎨 发现官方Gradio界面，启动双服务模式..."
        
        # 启动API服务 (后台)
        echo "📡 启动API服务 (端口7863)..."
        python -c "
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import sys
import os

app = FastAPI(title='SongGeneration API + Gradio')

@app.get('/health')
def health():
    return {'status': 'healthy', 'service': 'SongGeneration', 'mode': 'api+gradio'}

@app.get('/test')
def test():
    return {
        'message': 'SongGeneration API + Gradio界面', 
        'paths': {
            'current': os.getcwd(),
            'ckpt_exists': os.path.exists('/workspace/SongGeneration/ckpt'),
            'tools_exists': os.path.exists('/workspace/SongGeneration/tools')
        },
        'services': {
            'api': 'http://localhost:7863',
            'gradio': 'http://localhost:7862'
        }
    }

@app.post('/generate')
def generate_mock(request: dict):
    return {'status': 'mock', 'message': 'Mock music generation', 'input': request}

print('🚀 SongGeneration API服务启动完成！')
print('📍 API健康检查: http://localhost:7863/health') 
print('🧪 API测试接口: http://localhost:7863/test')
print('📋 API文档: http://localhost:7863/docs')
print('🎨 Gradio界面: http://localhost:7862')
print('💡 现在同时提供API和Web界面服务')

uvicorn.run(app, host='0.0.0.0', port=7863, log_level='info')
" &
        API_PID=$!
        
        # 启动Gradio界面
        echo "🎵 启动官方Gradio界面 (端口7862)..."
        cd /workspace/SongGeneration/tools/gradio
        
        # 再次确认Python路径设置
        echo "🐍 确认Python路径设置..."
        echo "PYTHONPATH=$PYTHONPATH"
        
        # 启动Gradio界面，使用我们修复过的app_fixed.py
        echo "🎨 启动SongGeneration官方Gradio界面..."
        echo "📁 工作目录: $(pwd)"
        echo "🎨 Gradio目录: /workspace/SongGeneration/tools/gradio"
        echo "🤖 模型目录: /workspace/SongGeneration/ckpt"
        
        # 检查gradio版本
        python -c "import gradio; print(f'✅ Gradio版本: {gradio.__version__}')"
        
        # 检查yaml支持
        python -c "import yaml; print('✅ YAML支持正常')"
        
        echo "📍 切换到目录: $(pwd)"
        echo "🔧 修复启动配置..."
        
        # 确保日志目录存在
        mkdir -p /workspace/SongGeneration/logs
        
        echo "✅ 配置修复完成"
        echo "🚀 启动Gradio界面 (端口7862)..."
        echo "🔧 执行命令: /opt/conda/bin/python app_fixed.py /workspace/SongGeneration/ckpt"
        
        # 启动Gradio界面
        PYTHONPATH=/workspace/SongGeneration:/workspace /opt/conda/bin/python app_fixed.py /workspace/SongGeneration/ckpt &
        GRADIO_PID=$!
        
        # 等待两个服务
        wait $GRADIO_PID $API_PID
        
    else
        echo "🔧 使用纯API模式启动..."
        
        # 创建最简API服务器
        python -c "
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import sys
import os

app = FastAPI(title='SongGeneration Pure API')

@app.get('/health')
def health():
    return {'status': 'healthy', 'service': 'SongGeneration', 'mode': 'pure-api'}

@app.get('/test')
def test():
    return {'message': 'SongGeneration API is working', 'paths': {
        'current': os.getcwd(),
        'ckpt_exists': os.path.exists('/workspace/SongGeneration/ckpt'),
        'workspace_exists': os.path.exists('/workspace')
    }}

@app.post('/generate')
def generate_mock(request: dict):
    return {'status': 'mock', 'message': 'Mock music generation', 'input': request}

print('🚀 启动SongGeneration纯API服务...')
print('📍 健康检查: http://localhost:7863/health') 
print('🧪 测试接口: http://localhost:7863/test')
print('📋 API文档: http://localhost:7863/docs')

uvicorn.run(app, host='0.0.0.0', port=7863, log_level='info')
"
    fi
else
    # 执行传入的命令
    exec "$@"
fi 