import sys
import os
from espnet_model_zoo.downloader import ModelDownloader

def download_model(model_name: str, target_dir: str = "exp"):
    os.makedirs(target_dir, exist_ok=True)
    downloader = ModelDownloader()
    model_info = downloader.download_and_unpack(model_name, target_dir)
    print(f"模型已下载到: {model_info['download_path']}")
    print(f"模型详细信息: {model_info}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        model = sys.argv[1]
    else:
        # 默认模型，可自行修改
        model = "espnet/kan-bayashi_ljspeech_vits"
    download_model(model) 