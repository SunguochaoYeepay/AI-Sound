# MegaTTS3 语音合成服务部署指南

本文档介绍如何部署和使用MegaTTS3语音合成服务。

## 1. 系统要求

- Docker Engine 20.10+
- Docker Compose 2.0+
- 至少4GB可用内存
- 可选: NVIDIA GPU + CUDA 11.7或更高版本

## 2. 目录结构

```
AI-Sound/
├── MegaTTS3/               # MegaTTS3源代码
├── data/
│   ├── checkpoints/        # 模型文件目录
│   └── output/             # 输出音频文件目录
├── docker/
│   └── tts/                # TTS服务容器相关文件
├── services/
│   └── api/                # API服务代码
├── docker-compose.tts.yml  # Docker Compose配置
└── start-tts-service.bat   # Windows启动脚本
```

## 3. 部署步骤

### 3.1 准备模型文件

将MegaTTS3模型文件(`megatts3_base.pth`)放置在`data/checkpoints/`目录下。如果没有模型文件，系统将使用增强版模拟引擎。

### 3.2 Windows系统部署

在Windows系统下，直接双击运行`start-tts-service.bat`文件启动服务。

### 3.3 Linux/MacOS系统部署

在Linux或MacOS系统下，运行以下命令启动服务:

```bash
# 给脚本添加执行权限
chmod +x docker/tts/build_tts.sh

# 运行部署脚本
./docker/tts/build_tts.sh
```

### 3.4 验证服务

部署完成后，服务将在`http://localhost:9930`上运行。可以使用以下命令查看服务日志:

```bash
docker-compose -f docker-compose.tts.yml logs -f
```

## 4. 使用方法

### 4.1 API接口

TTS服务提供以下API:

- `POST /api/tts`: 文本转语音
  - 请求参数:
    - `text`: 要转换的文本
    - `speaker_id`: 说话人ID (可选，默认为0)
  - 返回:
    - 生成的WAV音频文件

### 4.2 测试脚本

使用提供的测试脚本测试TTS服务:

```bash
python test-tts-api.py --text "你好，这是一个测试" --play
```

参数说明:
- `--text`, `-t`: 要转换的文本
- `--url`, `-u`: API端点URL，默认为`http://localhost:9930/api/tts`
- `--speaker`, `-s`: 说话人ID，默认为0
- `--output`, `-o`: 输出目录，默认为`output`
- `--play`, `-p`: 生成后自动播放

### 4.3 批量测试

使用以下命令测试多个预设文本:

```bash
python test-tts-api.py --text 测试 --play
```

## 5. 音色选择

当前版本支持以下音色ID:

- `0`: 默认音色
- `1`: 女声
- `2`: 男声
- `3`: 中性偏女声
- `4`: 中性偏男声

## 6. 常见问题

### 6.1 服务无法启动

检查Docker是否正常运行:

```bash
docker info
```

确保端口9930未被占用:

```bash
# Windows
netstat -ano | findstr 9930

# Linux/MacOS
netstat -tuln | grep 9930
```

### 6.2 生成的音频是噪音

如果生成的音频是噪音，可能原因:

1. MegaTTS3模型文件缺失或损坏
2. 模型加载失败，系统回退到模拟模式但配置不正确

解决方法:
- 检查模型文件是否存在
- 查看服务日志确认问题

### 6.3 GPU加速不生效

确保:
1. 已安装NVIDIA驱动和CUDA
2. Docker已配置NVIDIA容器工具包
3. `nvidia-smi`命令能正常运行

## 7. 高级定制

### 7.1 调整模拟引擎参数

可以编辑`services/api/src/tts/mock_infer.py`文件，调整以下参数:
- 音素特征
- 共振峰频率
- 说话人ID对应的音高偏移

### 7.2 Docker配置调整

编辑`docker-compose.tts.yml`文件，可以修改:
- 端口映射
- 资源限制
- 环境变量

## 8. 许可说明

本项目使用内部开发的MegaTTS3模型，仅供研究和内部使用。 