#!/usr/bin/env python3
"""
简单的API测试脚本
"""

import requests
import json

def test_api():
    """测试API基本功能"""
    base_url = "http://localhost:5000"
    
    print("🧪 测试API基本功能...")
    
    # 1. 测试健康检查
    print("\n[1] 测试健康检查")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"   响应: {response.json()}")
            print("   ✅ 健康检查通过")
        else:
            print("   ❌ 健康检查失败")
    except requests.exceptions.ConnectionError:
        print("   ❌ 连接失败 - API服务未启动")
        return False
    except Exception as e:
        print(f"   ❌ 测试异常: {e}")
        return False
    
    # 2. 测试登录API
    print("\n[2] 测试登录API")
    try:
        login_data = {"username": "admin", "password": "admin"}
        response = requests.post(f"{base_url}/api/auth/login", json=login_data, timeout=5)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                token = data['data']['token']
                print(f"   ✅ 登录成功，token: {token[:20]}...")
                
                # 3. 测试模型列表API
                print("\n[3] 测试模型列表API")
                headers = {'Authorization': f'Bearer {token}'}
                response = requests.get(f"{base_url}/api/models", headers=headers, timeout=5)
                print(f"   状态码: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        models = data['data']['models']
                        print(f"   ✅ 获取到 {len(models)} 个模型")
                        for model in models[:3]:  # 只显示前3个
                            print(f"      - {model['display_name']} ({model['model_type']})")
                    else:
                        print(f"   ❌ API返回失败: {data.get('error')}")
                else:
                    print(f"   ❌ HTTP错误: {response.status_code}")
                
                # 4. 测试统计数据API
                print("\n[4] 测试统计数据API")
                response = requests.get(f"{base_url}/api/stats/dashboard", headers=headers, timeout=5)
                print(f"   状态码: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        stats = data['data']['overview']
                        print(f"   ✅ 统计数据获取成功:")
                        print(f"      - 模型数量: {stats['total_models']}")
                        print(f"      - 对话数量: {stats['total_chats']}")
                        print(f"      - 数据集数量: {stats['total_datasets']}")
                        print(f"      - 评估任务: {stats['total_evaluations']}")
                    else:
                        print(f"   ❌ API返回失败: {data.get('error')}")
                else:
                    print(f"   ❌ HTTP错误: {response.status_code}")
                
                return True
            else:
                print(f"   ❌ 登录失败: {data.get('error')}")
        else:
            print(f"   ❌ 登录HTTP错误: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 测试异常: {e}")
    
    return False

if __name__ == "__main__":
    success = test_api()
    if success:
        print("\n🎉 API测试完成，基本功能正常！")
    else:
        print("\n❌ API测试失败，请检查服务状态")
