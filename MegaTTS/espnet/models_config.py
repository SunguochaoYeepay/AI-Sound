MODEL_CONFIG = {
    "tts_train_raw_phn_pypinyin_g2p_phone": {
        "display_name": "普通话基础模型",
        "params": [
            {"name": "speed", "type": "float", "default": 1.0, "min": 0.5, "max": 2.0, "label": "语速"},
            {"name": "pitch", "type": "float", "default": 0.0, "min": -12, "max": 12, "label": "音调"},
            {"name": "volume", "type": "float", "default": 1.0, "min": 0.0, "max": 2.0, "label": "音量"}
        ]
    }
    # 新模型下载后，按需补充
}
