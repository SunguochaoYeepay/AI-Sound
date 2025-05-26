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

---

## 常见问题

- **模型和配置文件去哪找？**  
  可从 ESPnet 官方或 HuggingFace 下载预训练模型，放到 `exp/tts_train_xxx/` 目录下。
- **推理脚本路径不对怎么办？**  
  用 `find / -name tts_inference.py` 在容器里查找实际路径。
