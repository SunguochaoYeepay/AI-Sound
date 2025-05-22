"""
测试MegaTTS3依赖项
"""

import sys
import os

print("Python版本:", sys.version)
print("\nSYS.PATH:")
for p in sys.path:
    print(f"  - {p}")

megatts_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "MegaTTS3")
print(f"\nMegaTTS3路径: {megatts_path}")
print(f"路径存在: {os.path.exists(megatts_path)}")

# 添加MegaTTS3到路径
if megatts_path not in sys.path:
    sys.path.insert(0, megatts_path)

print("\n测试导入MegaTTS3模块:")
try:
    import MegaTTS3
    print(f"MegaTTS3导入成功: {MegaTTS3}")
except ImportError as e:
    print(f"MegaTTS3导入失败: {e}")

# 尝试导入tts模块
print("\n测试导入tts模块:")
try:
    from MegaTTS3 import tts
    print(f"导入tts成功: {tts}")
except ImportError as e:
    print(f"导入tts失败: {e}")

# 尝试导入infer_cli模块
print("\n测试导入infer_cli模块:")
try:
    from MegaTTS3.tts import infer_cli
    print(f"导入infer_cli成功: {infer_cli}")
except ImportError as e:
    print(f"导入infer_cli失败: {e}")

# 检查关键依赖
print("\n测试导入关键依赖:")
dependencies = [
    "transformers", 
    "torch", 
    "numpy", 
    "librosa", 
    "tn.chinese.normalizer",
    "langdetect",
    "pydub",
    "pyloudnorm"
]

for dep in dependencies:
    try:
        exec(f"import {dep}")
        print(f"{dep}: 成功")
    except ImportError as e:
        print(f"{dep}: 失败 - {e}") 