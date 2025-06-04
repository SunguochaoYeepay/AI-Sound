#!/usr/bin/env python3
"""
测试安全的音频生成功能
验证修改后的逐个处理逻辑
"""
import requests
import json
import time

# 使用固定的外网API地址
BASE_URL = "http://soundapi.cpolar.top"

def test_safe_generation():
    project_id = 19  # 使用你的项目ID
    
    print("🛡️ === 测试安全的音频生成 ===")
    
    # 1. 检查项目状态
    print("1. 检查项目状态...")
    detail_response = requests.get(f'{BASE_URL}/api/novel-reader/projects/{project_id}')
    
    if detail_response.status_code != 200:
        print(f"❌ 获取项目详情失败: {detail_response.status_code}")
        return
    
    detail = detail_response.json()['data']
    print(f"✅ 项目名称: {detail['name']}")
    print(f"📊 段落数量: {len(detail.get('segments', []))}")
    print(f"🎭 角色映射: {detail['characterMapping']}")
    print(f"📈 当前状态: {detail['status']}")
    
    # 2. 检查待处理段落
    segments = detail.get('segments', [])
    pending_count = len([s for s in segments if s.get('status') == 'pending'])
    completed_count = len([s for s in segments if s.get('status') == 'completed'])
    failed_count = len([s for s in segments if s.get('status') == 'failed'])
    
    print(f"⏳ 待处理: {pending_count}")
    print(f"✅ 已完成: {completed_count}")
    print(f"❌ 失败: {failed_count}")
    
    if not detail['characterMapping']:
        print("❌ 角色映射为空，无法开始生成")
        return
    
    if pending_count == 0:
        print("✅ 所有段落已处理完成")
        return
    
    # 3. 开始安全的音频生成 (单任务处理)
    print("\n🚀 3. 开始安全的音频生成...")
    gen_data = {'parallel_tasks': '1'}  # 使用单任务，避免CUDA内存溢出
    
    gen_response = requests.post(f'{BASE_URL}/api/novel-reader/projects/{project_id}/start-generation', data=gen_data)
    
    print(f"响应状态码: {gen_response.status_code}")
    
    if gen_response.status_code == 200:
        print("✅ 音频生成开始成功")
        result = gen_response.json()
        print(f"📝 响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # 4. 监控进度
        print("\n📊 4. 监控生成进度...")
        monitor_progress(project_id, pending_count)
        
    else:
        print(f"❌ 音频生成失败: {gen_response.status_code}")
        print(f"错误响应: {gen_response.text}")
        
        try:
            error_data = gen_response.json()
            print(f"错误详情: {error_data.get('detail', '未知错误')}")
        except:
            print("无法解析错误响应")

def monitor_progress(project_id: int, total_pending: int):
    """监控生成进度"""
    start_time = time.time()
    last_completed = 0
    
    print("开始监控进度，每10秒检查一次...")
    print("按 Ctrl+C 停止监控")
    
    try:
        while True:
            time.sleep(10)
            
            # 获取进度
            progress_response = requests.get(f'{BASE_URL}/api/novel-reader/projects/{project_id}/progress')
            
            if progress_response.status_code == 200:
                progress = progress_response.json()
                stats = progress.get('stats', {})
                
                completed = stats.get('completed', 0)
                failed = stats.get('failed', 0)
                processing = stats.get('processing', 0)
                pending = stats.get('pending', 0)
                
                elapsed = time.time() - start_time
                
                print(f"\n📊 进度更新 (运行时间: {elapsed:.0f}秒)")
                print(f"   ✅ 已完成: {completed}")
                print(f"   ⏳ 处理中: {processing}")
                print(f"   📋 待处理: {pending}")
                print(f"   ❌ 失败: {failed}")
                print(f"   📈 进度: {progress.get('progress', 0):.1f}%")
                
                # 检查是否有新完成的
                if completed > last_completed:
                    new_completed = completed - last_completed
                    avg_time = elapsed / completed if completed > 0 else 0
                    remaining_time = avg_time * pending if pending > 0 else 0
                    
                    print(f"   🚀 新完成: {new_completed} 个段落")
                    print(f"   ⏱️ 平均用时: {avg_time:.1f}秒/段落")
                    if remaining_time > 0:
                        print(f"   🕐 预计剩余: {remaining_time/60:.1f}分钟")
                    
                    last_completed = completed
                
                # 检查是否完成
                if pending == 0 and processing == 0:
                    print("\n🎉 === 音频生成完成！ ===")
                    print(f"总用时: {elapsed/60:.1f}分钟")
                    print(f"成功: {completed}, 失败: {failed}")
                    break
                    
            else:
                print(f"❌ 获取进度失败: {progress_response.status_code}")
                
    except KeyboardInterrupt:
        print("\n⏹️ 监控已停止")
        print("生成任务仍在后台继续运行")

if __name__ == "__main__":
    test_safe_generation() 