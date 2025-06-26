import sys
import os
import requests
from tqdm import tqdm
from huggingface_hub import snapshot_download, HfApi
import time
from espnet_model_zoo.downloader import ModelDownloader

def download_model(model_name: str, target_dir: str = "exp"):
    try:
        # 创建目标目录
        os.makedirs(target_dir, exist_ok=True)
        print(f"正在下载模型: {model_name}")
        
        # 设置重试次数
        max_retries = 3
        current_retry = 0
        
        while current_retry < max_retries:
            try:
                # 尝试从 ESPnet 下载器获取 URL
                print("尝试使用 ESPnet 下载器...")
                downloader = ModelDownloader()
                url = downloader.get_url(name=model_name)
                
                if url and url.startswith(("http://", "https://")):
                    print(f"找到模型 URL: {url}")
                    print("开始下载文件...")
                    
                    # 设置较长的超时时间
                    session = requests.Session()
                    session.timeout = (30, 300)  # (连接超时, 读取超时)
                    
                    response = session.get(url, stream=True)
                    response.raise_for_status()  # 检查响应状态
                    
                    # 获取文件大小
                    total_size = int(response.headers.get('content-length', 0))
                    
                    # 确定文件名
                    filename = url.split('/')[-1].split('?')[0]
                    filepath = os.path.join(target_dir, filename)
                    
                    # 下载文件并显示进度条
                    with open(filepath, 'wb') as f, tqdm(
                        desc=filename,
                        total=total_size,
                        unit='iB',
                        unit_scale=True,
                        unit_divisor=1024,
                    ) as pbar:
                        for data in response.iter_content(chunk_size=1024):
                            size = f.write(data)
                            pbar.update(size)
                    
                    print(f"文件已下载到: {filepath}")
                    print("正在解压文件...")
                    
                    # 解压文件
                    import zipfile
                    with zipfile.ZipFile(filepath, 'r') as zip_ref:
                        zip_ref.extractall(target_dir)
                    
                    print("解压完成！")
                    return {"path": target_dir, "model_file": filename}
                
                else:
                    print("ESPnet URL 无效，尝试从 HuggingFace 下载...")
                    raise ValueError("Invalid URL")
            
            except Exception as e:
                print(f"ESPnet 下载器尝试失败: {str(e)}")
                
                try:
                    print("尝试从 HuggingFace Hub 下载...")
                    # 使用 HfApi 检查模型是否存在
                    api = HfApi()
                    try:
                        api.model_info(model_name)
                    except Exception:
                        print(f"模型 {model_name} 在 HuggingFace Hub 上不存在")
                        raise
                    
                    model_path = snapshot_download(
                        repo_id=model_name,
                        local_dir=target_dir,
                        local_dir_use_symlinks=False,
                        resume_download=True
                    )
                    print(f"模型已下载到: {model_path}")
                    return {"path": model_path}
                except Exception as he:
                    print(f"HuggingFace 下载失败: {str(he)}")
                
                current_retry += 1
                if current_retry < max_retries:
                    wait_time = 5 * current_retry
                    print(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    raise Exception("所有下载方式都失败了")
    
    except Exception as e:
        print(f"下载过程中发生错误: {str(e)}")
        raise

if __name__ == "__main__":
    if len(sys.argv) > 1:
        model = sys.argv[1]
    else:
        # 默认模型，可自行修改
        model = "espnet/kan-bayashi_ljspeech_vits"
    download_model(model)