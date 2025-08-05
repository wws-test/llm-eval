#!/usr/bin/env python3
"""
测试开发者后门功能
验证token="1"和token="dev"是否能直接访问API
"""

import requests
import json

BASE_URL = 'http://localhost:5000/api'

def test_backdoor_token(token_value, token_name):
    """测试指定的后门token"""
    print(f"\n🔓 测试开发者后门: {token_name} (token='{token_value}')")
    
    try:
        headers = {'Authorization': f'Bearer {token_value}'}
        
        # 测试获取模型列表
        response = requests.get(f'{BASE_URL}/models', headers=headers)
        print(f"   模型列表API响应: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                models = data.get('data', {}).get('models', [])
                print(f"   ✅ 成功获取模型列表，共 {len(models)} 个模型")
                for model in models[:3]:  # 只显示前3个
                    print(f"      - {model['display_name']}")
                return True
            else:
                print(f"   ❌ API返回失败: {data.get('error')}")
        else:
            print(f"   ❌ HTTP错误: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
    
    return False

def test_create_model_with_backdoor():
    """使用后门token测试创建模型"""
    print(f"\n➕ 使用后门token测试创建模型...")
    
    try:
        headers = {'Authorization': 'Bearer 1'}  # 使用后门token
        
        model_data = {
            'display_name': '后门测试模型',
            'model_identifier': 'backdoor-test-model',
            'api_base_url': 'https://api.example.com/v1',
            'provider_name': 'Test Provider',
            'default_temperature': 0.8,
            'system_prompt': 'You are a test model created via backdoor.',
            'notes': '这是通过开发者后门创建的测试模型'
        }
        
        response = requests.post(f'{BASE_URL}/models', json=model_data, headers=headers)
        print(f"   创建模型API响应: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ 成功创建模型: {data.get('message')}")
                model_id = data.get('data', {}).get('id')
                print(f"   新模型ID: {model_id}")
                return model_id
            else:
                print(f"   ❌ 创建失败: {data.get('error')}")
        else:
            print(f"   ❌ HTTP错误: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
    
    return None

def test_normal_auth():
    """测试正常的认证流程作为对比"""
    print(f"\n🔐 测试正常认证流程（对比）...")
    
    try:
        # 先登录获取正常token
        login_data = {'username': 'admin', 'password': 'admin'}
        response = requests.post(f'{BASE_URL}/auth/login', json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                token = data['data']['token']
                print(f"   ✅ 正常登录成功，token: {token[:20]}...")
                
                # 使用正常token访问API
                headers = {'Authorization': f'Bearer {token}'}
                response = requests.get(f'{BASE_URL}/models', headers=headers)
                
                if response.status_code == 200:
                    print(f"   ✅ 正常token访问API成功")
                    return True
                else:
                    print(f"   ❌ 正常token访问API失败: {response.status_code}")
            else:
                print(f"   ❌ 登录失败: {data.get('error')}")
        else:
            print(f"   ❌ 登录HTTP错误: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ 正常认证测试失败: {e}")
    
    return False

def test_invalid_token():
    """测试无效token（应该被拒绝）"""
    print(f"\n❌ 测试无效token（应该被拒绝）...")
    
    try:
        headers = {'Authorization': 'Bearer invalid-token-12345'}
        response = requests.get(f'{BASE_URL}/models', headers=headers)
        
        print(f"   无效token API响应: {response.status_code}")
        
        if response.status_code == 401:
            print(f"   ✅ 无效token被正确拒绝")
            return True
        else:
            print(f"   ❌ 无效token未被拒绝，这是安全问题！")
            
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
    
    return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🚪 LLM评估平台 - 开发者后门功能测试")
    print("=" * 60)
    
    # 检查服务器是否运行
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code != 200:
            print("❌ 服务器未正常运行，请先启动后端服务")
            return
        print("✅ 服务器运行正常")
    except:
        print("❌ 无法连接到服务器，请先启动后端服务")
        return
    
    # 测试各种后门token
    backdoor_tests = [
        ("1", "数字1后门"),
        ("dev", "dev后门"),
    ]
    
    success_count = 0
    for token, name in backdoor_tests:
        if test_backdoor_token(token, name):
            success_count += 1
    
    # 测试创建模型功能
    model_id = test_create_model_with_backdoor()
    
    # 测试正常认证（对比）
    test_normal_auth()
    
    # 测试无效token
    test_invalid_token()
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print(f"   - 后门token测试: {success_count}/{len(backdoor_tests)} 成功")
    print(f"   - 模型创建测试: {'✅ 成功' if model_id else '❌ 失败'}")
    print("\n💡 开发者后门使用说明:")
    print("   - 在API请求头中使用: Authorization: Bearer 1")
    print("   - 或者使用: Authorization: Bearer dev")
    print("   - 这将直接以管理员身份访问所有API")
    print("   - ⚠️  仅用于开发和调试，生产环境请禁用！")
    print("=" * 60)

if __name__ == '__main__':
    main()
