# MegaTTS3 语音合成服务

AI-Sound项目的语音合成引擎，基于MegaTTS3模型提供高质量的语音合成服务。

## 🚀 快速启动

### 标准启动
```bash
python start_megatts3.py
```

### 自定义端口启动
```bash
python start_megatts3.py --port 8000 --host 127.0.0.1
```

## 📋 服务信息

- **默认端口**: 7929
- **默认地址**: 0.0.0.0
- **服务名称**: MegaTTS3 API (Fixed FFmpeg)
- **GPU支持**: CUDA 12.1 (RTX 4090)

## 🔧 API接口

### 健康检查
```http
GET /health
```

### 服务信息
```http
GET /api/v1/info
```

### 语音合成
```http
POST /api/v1/tts/synthesize
Content-Type: multipart/form-data

参数:
- audio_file: 参考音频文件 (.wav)
- text: 要合成的文本
- latent_file: Latent文件 (.npy) [可选]
- time_step: 推理步数 [默认: 32]
- p_w: 智能度权重 [默认: 1.4]
- t_w: 相似度权重 [默认: 3.0]
```

## 📁 文件结构

```
MegaTTS/espnet/
├── start_megatts3.py          # 标准化启动脚本
├── megatts3_api_server.py     # API服务器
├── checkpoints/               # 模型文件
│   ├── wavvae/               # WaveVAE模型
│   ├── duration_lm/          # 时长模型
│   ├── diffusion_transformer/ # 扩散变换器
│   └── aligner_lm/           # 对齐模型
├── tts/                      # TTS核心代码
└── README.md                 # 本文档
```

## 🔧 依赖要求

- Python 3.11+
- PyTorch (CUDA 12.1)
- Flask
- Flask-CORS
- pydub
- numpy
- soundfile
- FFmpeg

## 🛠️ 故障排除

### FFmpeg问题
如果遇到FFmpeg相关错误，确保：
1. FFmpeg已正确安装
2. 路径配置正确
3. pydub能找到ffprobe

### GPU问题
如果GPU不可用：
1. 检查CUDA安装
2. 检查PyTorch CUDA版本
3. 检查GPU驱动

### 模型加载问题
如果模型加载失败：
1. 检查checkpoints目录
2. 检查模型文件完整性
3. 检查内存和显存

## 📝 使用示例

### Python客户端示例
```python
import requests

# 语音合成
files = {
    'audio_file': open('reference.wav', 'rb'),
    'latent_file': open('reference.npy', 'rb')  # 可选
}
data = {
    'text': '你好，这是一个测试。',
    'time_step': 32,
    'p_w': 1.4,
    't_w': 3.0
}

response = requests.post(
    'http://localhost:7929/api/v1/tts/synthesize',
    files=files,
    data=data
)

if response.status_code == 200:
    with open('output.wav', 'wb') as f:
        f.write(response.content)
    print("语音合成成功！")
else:
    print(f"错误: {response.json()}")
```

## 🔄 服务管理

### 启动服务
```bash
python start_megatts3.py
```

### 停止服务
按 `Ctrl+C` 优雅关闭

### 后台运行
```bash
nohup python start_megatts3.py > megatts3.log 2>&1 &
```

## 📊 性能指标

- **模型加载时间**: ~30秒
- **单次合成时间**: ~5-10秒
- **内存占用**: ~8GB
- **显存占用**: ~6GB

## 🤝 集成说明

本服务已集成到AI-Sound项目中，作为语音合成引擎使用。服务启动后，AI-Sound后端会自动检测并连接到该服务。

## 📄 许可证

遵循MegaTTS3项目的原始许可证。
