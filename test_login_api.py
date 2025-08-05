#!/usr/bin/env python3
"""
测试登录API的脚本
"""

import requests
import json

def test_login_api():
    """测试登录API"""
    base_url = "http://localhost:5000/api"
    
    # 测试数据
    test_cases = [
        {
            "name": "正常登录",
            "data": {"username": "admin", "password": "admin"},
            "expected_status": 200
        },
        {
            "name": "空用户名",
            "data": {"username": "", "password": "admin"},
            "expected_status": 400
        },
        {
            "name": "空密码",
            "data": {"username": "admin", "password": ""},
            "expected_status": 400
        },
        {
            "name": "缺少用户名字段",
            "data": {"password": "admin"},
            "expected_status": 400
        },
        {
            "name": "缺少密码字段",
            "data": {"username": "admin"},
            "expected_status": 400
        },
        {
            "name": "非JSON请求",
            "data": "username=admin&password=admin",
            "expected_status": 400,
            "content_type": "application/x-www-form-urlencoded"
        }
    ]
    
    print("🧪 开始测试登录API...")
    print(f"📍 API地址: {base_url}/auth/login")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"[{i}/{len(test_cases)}] 测试: {test_case['name']}")
        
        try:
            headers = {"Content-Type": test_case.get("content_type", "application/json")}
            
            if test_case.get("content_type") == "application/x-www-form-urlencoded":
                response = requests.post(
                    f"{base_url}/auth/login",
                    data=test_case["data"],
                    headers=headers,
                    timeout=10
                )
            else:
                response = requests.post(
                    f"{base_url}/auth/login",
                    json=test_case["data"],
                    headers=headers,
                    timeout=10
                )
            
            print(f"   状态码: {response.status_code}")
            print(f"   预期状态码: {test_case['expected_status']}")
            
            try:
                response_data = response.json()
                print(f"   响应: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            except:
                print(f"   响应: {response.text}")
            
            if response.status_code == test_case["expected_status"]:
                print("   ✅ 测试通过")
            else:
                print("   ❌ 测试失败")
                
        except requests.exceptions.ConnectionError:
            print("   ❌ 连接失败 - 请确保后端服务正在运行")
        except Exception as e:
            print(f"   ❌ 测试异常: {e}")
        
        print()

if __name__ == "__main__":
    test_login_api()
