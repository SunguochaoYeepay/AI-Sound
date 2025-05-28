import subprocess
import sys

models = [
    "kan-bayashi/aishell3_vits",
    "kan-bayashi/aishell3_tacotron2",
    "kan-bayashi/csmsc_vits",
    "kan-bayashi/csmsc_tacotron2",
    "kan-bayashi/baker_vits",
    "kan-bayashi/baker_tacotron2",
    "kan-bayashi/thchs30_vits"
]

python_exe = sys.executable  # 当前 venv 的 python 路径

for model in models:
    print(f"正在下载: {model}")
    subprocess.run([python_exe, "download_espnet_model.py", model])
