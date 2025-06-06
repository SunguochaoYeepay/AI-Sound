#!/usr/bin/env python3
"""
直接通过数据库创建默认声音角色
绕过API，直接操作数据库
"""
import os
import sys
import psycopg2
import json
from datetime import datetime

def create_default_voices_db():
    print("🎭 === 直接创建默认声音角色 ===")
    
    # 数据库连接参数
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'ai_sound',
        'user': 'ai_sound_user',
        'password': 'ai_sound_password'
    }
    
    # 默认角色列表
    default_voices = [
        {
            "name": "温柔女声",
            "description": "温柔甜美的女性声音，适合朗读文学作品和温暖故事",
            "type": "female",
            "color": "#ff6b9d",
            "tags": '["温柔", "甜美", "文学"]'
        },
        {
            "name": "磁性男声", 
            "description": "低沉有磁性的男性声音，适合商务播报和严肃内容",
            "type": "male",
            "color": "#4e73df",
            "tags": '["磁性", "低沉", "商务"]'
        },
        {
            "name": "专业主播",
            "description": "专业播音员声音，声音清晰标准，适合新闻播报",
            "type": "female", 
            "color": "#1cc88a",
            "tags": '["专业", "播音", "新闻"]'
        },
        {
            "name": "青春活力",
            "description": "年轻有活力的声音，适合娱乐内容和轻松对话",
            "type": "female",
            "color": "#36b9cc",
            "tags": '["青春", "活力", "娱乐"]'
        },
        {
            "name": "成熟稳重",
            "description": "成熟稳重的男性声音，适合教育内容和知识分享",
            "type": "male",
            "color": "#f6c23e", 
            "tags": '["成熟", "稳重", "教育"]'
        },
        {
            "name": "童声萌音",
            "description": "清脆可爱的儿童声音，适合童话故事和儿童内容",
            "type": "child",
            "color": "#e74a3b",
            "tags": '["童声", "可爱", "童话"]'
        }
    ]
    
    try:
        # 连接数据库
        print("📡 连接数据库...")
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # 清空现有数据
        print("🧹 清空现有声音档案...")
        cursor.execute("DELETE FROM voice_profiles")
        conn.commit()
        
        # 插入默认角色
        created_count = 0
        current_time = datetime.now()
        
        for voice_data in default_voices:
            try:
                print(f"📝 创建角色: {voice_data['name']}")
                
                cursor.execute("""
                    INSERT INTO voice_profiles 
                    (name, description, type, color, tags, parameters, quality_score, 
                     usage_count, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    voice_data['name'],
                    voice_data['description'], 
                    voice_data['type'],
                    voice_data['color'],
                    voice_data['tags'],
                    '{"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}',
                    3.0,  # 默认质量分
                    0,    # 使用次数
                    'active',
                    current_time,
                    current_time
                ))
                
                created_count += 1
                print(f"  ✅ 创建成功: {voice_data['name']}")
                
            except Exception as e:
                print(f"  ❌ 创建失败: {str(e)}")
        
        # 提交事务
        conn.commit()
        
        # 验证结果
        cursor.execute("SELECT id, name, type FROM voice_profiles ORDER BY id")
        voices = cursor.fetchall()
        
        print(f"\n🎉 === 默认角色创建完成 ===")
        print(f"✅ 成功创建: {created_count} 个角色")
        print(f"📊 数据库中现有: {len(voices)} 个角色")
        
        print(f"\n📋 创建的角色列表:")
        for voice in voices:
            print(f"  ID: {voice[0]} | 名称: {voice[1]} | 类型: {voice[2]}")
        
        print(f"\n📝 下一步操作：")
        print(f"1. 打开浏览器访问: http://localhost:3001")
        print(f"2. 进入声音库管理页面")
        print(f"3. 选择任意角色，点击编辑")
        print(f"4. 上传对应的音频文件和latent文件")
        print(f"5. 保存后即可使用该声音进行合成")
        
        print(f"\n🔧 音频文件要求：")
        print(f"- 格式：WAV, MP3, FLAC, M4A, OGG")
        print(f"- 大小：不超过100MB")
        print(f"- 建议：10-30秒的清晰语音")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ 数据库错误: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_default_voices_db()
    if not success:
        print("\n❌ 创建失败，请检查数据库连接")
        sys.exit(1)
    else:
        print("\n🎉 所有默认角色创建完成！现在可以手工添加声音文件了！")