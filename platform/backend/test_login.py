#!/usr/bin/env python3
"""
测试登录功能脚本
"""

import requests
import json

def test_login():
    """测试登录功能"""
    try:
        # 登录请求
        login_url = "http://localhost:8000/api/v1/login"
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        print("🔐 测试登录...")
        print(f"URL: {login_url}")
        print(f"数据: {login_data}")
        
        response = requests.post(
            login_url, 
            data=login_data,  # 使用表单数据格式
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 登录成功！")
            print(f"访问令牌: {result.get('access_token', '')[:50]}...")
            print(f"刷新令牌: {result.get('refresh_token', '')[:50]}...")
            print(f"令牌类型: {result.get('token_type')}")
            print(f"过期时间: {result.get('expires_in')}秒")
            
            # 测试获取用户信息
            if 'access_token' in result:
                test_me_endpoint(result['access_token'])
                
        else:
            print("❌ 登录失败！")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_me_endpoint(access_token):
    """测试获取用户信息接口"""
    try:
        print("\n👤 测试获取用户信息...")
        me_url = "http://localhost:8000/api/v1/me"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(me_url, headers=headers)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            user_info = response.json()
            print("✅ 获取用户信息成功！")
            print(f"用户ID: {user_info.get('id')}")
            print(f"用户名: {user_info.get('username')}")
            print(f"邮箱: {user_info.get('email')}")
            print(f"状态: {user_info.get('status')}")
            print(f"是否管理员: {user_info.get('is_superuser')}")
        else:
            print("❌ 获取用户信息失败！")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试用户信息接口失败: {e}")

if __name__ == "__main__":
    print("🚀 开始测试登录功能...")
    test_login() 