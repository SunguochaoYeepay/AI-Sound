# ESPnet TTS HTTP API 服务搭建文档

## 1. 方案说明
本方案基于 Flask + ESPnet，提供一个开源、可自部署的 HTTP API 服务，支持通过 POST 请求合成语音，便于后续系统集成和二次开发。

---

## 2. 依赖环境
- Python 3.8+
- espnet（已安装）
- torch（已安装）
- soundfile
- flask

安装 Flask 和 soundfile：
```bash
pip install flask soundfile
```

---

## 3. API 服务脚本示例
将以下内容保存为 `espnet_tts_api.py`：

```python
from flask import Flask, request, send_file, jsonify
from espnet2.bin.tts_inference import Text2Speech
import soundfile as sf
import tempfile
import torch

app = Flask(__name__)
text2speech = Text2Speech(
    train_config="exp/tts_train_raw_phn_pypinyin_g2p_phone/config.yaml",
    model_file="exp/tts_train_raw_phn_pypinyin_g2p_phone/valid.acc.ave.pth",
    device="cuda" if torch.cuda.is_available() else "cpu"
)

@app.route('/tts', methods=['POST'])
def tts():
    text = request.json.get('text')
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    wav = text2speech(text)["wav"].view(-1).cpu().numpy()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, wav, 24000)
        return send_file(f.name, mimetype="audio/wav", as_attachment=True, download_name="output.wav")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

---

## 4. 启动服务
在 `espnet` 目录下运行：
```bash
python espnet_tts_api.py
```

---

## 5. 调用示例
用 curl 或 Postman 发送 POST 请求：
```bash
curl -X POST http://localhost:5000/tts -H "Content-Type: application/json" -d '{"text": "你好，世界！"}' --output output.wav
```

---

## 6. 端口映射（Docker 场景）
如在 Docker 容器内运行，需加端口映射：
```bash
docker run -p 5000:5000 ...
```

---

## 7. 备注
- 支持中文、英文等多种模型，只需更换 `train_config` 和 `model_file` 路径
- 可根据实际需求扩展 API 功能
- 如需前端页面，可用 Gradio/Streamlit 快速搭建
