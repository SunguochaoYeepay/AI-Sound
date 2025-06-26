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
    try:
        text = request.json.get('text')
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        result = text2speech(text)
        wav = result["wav"].view(-1).cpu().numpy()
        print(f"合成音频长度: {len(wav)} 采样率: 24000")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, wav, 24000)
            return send_file(f.name, mimetype="audio/wav", as_attachment=True, download_name="output.wav")
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
