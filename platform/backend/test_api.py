import requests
import json

def test_api():
    try:
        # 测试项目详情
        print("=== 测试项目详情 ===")
        response = requests.get('http://localhost:8000/api/v1/novel-reader/projects/24')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                project = data['data']
                print(f"项目名称: {project['name']}")
                print(f"项目状态: {project['status']}")
                print(f"进度: {project['progress']}%")
            else:
                print(f"API返回错误: {data}")
        else:
            print(f"HTTP错误: {response.text}")
        
        print("\n=== 测试启动合成 ===")
        # 测试启动合成
        response = requests.post('http://localhost:8000/api/v1/novel-reader/projects/24/start')
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    test_api() 