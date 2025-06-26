# 测试合成中心页面加载的API数据
import requests
import json

def test_synthesis_center_apis():
    base_url = "http://localhost:8000"
    project_id = 34
    
    print("🔍 测试合成中心页面相关API")
    print("="*60)
    
    # 1. 测试项目详情API (前端首次加载时调用)
    print("\n1. 项目详情API (/api/v1/novel-reader/projects/34)")
    try:
        response = requests.get(f"{base_url}/api/v1/novel-reader/projects/{project_id}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                project = data.get('data', {})
                print(f"✅ 项目详情加载成功")
                print(f"   - 项目名称: {project.get('name')}")
                print(f"   - 项目状态: {project.get('status')}")
                print(f"   - 总段落数: {project.get('total_segments')}")
                print(f"   - 已处理数: {project.get('processed_segments')}")
                print(f"   - 进度: {project.get('progress')}%")
                
                # 检查statistics字段
                stats = project.get('statistics', {})
                print(f"   - 统计数据: {stats}")
                
                return project
            else:
                print(f"❌ API返回失败: {data.get('message')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    return None

def test_progress_api():
    base_url = "http://localhost:8000"
    project_id = 34
    
    print("\n2. 进度API (/api/v1/novel-reader/projects/34/progress)")
    try:
        response = requests.get(f"{base_url}/api/v1/novel-reader/projects/{project_id}/progress")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                progress = data.get('data', {})
                print(f"✅ 进度数据加载成功")
                print(f"   - 状态: {progress.get('status')}")
                print(f"   - 进度百分比: {progress.get('progress_percentage')}%")
                
                segments = progress.get('segments', {})
                print(f"   - 段落统计: {segments}")
                
                return progress
            else:
                print(f"❌ API返回失败: {data.get('message')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    return None

def main():
    # 测试项目详情
    project = test_synthesis_center_apis()
    
    # 测试进度API
    progress = test_progress_api()
    
    print("\n" + "="*60)
    print("📊 前端数据对比分析")
    
    if project and progress:
        print(f"\n项目详情API vs 进度API:")
        print(f"  项目详情 - 总数: {project.get('total_segments')}, 已完成: {project.get('processed_segments')}")
        print(f"  进度API  - 总数: {progress.get('segments', {}).get('total')}, 已完成: {progress.get('segments', {}).get('completed')}")
        
        # 分析statistics字段
        stats = project.get('statistics', {})
        if stats:
            print(f"\n前端statistics字段分析:")
            print(f"  totalSegments: {stats.get('totalSegments')}")
            print(f"  completedSegments: {stats.get('completedSegments')}")
            print(f"  failedSegments: {stats.get('failedSegments')}")
            
            print(f"\n✨ 前端应该显示的数据:")
            total = stats.get('totalSegments', 0)
            completed = stats.get('completedSegments', 0)
            if total > 0:
                percent = round((completed / total) * 100, 1)
                print(f"  总段落: {total}")
                print(f"  已完成: {completed}")
                print(f"  进度: {percent}%")
            else:
                print(f"  ⚠️ 总段落数为0，可能数据有问题")

if __name__ == "__main__":
    main()