# 配置目录说明

此目录包含项目的配置文件。

## 文件说明

- `test_config.json`: 测试配置文件，用于配置测试参数

## 使用方法

在代码中引用配置：

```python
import json
import os

config_path = os.path.join('config', 'test_config.json')
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)
``` 