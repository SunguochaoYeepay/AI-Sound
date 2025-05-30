#!/usr/bin/env python3
"""
全面验证ESPnet和MegaTTS3服务可用性
确保两个服务都能为AI-Sound提供接口
"""

import urllib.request
import urllib.error
import json
import time

class TTSServiceValidator:
    def __init__(self):
        self.espnet_url = "http://127.0.0.1:9001"
        self.megatts_url = "http://127.0.0.1:7929"
        
    def test_service_health(self, service_name, base_url):
        """测试服务健康状态"""
        print(f"\n🏥 测试 {service_name} 健康状态")
        try:
            req = urllib.request.Request(f"{base_url}/health")
            with urllib.request.urlopen(req, timeout=10) as response:
                health_data = json.loads(response.read().decode())
                print(f"   ✅ {service_name} 健康: {health_data}")
                return True, health_data
        except Exception as e:
            print(f"   ❌ {service_name} 健康检查失败: {e}")
            return False, None
    
    def discover_megatts_endpoints(self):
        """发现MegaTTS3的API端点"""
        print(f"\n🔍 发现MegaTTS3 API端点")
        
        # 尝试常见的API端点
        endpoints_to_try = [
            "/",
            "/voices",
            "/api/voices", 
            "/api/voice-pairs",
            "/api/synthesis/synthesize-by-text",
            "/synthesize",
            "/tts",
            "/generate",
            "/docs",
            "/openapi.json"
        ]
        
        available_endpoints = []
        
        for endpoint in endpoints_to_try:
            try:
                req = urllib.request.Request(f"{self.megatts_url}{endpoint}")
                with urllib.request.urlopen(req, timeout=5) as response:
                    status = response.getcode()
                    content_type = response.headers.get('Content-Type', '')
                    
                    if status == 200:
                        available_endpoints.append({
                            'endpoint': endpoint,
                            'status': status,
                            'content_type': content_type
                        })
                        print(f"   ✅ {endpoint} - {status} ({content_type})")
                    
            except urllib.error.HTTPError as e:
                if e.code != 404:  # 忽略404，记录其他错误
                    print(f"   ⚠️ {endpoint} - HTTP {e.code}")
            except Exception:
                pass  # 忽略连接错误
        
        return available_endpoints
    
    def test_espnet_synthesis(self):
        """测试ESPnet语音合成"""
        print(f"\n🎵 测试ESPnet语音合成")
        try:
            data = {
                "text": "ESPnet服务验证测试",
                "speaker": "espnet_zh_female_001",
                "speed": 1.0,
                "volume": 1.0
            }
            
            json_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(
                f"{self.espnet_url}/synthesize",
                data=json_data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                content_type = response.headers.get('Content-Type', '')
                audio_size = len(response.read())
                
                print(f"   ✅ 合成成功: {audio_size} bytes, {content_type}")
                
                if 'audio' in content_type and audio_size > 10000:
                    print(f"   🎉 ESPnet返回真实音频!")
                    return True
                else:
                    print(f"   ⚠️ 数据异常: 可能是模拟音频")
                    return False
                    
        except Exception as e:
            print(f"   ❌ ESPnet合成失败: {e}")
            return False
    
    def test_megatts_synthesis(self):
        """测试MegaTTS3语音合成"""
        print(f"\n🎵 测试MegaTTS3语音合成")
        
        # 尝试不同的合成端点
        synthesis_endpoints = [
            "/api/synthesis/synthesize-by-text",
            "/synthesize", 
            "/tts",
            "/generate"
        ]
        
        test_data_variants = [
            {
                "text": "MegaTTS3服务验证测试",
                "voice_id": "default"
            },
            {
                "text": "MegaTTS3服务验证测试",
                "speaker": "default"
            },
            {
                "text": "MegaTTS3服务验证测试"
            }
        ]
        
        for endpoint in synthesis_endpoints:
            for data in test_data_variants:
                try:
                    json_data = json.dumps(data).encode('utf-8')
                    req = urllib.request.Request(
                        f"{self.megatts_url}{endpoint}",
                        data=json_data,
                        headers={'Content-Type': 'application/json'},
                        method='POST'
                    )
                    
                    with urllib.request.urlopen(req, timeout=30) as response:
                        content_type = response.headers.get('Content-Type', '')
                        response_size = len(response.read())
                        
                        print(f"   ✅ {endpoint} 成功: {response_size} bytes, {content_type}")
                        
                        if 'audio' in content_type and response_size > 1000:
                            print(f"   🎉 MegaTTS3返回音频!")
                            return True, endpoint
                        elif response_size > 100:
                            print(f"   📄 返回数据，可能需要进一步处理")
                            
                except urllib.error.HTTPError as e:
                    if e.code != 404:
                        print(f"   ⚠️ {endpoint} HTTP {e.code}")
                except Exception as e:
                    pass  # 继续尝试其他端点
        
        print(f"   ❌ 未找到可用的MegaTTS3合成端点")
        return False, None
    
    def validate_services(self):
        """综合验证两个服务"""
        print("🔥 AI-Sound TTS服务全面验证")
        print("=" * 60)
        
        results = {
            'espnet': {'health': False, 'synthesis': False},
            'megatts3': {'health': False, 'synthesis': False, 'endpoints': []}
        }
        
        # 1. ESPnet验证
        print("\n🎯 验证ESPnet服务")
        results['espnet']['health'], _ = self.test_service_health("ESPnet", self.espnet_url)
        if results['espnet']['health']:
            results['espnet']['synthesis'] = self.test_espnet_synthesis()
        
        # 2. MegaTTS3验证  
        print("\n🎯 验证MegaTTS3服务")
        results['megatts3']['health'], _ = self.test_service_health("MegaTTS3", self.megatts_url)
        if results['megatts3']['health']:
            results['megatts3']['endpoints'] = self.discover_megatts_endpoints()
            synthesis_ok, endpoint = self.test_megatts_synthesis()
            results['megatts3']['synthesis'] = synthesis_ok
            if synthesis_ok:
                results['megatts3']['working_endpoint'] = endpoint
        
        # 3. 最终报告
        print("\n" + "=" * 60)
        print("📊 验证结果汇总")
        print("=" * 60)
        
        # ESPnet状态
        espnet_status = "🟢 完全可用" if all(results['espnet'].values()) else "🔴 有问题"
        print(f"ESPnet: {espnet_status}")
        print(f"  - 健康检查: {'✅' if results['espnet']['health'] else '❌'}")
        print(f"  - 语音合成: {'✅' if results['espnet']['synthesis'] else '❌'}")
        
        # MegaTTS3状态
        megatts_fully_working = results['megatts3']['health'] and results['megatts3']['synthesis']
        megatts_status = "🟢 完全可用" if megatts_fully_working else "🔴 有问题"
        print(f"MegaTTS3: {megatts_status}")
        print(f"  - 健康检查: {'✅' if results['megatts3']['health'] else '❌'}")
        print(f"  - 语音合成: {'✅' if results['megatts3']['synthesis'] else '❌'}")
        print(f"  - 可用端点: {len(results['megatts3']['endpoints'])}")
        
        # 整体结论
        both_working = all(results['espnet'].values()) and megatts_fully_working
        print(f"\n🎯 最终结论:")
        if both_working:
            print("🎉 两个TTS服务都完全可用! AI-Sound系统可以正常工作!")
        else:
            print("⚠️ 至少有一个服务存在问题，需要进一步调试")
            
        return results

if __name__ == "__main__":
    validator = TTSServiceValidator()
    validator.validate_services()