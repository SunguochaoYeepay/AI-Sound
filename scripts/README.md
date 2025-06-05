# 🚀 Scripts 目录说明

AI-Sound项目的自动化脚本和工具集。

## 📁 目录结构

```
scripts/
├── deploy.sh                    # Linux/macOS自动化部署脚本
├── deploy.bat                   # Windows自动化部署脚本  
├── megatts3_health.sh          # MegaTTS3健康检查脚本
├── analysis/                    # 语音分析工具集
│   ├── analyze_voice_features.py   # 语音特征分析工具
│   ├── check_npy_shape.py          # NPY文件格式检查
│   └── check_model_load.py         # 模型加载测试
└── README.md                    # 本文档
```

## 🛠️ 部署脚本

### 自动化部署
**一键部署生产环境：**
```bash
# Linux/macOS
./scripts/deploy.sh

# Windows
.\scripts\deploy.bat
```

**开发环境部署：**
```bash
# 使用开发模式（热重载）
./scripts/deploy.sh dev

# 清理环境
./scripts/deploy.sh clean
```

**功能特性：**
- ✅ 系统要求检查（Docker、Node.js等）
- ✅ 自动创建数据目录结构
- ✅ 前端构建和部署
- ✅ Docker服务启动
- ✅ 健康检查和状态监控
- ✅ 错误处理和日志记录

### MegaTTS3健康检查
**全面的系统健康监控：**
```bash
./scripts/megatts3_health.sh
```

**检查项目：**
- 🔍 **服务状态检查** - 容器运行状态、HTTP服务响应
- 💾 **GPU状态检查** - GPU驱动、内存使用、温度监控
- 📊 **系统资源检查** - CPU、内存、磁盘使用情况
- 🌐 **网络连接检查** - 端口监听、API响应时间
- 🧠 **模型状态检查** - 模型加载状态、预测性能
- 📋 **日志分析** - 错误日志检测和分析

## 🔬 分析工具

### 语音特征分析
**全面的语音样本分析：**
```bash
python scripts/analysis/analyze_voice_features.py [文件路径或目录]
```

**功能特性：**
- 📈 **支持多种格式** - NPY特征文件、WAV/MP3音频文件
- 📊 **可视化分析** - 热图、统计图、趋势图、频谱图
- 📄 **HTML报告** - 自动生成完整的分析报告
- 🎯 **特征提取** - MFCC、梅尔频谱、色度特征等

**输出文件：**
- `*_heatmap.png` - 特征热图
- `*_stats.png` - 统计图表
- `*_trend.png` - 时间趋势图
- `*_melspectrogram.png` - 梅尔频谱图
- `analysis_report.html` - 完整分析报告

### NPY文件检查
**检查NPY特征文件格式：**
```bash
python scripts/analysis/check_npy_shape.py [NPY文件路径]
```

### 模型加载测试
**验证模型文件完整性：**
```bash
python scripts/analysis/check_model_load.py [模型文件路径]
```

## 📝 使用示例

### 完整部署流程
```bash
# 1. 克隆项目
git clone <repository>
cd AI-Sound

# 2. 一键部署
./scripts/deploy.sh

# 3. 健康检查
./scripts/megatts3_health.sh

# 4. 访问应用
# 前端: http://localhost:3001
# API: http://localhost:3001/api
```

### 语音分析流程
```bash
# 分析单个音频文件
python scripts/analysis/analyze_voice_features.py data/voices/sample.wav

# 批量分析目录下所有文件
python scripts/analysis/analyze_voice_features.py data/voices/

# 检查特征文件
python scripts/analysis/check_npy_shape.py data/features/voice_001.npy
```

## 🆘 故障排查

### 部署失败
```bash
# 查看详细日志
docker-compose logs -f

# 重新部署
./scripts/deploy.sh clean
./scripts/deploy.sh
```

### MegaTTS3问题
```bash
# 运行完整健康检查
./scripts/megatts3_health.sh

# 检查GPU状态
nvidia-smi

# 重启MegaTTS3服务
docker-compose restart ai-sound-megatts3
```

### 分析工具问题
```bash
# 检查Python环境
python --version

# 安装依赖
pip install librosa soundfile matplotlib numpy scipy
```

## 📚 相关文档

- [部署指南](../docs/deployment.md)
- [项目文档](../README.md)
- [配置说明](../DEPLOYMENT.md)

---

💡 **提示**: 所有脚本都包含详细的错误处理和日志输出，遇到问题时请查看控制台输出信息。 