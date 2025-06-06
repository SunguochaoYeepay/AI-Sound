#!/usr/bin/env python3
"""
创建默认声音角色
用户可以后续手工上传声音文件
"""
import requests
import json

def create_default_voices():
    print("🎭 === 创建默认声音角色 ===")
    
    # API基地址
    api_base = "http://localhost:3001/api/characters"
    
    # 默认角色列表
    default_voices = [
        {
            "name": "温柔女声",
            "description": "温柔甜美的女性声音，适合朗读文学作品和温暖故事",
            "voice_type": "female",
            "color": "#ff6b9d",
            "tags": "温柔,甜美,文学"
        },
        {
            "name": "磁性男声", 
            "description": "低沉有磁性的男性声音，适合商务播报和严肃内容",
            "voice_type": "male",
            "color": "#4e73df",
            "tags": "磁性,低沉,商务"
        },
        {
            "name": "专业主播",
            "description": "专业播音员声音，声音清晰标准，适合新闻播报",
            "voice_type": "female", 
            "color": "#1cc88a",
            "tags": "专业,播音,新闻"
        },
        {
            "name": "青春活力",
            "description": "年轻有活力的声音，适合娱乐内容和轻松对话",
            "voice_type": "female",
            "color": "#36b9cc",
            "tags": "青春,活力,娱乐"
        },
        {
            "name": "成熟稳重",
            "description": "成熟稳重的男性声音，适合教育内容和知识分享",
            "voice_type": "male",
            "color": "#f6c23e", 
            "tags": "成熟,稳重,教育"
        },
        {
            "name": "童声萌音",
            "description": "清脆可爱的儿童声音，适合童话故事和儿童内容",
            "voice_type": "child",
            "color": "#e74a3b",
            "tags": "童声,可爱,童话"
        }
    ]
    
    created_count = 0
    failed_count = 0
    
    for voice_data in default_voices:
        try:
            print(f"\n📝 创建角色: {voice_data['name']}")
            
            # 准备表单数据
            form_data = {
                'name': voice_data['name'],
                'description': voice_data['description'],
                'voice_type': voice_data['voice_type'],
                'tags': voice_data['tags'],
                'color': voice_data['color'],
                'parameters': json.dumps({"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0})
            }
            
            # 发送POST请求
            response = requests.post(api_base, data=form_data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    created_count += 1
                    print(f"  ✅ 创建成功: {voice_data['name']} (ID: {result['data']['id']})")
                else:
                    failed_count += 1
                    print(f"  ❌ 创建失败: {result.get('message', '未知错误')}")
            else:
                failed_count += 1
                print(f"  ❌ HTTP错误: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            failed_count += 1
            print(f"  ❌ 网络错误: {str(e)}")
        except Exception as e:
            failed_count += 1
            print(f"  ❌ 异常: {str(e)}")
    
    print(f"\n🎉 === 默认角色创建完成 ===")
    print(f"✅ 成功创建: {created_count} 个角色")
    print(f"❌ 创建失败: {failed_count} 个角色")
    print(f"📊 总计: {len(default_voices)} 个角色")
    
    if created_count > 0:
        print("\n📝 下一步操作：")
        print("1. 打开浏览器访问: http://localhost:3001")
        print("2. 进入声音库管理页面")
        print("3. 选择任意角色，点击编辑")
        print("4. 上传对应的音频文件和latent文件")
        print("5. 保存后即可使用该声音进行合成")
        
        print("\n🔧 音频文件要求：")
        print("- 格式：WAV, MP3, FLAC, M4A, OGG")
        print("- 大小：不超过100MB")
        print("- 建议：10-30秒的清晰语音")
        
        print("\n🧠 Latent文件要求：")
        print("- 格式：NPY文件")
        print("- 大小：不超过50MB")
        print("- 说明：可选，系统会自动生成")
    
    return created_count > 0

if __name__ == "__main__":
    import time
    print("⏳ 等待服务启动...")
    time.sleep(10)  # 等待容器完全启动
    
    success = create_default_voices()
    if not success:
        print("\n❌ 未能成功创建任何角色，请检查服务状态")
        exit(1)