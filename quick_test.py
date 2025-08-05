import requests

# 测试开发者后门
headers = {'Authorization': 'Bearer 1'}
response = requests.get('http://localhost:5000/api/dev/info', headers=headers)
print(f"状态码: {response.status_code}")
print(f"响应: {response.json()}")
