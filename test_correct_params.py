#!/usr/bin/env python3
import requests
import json

print('🎯 测试修复后的参数格式...')

# 使用Gradio版本的正确格式
data = {
    'lyrics': '[intro-short]\n\n[verse]\n夜晚的街灯闪烁',
    'description': '',  # 单数
    'genre': 'Pop',     # 正确的参数名
    'cfg_coef': 1.5,
    'temperature': 0.9,
    'top_k': 50
}

print('发送数据:', json.dumps(data, indent=2, ensure_ascii=False))

try:
    response = requests.post(
        'http://localhost:7862/generate',
        json=data,
        headers={'Content-Type': 'application/json'},
        timeout=30
    )
    print(f'响应状态码: {response.status_code}')
    if response.status_code == 200:
        result = response.json()
        print('✅ 成功！响应:', json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print('❌ 失败，响应:', response.text)
except Exception as e:
    print(f'❌ 异常: {e}') 