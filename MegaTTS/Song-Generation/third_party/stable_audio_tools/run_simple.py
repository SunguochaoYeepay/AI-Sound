from stable_audio_tools import get_pretrained_model
from stable_audio_tools.interface.gradio import create_ui
import torch

torch.manual_seed(42)

interface = create_ui(
    model_config_path='/workspace/ckpt/third_party/stable_audio_tools/config/model_1920.json',
    ckpt_path='/workspace/ckpt/vae/autoencoder_music_1320k.ckpt',
    pretrained_name=None,
    pretransform_ckpt_path=None,
    model_half=False
)
interface.queue()
interface.launch(share=True, server_name='0.0.0.0', server_port=7862)
