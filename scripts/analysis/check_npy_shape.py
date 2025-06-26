"""
检查声音特征NPY文件的维度
确保数据格式符合要求(应为3D格式如[1,150,32])
"""

import os
import numpy as np
import glob

def check_npy_file(file_path):
    """检查单个NPY文件的维度"""
    try:
        data = np.load(file_path)
        print(f"文件: {os.path.basename(file_path)}")
        print(f"  维度: {data.shape}")
        print(f"  类型: {data.dtype}")
        
        # 检查是否为3D格式
        if len(data.shape) == 3:
            print(f"  ✅ 正确的3D格式")
        elif len(data.shape) == 2:
            print(f"  ⚠️ 2D格式，可能需要转换为3D格式: {data.shape} -> [{1}, {data.shape[0]}, {data.shape[1]}]")
            # 示范如何转换
            reshaped = data.reshape(1, data.shape[0], data.shape[1])
            print(f"  转换后的维度: {reshaped.shape}")
        else:
            print(f"  ❌ 不支持的维度格式: {len(data.shape)}D")
        
        return data.shape
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {str(e)}")
        return None

def main():
    """主函数"""
    print("===== 声音特征NPY文件检查 =====")
    print("检查文件是否是正确的3D格式 [1, seq_len, dim]")
    
    # 定义要检查的目录
    directories = [
        "./services/data/voice_features",
        "D:/AI-Sound/services/data/voice_features",
        "./data/voice_features",
        "./voice_samples",
        "D:/AI-Sound/data/checkpoints/voice_samples"
    ]
    
    found_files = False
    
    for directory in directories:
        if os.path.exists(directory):
            print(f"\n检查目录: {directory}")
            npy_files = glob.glob(os.path.join(directory, "*.npy"))
            
            if npy_files:
                found_files = True
                print(f"找到 {len(npy_files)} 个NPY文件")
                
                for npy_file in npy_files:
                    print("\n----------------------------")
                    shape = check_npy_file(npy_file)
                    
                    # 如果是2D格式，创建转换后的3D版本
                    if shape and len(shape) == 2:
                        try:
                            data = np.load(npy_file)
                            reshaped = data.reshape(1, data.shape[0], data.shape[1])
                            
                            # 保存转换后的文件
                            new_filename = os.path.splitext(npy_file)[0] + "_3d.npy"
                            np.save(new_filename, reshaped)
                            print(f"  已创建3D版本: {os.path.basename(new_filename)}")
                        except Exception as e:
                            print(f"  创建3D版本失败: {str(e)}")
            else:
                print(f"目录中没有NPY文件")
        else:
            print(f"目录不存在: {directory}")
    
    if not found_files:
        print("\n❌ 未找到任何NPY文件，请确保声音特征文件存在")
    
    print("\n检查完成。")

if __name__ == "__main__":
    main() 