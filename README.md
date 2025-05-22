# AI-Sound TTS系统

一个基于MegaTTS3的文本转语音系统，支持多种声音和情感表达。

## 项目介绍

AI-Sound TTS系统是一个灵活、高性能的文本转语音解决方案，可以生成自然流畅的语音输出。系统支持多种声音ID和情感类型，可以满足不同场景的语音合成需求。

### 主要功能

- 多种声音ID支持（如范闲、周杰伦、各种男声/女声等）
- 多种情感类型（如中性、开心、悲伤、愤怒、惊讶等）
- 音高、速度、能量等参数调整
- 声音特征提取和应用
- API服务接口
- 批量处理能力

## 项目结构

```
AI-Sound/
├── services/                  # 核心服务
│   └── api/                   # API服务
│       └── src/
│           └── tts/           # TTS核心模块
│               ├── engine.py  # TTS引擎实现
│               └── mock_infer.py # 模拟推理模块
├── MegaTTS3/                  # MegaTTS3模型库
├── data/                      # 数据目录
│   └── checkpoints/           # 模型检查点
│       ├── wavvae/            # WavVAE模型
│       ├── duration_lm/       # 持续时间语言模型
│       └── voice_samples/     # 声音样本
├── tools/                     # 工具脚本
├── test_*.py                  # 测试脚本
├── start_api_server.py        # API服务启动脚本
├── analyze_voice_features.py  # 声音特征分析工具
├── test_voice_compare.py      # 声音对比测试工具
├── test_config.json           # 测试配置文件
└── README.md                  # 项目文档
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动API服务

```bash
python start_api_server.py
```

服务将在 http://127.0.0.1:9970 上启动，可以通过 http://127.0.0.1:9970/api/tts/text 访问TTS功能。

## 工具和脚本

### 1. 启动API服务

```bash
python start_api_server.py
```

跨平台启动API服务的脚本，自动处理路径和进程管理。

### 2. 声音特征分析工具

```bash
python analyze_voice_features.py --input <文件或目录路径> --output <输出目录>
```

分析声音特征文件（NPY格式）或音频文件（WAV/MP3等），生成可视化报告。

参数:
- `--input`, `-i`: 输入文件或目录路径（必需）
- `--output`, `-o`: 输出目录（默认：voice_analysis_output）
- `--sample-name`, `-n`: 样本名称前缀（仅适用于单个文件分析）

### 3. 声音对比测试工具

```bash
python test_voice_compare.py --config test_config.json --output voice_compare_output --parallel
```

生成不同声音ID和情感类型的音频样本，并生成对比报告。

参数:
- `--config`, `-c`: 测试配置JSON文件
- `--output`, `-o`: 输出目录（默认：voice_compare_output）
- `--parallel`, `-p`: 使用并行处理加速生成
- `--clean`: 清空输出目录

### 4. 直接TTS测试

```bash
python test_direct_tts.py
```

直接测试TTS引擎功能，不通过API服务。

### 5. 情感TTS测试

```bash
python test_emotion_tts.py
```

测试不同情感类型和声音ID的语音合成效果。

## 配置文件

### test_config.json

声音对比测试工具的配置文件，示例：

```json
{
  "texts": [
    "这是一段测试文本，用于测试不同声音和情感的语音合成效果。",
    "人工智能语音合成技术可以模拟不同说话人的声音特征，生成自然流畅的语音。"
  ],
  "voices": [
    "范闲",
    "周杰伦",
    "female_young"
  ],
  "emotions": [
    {"type": "neutral", "intensity": 0.5},
    {"type": "happy", "intensity": 0.8},
    {"type": "sad", "intensity": 0.7}
  ]
}
```

## 声音样本

系统支持以下声音ID：

1. 扩展声音样本：
   - `范闲`: 男声，低沉
   - `周杰伦`: 男声，特色音色
   - `english_talk`: 英文说话声音

2. 基础声音：
   - `female_young`: 年轻女声
   - `female_mature`: 成熟女声
   - `male_young`: 年轻男声
   - `male_middle`: 中年男声
   - `male_mature`: 成熟男声

## 情感类型

系统支持以下情感类型：

- `neutral`: 中性语气
- `happy`: 开心语气
- `sad`: 悲伤语气
- `angry`: 愤怒语气
- `surprise`: 惊讶语气（或使用`surprised`）
- `fear`: 恐惧语气

每种情感都可以通过0.0-1.0的强度参数进行调整。

## API接口

### 文本转语音

```
GET /api/tts/text?text=你好世界&voice_id=female_young&emotion_type=happy&emotion_intensity=0.8
```

参数:
- `text`: 要转换为语音的文本
- `voice_id`: 声音ID（可选，默认为female_young）
- `emotion_type`: 情感类型（可选，默认为neutral）
- `emotion_intensity`: 情感强度0.0-1.0（可选，默认为0.5）
- `speed_scale`: 速度缩放（可选，默认为1.0）
- `pitch_scale`: 音高缩放（可选，默认为1.0）
- `energy_scale`: 能量缩放（可选，默认为1.0）

返回：WAV格式的音频数据

## 性能优化

对于生产环境，建议：

1. 使用并行处理进行批量生成
2. 根据实际需求调整batch_size
3. 对于频繁使用的文本考虑启用缓存机制
4. 如果有GPU资源，启用GPU加速

## 问题排查

如果遇到问题，可以尝试：

1. 检查日志文件查看详细错误信息
2. 使用`test_direct_tts.py`直接测试TTS引擎
3. 使用`check_npy_shape.py`检查声音特征文件格式
4. 使用`analyze_voice_features.py`分析声音特征

## 扩展声音库

要添加新的声音ID，您需要：

1. 准备一个清晰的语音样本WAV文件
2. 使用MegaTTS3工具提取声音特征（NPY文件）
3. 将NPY文件和WAV文件放入`data/checkpoints/voice_samples/`目录
4. 在`engine.py`中的`voice_samples`字典中添加新的声音ID配置

## 许可证

本项目遵循MIT许可证。详情请参阅LICENSE文件。

## 致谢

本项目基于MegaTTS3模型开发，感谢所有开源贡献者的工作。