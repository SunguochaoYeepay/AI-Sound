import requests
import time
import os

# 确保输出目录存在
os.makedirs("test_voices", exist_ok=True)

# 测试文本
TEST_TEXT = "这是一段测试不同角色声音的文本，需要确认每个角色是否有不同的声音特征。"

# 测试不同角色声音
def test_different_voices():
    """测试不同角色是否有不同声音"""
    print("\n开始测试不同角色声音...")
    
    # 声音列表
    voices = ["范闲", "周杰伦", "english_talk", "female_young", "male_young"]
    
    # 对每个声音生成音频
    for voice_id in voices:
        print(f"测试角色: {voice_id}")
        
        try:
            # 发送TTS请求
            response = requests.post(
                "http://127.0.0.1:9930/api/tts/text",
                json={"text": TEST_TEXT, "voice_id": voice_id},
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
            if response.status_code == 200:
                # 保存响应音频
                output_path = f"test_voices/{voice_id}_{int(time.time())}.wav"
                with open(output_path, "wb") as f:
                    f.write(response.content)
                print(f"✅ 请求成功 - 音频已保存到: {output_path}")
                print(f"   文件大小: {len(response.content)} 字节")
            else:
                print(f"❌ 请求失败 - 状态码: {response.status_code}")
                print(f"   错误信息: {response.text}")
        except Exception as e:
            print(f"❌ 异常: {str(e)}")

# 执行测试
if __name__ == "__main__":
    test_different_voices()
    print("\n测试完成。请手动比较生成的音频文件，检查不同角色是否具有不同的声音特征。")