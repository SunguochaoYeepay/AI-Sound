# AI-Sound SongGeneration引擎验证指南

## 🎯 验证目标
确认SongGeneration音乐生成引擎已正确修复并可以正常工作。

## 📋 验证步骤

### 步骤1: 启动SongGeneration容器
```powershell
# 如果容器已存在，先删除
docker rm -f songgen

# 启动新的SongGeneration容器
docker run -d --name songgen -p 8081:8081 -v "D:/AI-Sound/MegaTTS/SongGeneration:/workspace/SongGeneration" --gpus all juhayna/song-generation-levo:hf0613
```

### 步骤2: 检查容器状态
```powershell
# 查看容器是否正常运行
docker ps | findstr songgen

# 查看容器日志
docker logs songgen
```

**期望结果**: 
- 容器状态为"Up"
- 日志显示"Running on local URL: http://0.0.0.0:8081"
- 没有模型文件缺失的错误

### 步骤3: 启动AI-Sound后端
```powershell
# 在platform/backend目录下启动后端
cd platform/backend
python main.py
```

**期望结果**:
- 后端正常启动，监听8000端口
- 连接到SongGeneration服务成功
- 没有SONGGENERATION_URL配置错误

### 步骤4: 运行自动验证脚本
```powershell
# 回到AI-Sound根目录
cd ..\..\

# 运行验证脚本
python verify_songgeneration.py
```

**期望结果**:
- ✅ SongGeneration引擎: 正常
- ✅ AI-Sound后端连接: 正常
- 🎉 所有服务验证通过！

### 步骤5: Web界面验证
1. 打开浏览器访问: http://localhost:3001
2. 进入"音乐库"页面
3. 点击"AI智能生成"按钮
4. 填写测试参数:
   - 歌词: "美丽的夜晚"
   - 风格: "流行"
   - 时长: 30秒
5. 点击"开始生成"

**期望结果**:
- 生成请求成功提交
- 进度显示正常
- 最终生成音频文件并可播放

## 🔧 常见问题排查

### 问题1: 容器启动失败
**症状**: `docker run`命令报错
**解决**: 
1. 检查Docker Desktop是否运行
2. 确认GPU驱动和nvidia-docker已安装
3. 检查端口8081是否被占用

### 问题2: 模型文件缺失
**症状**: 日志显示"FileNotFoundError: Model file not found"
**解决**:
```powershell
# 复制缺失的模型文件
xcopy "D:\AI-Sound\SongGeneration-HF-Official\ckpt\models--lengyue233--content-vec-best" "D:\AI-Sound\MegaTTS\SongGeneration\ckpt\models--lengyue233--content-vec-best\" /E /I /Y

# 重启容器
docker restart songgen
```

### 问题3: AI-Sound后端连接失败
**症状**: 后端日志显示"SONGGENERATION_URL配置错误"
**解决**:
1. 确认已修改`platform/backend/app/config/__init__.py`
2. 重新启动后端服务

### 问题4: Web界面生成失败
**症状**: 点击生成按钮后报错
**解决**:
1. 检查F12开发者工具中的网络请求
2. 确认API路径正确: `/api/v1/music/generate`
3. 检查后端日志中的错误信息

## 📊 验证成功标志

当所有步骤完成后，你应该看到:

1. **Docker容器**: songgen容器运行在8081端口
2. **后端服务**: AI-Sound后端运行在8000端口并成功连接SongGeneration
3. **Web界面**: 音乐库中的AI生成功能可以正常工作
4. **验证脚本**: 所有测试项目显示✅正常

## 🎉 验证完成

如果所有步骤都成功，说明SongGeneration引擎已经完全修复并集成到AI-Sound系统中。你现在可以:

- 通过Web界面生成背景音乐
- 在小说合成中添加AI生成的背景音乐
- 通过API接口调用音乐生成功能

## 📝 注意事项

1. **GPU要求**: SongGeneration需要GPU支持，确保显卡驱动正常
2. **内存要求**: 音乐生成过程需要较大内存，建议16GB+
3. **生成时间**: 首次生成可能需要较长时间(1-3分钟)，这是正常的
4. **模型加载**: 容器启动后需要时间加载模型，请耐心等待

验证完成后，请将此文档保存，以便后续维护参考。 