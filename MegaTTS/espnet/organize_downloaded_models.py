import os
import shutil
import glob

# 1. 源目录（espnet_model_zoo缓存目录，自动适配虚拟环境/全局环境）
SITE_PACKAGES = os.path.join(os.path.dirname(__file__), 'venv', 'Lib', 'site-packages')
ZOO_ROOT = None
for d in os.listdir(SITE_PACKAGES):
    if d.startswith('espnet_model_zoo'):
        zoo_dir = os.path.join(SITE_PACKAGES, d)
        for sub in os.listdir(zoo_dir):
            if sub.startswith('models--'):
                ZOO_ROOT = os.path.join(zoo_dir, sub)
                break
        if ZOO_ROOT:
            break
if not ZOO_ROOT or not os.path.exists(ZOO_ROOT):
    print('未找到模型缓存目录！')
    exit(1)

# 2. 目标目录
EXP_DIR = os.path.join(os.path.dirname(__file__), 'exp')
os.makedirs(EXP_DIR, exist_ok=True)

# 3. 扫描所有模型快照
for root, dirs, files in os.walk(ZOO_ROOT):
    if 'config.yaml' in files:
        model_dir = root
        model_name = os.path.basename(model_dir)
        # 兼容多级目录
        if model_name == 'exp':
            model_name = os.path.basename(os.path.dirname(model_dir))
        target_dir = os.path.join(EXP_DIR, model_name)
        os.makedirs(target_dir, exist_ok=True)
        # 拷贝 config.yaml
        shutil.copy2(os.path.join(model_dir, 'config.yaml'), os.path.join(target_dir, 'config.yaml'))
        # 拷贝所有 .pth
        for pth_file in glob.glob(os.path.join(model_dir, '*.pth')):
            shutil.copy2(pth_file, os.path.join(target_dir, os.path.basename(pth_file)))
        print(f'已整理模型: {model_name} -> {target_dir}')
print('全部模型整理完成！')
