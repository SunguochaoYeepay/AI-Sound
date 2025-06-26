# ESPnet TTS Docker 使用说明

## 1. 本地目录准备

确保你的本地 `D:/AI-Sound/megaTTS/espnet` 目录结构如下（最少要有这些文件）：

```
D:/AI-Sound/megaTTS/espnet/
├── test.txt                # 输入文本，每行一句
├── exp/
│   └── tts_train_xxx/
│       ├── valid.acc.ave.pth   # 预训练模型
│       └── config.yaml         # 配置文件
```

- `test.txt` 示例内容：
  ```
  你好，世界！
  Hello, world！
  ```

## 2. 启动 ESPnet Docker 容器

```bash
docker run --gpus all -it --rm -v D:/AI-Sound/megaTTS/espnet:/workspace espnet/espnet:gpu-latest /bin/bash
```

- 进入容器后，`/workspace` 就是你本地的 `D:/AI-Sound/megaTTS/espnet`

## 3. 容器内执行 TTS 推理命令

```bash
cd /workspace

python3 /espnet/espnet2/bin/tts_inference.py \
  --ngpu 1 \
  --data_path_and_name_and_type "test.txt,text,text" \
  --model_file "exp/tts_train_xxx/valid.acc.ave.pth" \
  --train_config "exp/tts_train_xxx/config.yaml" \
  --output_dir "output"
```

- `/espnet/espnet2/bin/tts_inference.py` 是容器内 ESPnet 的推理脚本路径（如报错可用 `find / -name tts_inference.py` 查找）
- `test.txt`：输入文本
- `model_file` 和 `train_config`：按你实际模型路径填写
- `output`：输出目录，合成音频会保存在这里

## 4. 查看结果

- 合成的音频文件会在 `/workspace/output` 目录下
- 你本地 `D:/AI-Sound/megaTTS/espnet/output` 也能直接访问

## 5. HTTP API 服务（Flask）

### 5.1 启动 API 服务

确保已安装依赖（容器内执行）：
```bash
pip install flask soundfile
```

运行 API 服务（容器内 espnet 目录下）：
```bash
python espnet_tts_api.py
```
- 默认监听 `0.0.0.0:5000`

### 5.2 Docker 端口映射

如果在 Docker 容器内运行，需加端口映射参数：
```bash
docker run -p 5000:5000 ...
```

### 5.3 API 调用示例

```bash
curl -X POST http://localhost:5000/tts -H "Content-Type: application/json" -d '{"text": "你好，世界！"}' --output output.wav
```

---

## 6. Gradio 页面服务

### 6.1 启动 Gradio 服务

确保已安装依赖（容器内执行）：
```bash
pip install gradio soundfile
```

运行 Gradio 页面服务（容器内 espnet 目录下）：
```bash
python espnet_tts_gradio.py
```
- 默认监听 `0.0.0.0:7860`，如脚本内有端口参数以实际为准（如日志显示 5001 就用 5001）
- 启动后浏览器访问 `http://localhost:7860` 或实际端口即可使用页面

### 6.2 Docker 端口映射

如果在 Docker 容器内运行，需加端口映射参数：
```bash
docker run -p 7860:7860 ...
```
- 如实际端口为 5001，则用 `-p 5001:5001`，访问 `http://localhost:5001`

### 6.3 常见报错说明

- **NLTK 报错**：如 `Error loading averaged_perceptron_tagger`、`cmudict` 等，是因为容器无网络，影响英文分词/发音，中文 TTS 不受影响。
- **Gradio analytics 报错**：如 `httpcore.ConnectTimeout`，是匿名统计上报失败，不影响页面功能。
- **页面服务端口**：以实际启动日志为准，注意端口映射。

---

如遇 `espnet2` 未找到，需先激活 conda 环境：
```bash
source /opt/conda/etc/profile.d/conda.sh
conda activate espnet
```

如有其他问题，建议先查容器日志或反馈给开发者。

---

## 常见问题

- **模型和配置文件去哪找？**  
  可从 ESPnet 官方或 HuggingFace 下载预训练模型，放到 `exp/tts_train_xxx/` 目录下。
- **推理脚本路径不对怎么办？**  
  用 `find / -name tts_inference.py` 在容器里查找实际路径。

---

## 7. Windows 一键启动 Gradio 页面服务脚本

为避免多端口冲突和重复容器，推荐使用如下 Windows 批处理脚本一键启动 Gradio 页面服务（适用于 base 环境）：

### 7.1 脚本内容（espnet_gradio_start.bat）

```bat
@echo off
REM === 1. 先杀掉所有 espnet/espnet:gpu-latest 容器 ===
for /f "tokens=1" %%i in ('docker ps -a --filter "ancestor=espnet/espnet:gpu-latest" -q') do docker stop %%i

REM === 2. 选择端口（可自定义） ===
set PORT=9000

REM === 3. 启动 espnet 容器并自动进入bash（base环境下安装依赖并启动服务） ===
docker run --gpus all -it --rm -v D:/AI-Sound/megaTTS/espnet:/workspace -p %PORT%:%PORT% espnet/espnet:gpu-latest /bin/bash -c "pip install espnet gradio soundfile && cd /workspace && python espnet_tts_gradio.py --port %PORT%"

pause
```

### 7.2 使用方法

1. 将上述内容保存为 `espnet_gradio_start.bat`，放在任意目录。
2. 双击运行，自动清理旧容器，只会启动一个新容器，端口不会冲突。
3. 浏览器访问：`http://localhost:9000`（如自定义端口，按实际端口访问）。

---

如需自定义端口，修改脚本中的 `set PORT=9000` 即可。
