# 脚本目录说明

此目录包含项目的各种脚本工具。

## 目录结构

- `tools/`: 实用工具脚本
  - `start_api_server.py`: API服务启动脚本
  - `bfg.jar`: Git仓库清理工具

- `analysis/`: 分析工具脚本
  - `analyze_voice_features.py`: 语音特征分析工具
  - `check_npy_shape.py`: NPY文件格式检查工具
  - `check_model_load.py`: 模型加载测试工具

## 使用说明

### 启动API服务
```bash
python scripts/tools/start_api_server.py
```

### 分析语音特征
```bash
python scripts/analysis/analyze_voice_features.py [参数]
```

### 检查NPY文件格式
```bash
python scripts/analysis/check_npy_shape.py [文件路径]
```

### 检查模型加载
```bash
python scripts/analysis/check_model_load.py [模型路径]
``` 