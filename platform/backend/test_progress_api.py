# 测试项目34的进度API
import requests
import json

def test_progress_api():
    base_url = "http://localhost:8000"
    
    # 测试novel-reader的进度API
    try:
        response = requests.get(f"{base_url}/api/v1/novel-reader/projects/34/progress")
        print(f"Novel-reader进度API状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Novel-reader进度数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"Novel-reader进度API错误: {response.text}")
    except Exception as e:
        print(f"Novel-reader进度API请求失败: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试project的进度API
    try:
        response = requests.get(f"{base_url}/api/v1/projects/34/progress")
        print(f"Projects进度API状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Projects进度数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"Projects进度API错误: {response.text}")
    except Exception as e:
        print(f"Projects进度API请求失败: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试项目详情API
    try:
        response = requests.get(f"{base_url}/api/v1/novel-reader/projects/34")
        print(f"项目详情API状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            project_data = data.get('data', {})
            print(f"项目详情 - 总段落: {project_data.get('total_segments')}")
            print(f"项目详情 - 已处理: {project_data.get('processed_segments')}")
            print(f"项目详情 - 进度: {project_data.get('progress')}%")
            print(f"项目详情 - 状态: {project_data.get('status')}")
        else:
            print(f"项目详情API错误: {response.text}")
    except Exception as e:
        print(f"项目详情API请求失败: {e}")

if __name__ == "__main__":
    test_progress_api()