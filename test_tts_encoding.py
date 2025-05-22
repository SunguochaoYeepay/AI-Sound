import requests
import time
import os

# 测试文本
TEST_TEXT = "这是一段中文测试文本，需要确认编码问题是否导致滴滴声。"

# 确保输出目录存在
os.makedirs("test_results", exist_ok=True)

def test_without_charset():
    """测试不带charset的请求"""
    print("\n测试1: 不指定charset=utf-8...")
    try:
        response = requests.post(
            "http://127.0.0.1:9930/api/tts/text",
            json={"text": TEST_TEXT, "voice_id": "female_young"},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            # 保存响应音频
            output_path = f"test_results/no_charset_{int(time.time())}.wav"
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"✅ 请求成功 - 音频已保存到: {output_path}")
            print(f"   文件大小: {len(response.content)} 字节")
            
            # 检查文件大小判断是否为模拟音频
            if len(response.content) < 1000:
                print("❗ 警告: 文件太小，可能是模拟音频（滴滴声）")
            else:
                print("   文件大小正常，可能是真实语音")
        else:
            print(f"❌ 请求失败: {response.status_code} {response.reason}")
            print(f"   响应内容: {response.text[:200]}")
    except Exception as e:
        print(f"❌ 异常: {str(e)}")

def test_with_charset():
    """测试带charset=utf-8的请求"""
    print("\n测试2: 指定charset=utf-8...")
    try:
        response = requests.post(
            "http://127.0.0.1:9930/api/tts/text",
            json={"text": TEST_TEXT, "voice_id": "female_young"},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
        
        if response.status_code == 200:
            # 保存响应音频
            output_path = f"test_results/with_charset_{int(time.time())}.wav"
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"✅ 请求成功 - 音频已保存到: {output_path}")
            print(f"   文件大小: {len(response.content)} 字节")
            
            # 检查文件大小判断是否为模拟音频
            if len(response.content) < 1000:
                print("❗ 警告: 文件太小，可能是模拟音频（滴滴声）")
            else:
                print("   文件大小正常，可能是真实语音")
        else:
            print(f"❌ 请求失败: {response.status_code} {response.reason}")
            print(f"   响应内容: {response.text[:200]}")
    except Exception as e:
        print(f"❌ 异常: {str(e)}")

def compare_files():
    """比较测试结果文件"""
    print("\n比较测试结果...")
    
    # 获取最新的两个测试文件
    files = os.listdir("test_results")
    no_charset_files = [f for f in files if f.startswith("no_charset")]
    with_charset_files = [f for f in files if f.startswith("with_charset")]
    
    if not no_charset_files or not with_charset_files:
        print("❌ 未找到足够的测试文件进行比较")
        return
    
    # 获取最新的文件
    no_charset_file = max(no_charset_files, key=lambda f: os.path.getctime(os.path.join("test_results", f)))
    with_charset_file = max(with_charset_files, key=lambda f: os.path.getctime(os.path.join("test_results", f)))
    
    # 获取文件大小
    no_charset_size = os.path.getsize(os.path.join("test_results", no_charset_file))
    with_charset_size = os.path.getsize(os.path.join("test_results", with_charset_file))
    
    print(f"不带charset的文件: {no_charset_file}, 大小: {no_charset_size} 字节")
    print(f"带charset的文件: {with_charset_file}, 大小: {with_charset_size} 字节")
    
    # 根据文件大小判断是否为模拟音频
    if no_charset_size < 1000 and with_charset_size > 10000:
        print("\n✅ 验证成功: 不带charset生成的是模拟音频(滴滴声)，带charset生成的是真实语音")
        print("   结论: 编码问题确实会导致文本变为乱码，从而生成模拟音频(滴滴声)而非真实语音")
    elif no_charset_size > 10000 and with_charset_size > 10000:
        print("\n❓ 结果不明确: 两种方式生成的都是大文件，可能都是真实语音")
        print("   建议: 请手动播放两个音频文件进行比较")
    elif no_charset_size < 1000 and with_charset_size < 1000:
        print("\n❌ 测试失败: 两种方式生成的都是小文件，可能都是模拟音频")
        print("   可能的原因: 服务器可能有其他问题，或者两种方式都没有正确传递中文")
    else:
        print("\n❓ 结果不明确: 请手动播放两个音频文件进行比较")

if __name__ == "__main__":
    print("===== TTS编码问题测试 =====")
    print(f"测试文本: {TEST_TEXT}")
    
    # 运行测试
    test_without_charset()
    test_with_charset()
    
    # 稍等几秒让服务器完成处理
    print("\n等待3秒让服务器处理完成...")
    time.sleep(3)
    
    # 比较结果
    compare_files()