#!/usr/bin/env python3
"""
测试静态文件服务配置
"""
import os
import sys
import argparse
import requests
import time
import mimetypes
from pathlib import Path

# 确保音频类型被正确识别
mimetypes.add_type('audio/wav', '.wav')
mimetypes.add_type('audio/mpeg', '.mp3')
mimetypes.add_type('audio/ogg', '.ogg')

def test_static_files(base_url, test_file=None):
    """测试静态文件服务是否正常工作"""
    print(f"🔍 测试静态文件服务 - 基础URL: {base_url}")
    
    # 创建测试文件目录
    data_dir = Path("../data")
    audio_dir = data_dir / "audio"
    audio_dir.mkdir(exist_ok=True, parents=True)
    
    if not test_file:
        # 如果没有提供测试文件，创建一个小的测试文件
        test_file_path = audio_dir / "test_static_service.wav"
        
        if not test_file_path.exists():
            print(f"📝 创建测试文件: {test_file_path}")
            # 创建一个简单的1秒空白WAV文件
            try:
                # 标准WAV文件头 (44字节) + 1秒16位单声道8000Hz音频数据
                with open(test_file_path, "wb") as f:
                    # WAV文件头
                    f.write(b"RIFF")                  # ChunkID
                    f.write(b"\x24\x00\x00\x00")      # ChunkSize (36 + SubChunk2Size)
                    f.write(b"WAVE")                  # Format
                    f.write(b"fmt ")                  # Subchunk1ID
                    f.write(b"\x10\x00\x00\x00")      # Subchunk1Size (16 for PCM)
                    f.write(b"\x01\x00")              # AudioFormat (1 for PCM)
                    f.write(b"\x01\x00")              # NumChannels (1 for mono)
                    f.write(b"\x40\x1F\x00\x00")      # SampleRate (8000Hz)
                    f.write(b"\x40\x1F\x00\x00")      # ByteRate (SampleRate * NumChannels * BitsPerSample/8)
                    f.write(b"\x02\x00")              # BlockAlign (NumChannels * BitsPerSample/8)
                    f.write(b"\x10\x00")              # BitsPerSample (16 bits)
                    f.write(b"data")                  # Subchunk2ID
                    f.write(b"\x00\x00\x00\x00")      # Subchunk2Size (0 - empty audio)
                print("✅ 测试文件已创建")
            except Exception as e:
                print(f"❌ 创建测试文件失败: {str(e)}")
                test_file_path = None
    else:
        # 使用用户提供的测试文件
        test_file_path = Path(test_file)
        if not test_file_path.exists():
            print(f"❌ 提供的测试文件不存在: {test_file}")
            test_file_path = None
    
    if not test_file_path:
        print("❌ 没有可用的测试文件，无法继续测试")
        return
    
    # 获取文件相对路径
    rel_path = test_file_path.relative_to(data_dir)
    
    # 测试文件URL
    file_url = f"{base_url}/{rel_path}"
    print(f"🌐 测试URL: {file_url}")
    
    # 发送HEAD请求检查文件是否可访问
    try:
        print("\n1. 发送HEAD请求检查文件是否可访问")
        head_response = requests.head(file_url, timeout=10)
        print(f"状态码: {head_response.status_code}")
        print(f"内容类型: {head_response.headers.get('Content-Type', '未知')}")
        
        if head_response.status_code == 200:
            print("✅ HEAD请求成功")
        else:
            print(f"❌ HEAD请求失败: {head_response.status_code}")
    except Exception as e:
        print(f"❌ HEAD请求异常: {str(e)}")
    
    # 测试跨域资源共享
    try:
        print("\n2. 测试跨域资源共享(CORS)")
        origins = [
            "http://localhost:3000",
            "http://aisound.cpolar.top",
            "https://aisound.cpolar.top"
        ]
        
        for origin in origins:
            print(f"\n测试来源: {origin}")
            try:
                # 发送OPTIONS预检请求
                options_headers = {
                    'Origin': origin,
                    'Access-Control-Request-Method': 'GET',
                    'Access-Control-Request-Headers': 'Content-Type'
                }
                options_response = requests.options(file_url, headers=options_headers, timeout=10)
                
                print(f"OPTIONS状态码: {options_response.status_code}")
                print("CORS响应头:")
                cors_headers = {k: v for k, v in options_response.headers.items() 
                               if 'access-control' in k.lower()}
                
                for header, value in cors_headers.items():
                    print(f"  {header}: {value}")
                
                # 发送带有Origin的GET请求
                get_headers = {'Origin': origin}
                get_response = requests.get(file_url, headers=get_headers, timeout=10, 
                                          stream=True)
                
                print(f"GET状态码: {get_response.status_code}")
                allow_origin = get_response.headers.get('Access-Control-Allow-Origin')
                print(f"Access-Control-Allow-Origin: {allow_origin or '无'}")
                
                if (allow_origin == '*' or allow_origin == origin) and get_response.status_code == 200:
                    print(f"✅ 从 {origin} 访问成功")
                else:
                    print(f"❌ 从 {origin} 访问受限")
                
                # 关闭连接，避免占用资源
                get_response.close()
                
            except Exception as e:
                print(f"❌ 测试 {origin} 异常: {str(e)}")
    except Exception as e:
        print(f"❌ CORS测试异常: {str(e)}")
    
    # 测试实际文件下载
    try:
        print("\n3. 测试文件下载")
        start_time = time.time()
        download_response = requests.get(file_url, timeout=30, stream=True)
        
        if download_response.status_code == 200:
            # 流式读取内容，避免一次性加载大文件
            content_length = download_response.headers.get('Content-Length')
            content_size = int(content_length) if content_length else 0
            
            chunk_size = 8192
            total_chunks = 0
            total_bytes = 0
            
            for chunk in download_response.iter_content(chunk_size=chunk_size):
                if chunk:
                    total_bytes += len(chunk)
                    total_chunks += 1
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"下载状态码: {download_response.status_code}")
            print(f"下载内容类型: {download_response.headers.get('Content-Type', '未知')}")
            print(f"下载文件大小: {total_bytes} 字节")
            print(f"下载用时: {duration:.2f} 秒")
            print(f"下载速度: {(total_bytes / 1024) / duration:.2f} KB/s")
            
            print("✅ 文件下载成功")
        else:
            print(f"❌ 文件下载失败: {download_response.status_code}")
    except Exception as e:
        print(f"❌ 文件下载异常: {str(e)}")
    
    print("\n🎯 测试完成!")

def main():
    parser = argparse.ArgumentParser(description="测试静态文件服务配置")
    parser.add_argument("--url", default="http://localhost:3000",
                        help="API服务器基础URL")
    parser.add_argument("--file", help="要测试的音频文件路径")
    
    args = parser.parse_args()
    test_static_files(args.url, args.file)

if __name__ == "__main__":
    main() 