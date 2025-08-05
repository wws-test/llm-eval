#!/usr/bin/env python3
"""
批量性能测试示例脚本
用于替代 run_1k_4K.sh 脚本，使用新的批量测试框架

使用方法:
1. 确保后端服务正在运行
2. 修改配置参数（模型ID、数据集ID等）
3. 运行脚本: python batch_performance_test_example.py
"""

import requests
import json
import time
import sys
from typing import List, Tuple

# 配置参数
API_BASE_URL = "http://localhost:5000/api"
API_TOKEN = "1"  # 使用开发者后门token

# 测试配置（对应原脚本的参数）
NUM_PROMPTS_LIST = [8, 16, 16, 48, 256, 384, 512, 512, 1024]
MAX_CONCURRENCY_LIST = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
INPUT_OUTPUT_PAIRS = [
    [128, 128],
    [256, 256],
    [128, 2048],
    [2048, 128],
    [1024, 1024],
    [2048, 2048]
]

# 模型和数据集配置（需要根据实际情况修改）
MODEL_ID = 1  # 需要替换为实际的模型ID
DATASET_ID = -1  # -1表示使用内置openqa数据集
TASK_NAME = "Qwen3-235B-A22B_批量压测"
TASK_DESCRIPTION = "基于原run_1k_4K.sh脚本的批量性能测试"


def make_api_request(method: str, endpoint: str, data: dict = None) -> dict:
    """发送API请求"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_TOKEN}"
    }
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"API请求失败: {e}")
        return {"success": False, "error": str(e)}


def get_available_models() -> List[dict]:
    """获取可用的模型列表"""
    print("获取可用模型列表...")
    result = make_api_request("GET", "/performance-eval/models")
    
    if result.get("success"):
        models = result.get("data", [])
        print(f"找到 {len(models)} 个可用模型:")
        for model in models:
            print(f"  - ID: {model['id']}, 名称: {model['name']}, 显示名: {model['display_name']}")
        return models
    else:
        print(f"获取模型列表失败: {result.get('error')}")
        return []


def get_available_datasets() -> List[dict]:
    """获取可用的数据集列表"""
    print("获取可用数据集列表...")
    result = make_api_request("GET", "/performance-eval/datasets")
    
    if result.get("success"):
        datasets = result.get("data", [])
        print(f"找到 {len(datasets)} 个可用数据集:")
        for dataset in datasets:
            print(f"  - ID: {dataset['id']}, 名称: {dataset['name']}, 描述: {dataset.get('description', 'N/A')}")
        return datasets
    else:
        print(f"获取数据集列表失败: {result.get('error')}")
        return []


def create_batch_task_from_script() -> dict:
    """使用脚本样式参数创建批量测试任务"""
    print("创建批量性能测试任务...")
    
    data = {
        "model_id": MODEL_ID,
        "dataset_id": DATASET_ID,
        "num_prompts_list": NUM_PROMPTS_LIST,
        "max_concurrency_list": MAX_CONCURRENCY_LIST,
        "input_output_pairs": INPUT_OUTPUT_PAIRS,
        "name": TASK_NAME,
        "description": TASK_DESCRIPTION
    }
    
    result = make_api_request("POST", "/performance-eval/batch-tasks/from-script", data)
    
    if result.get("success"):
        task = result.get("data", {})
        print(f"✅ 批量测试任务创建成功!")
        print(f"   任务ID: {task.get('id')}")
        print(f"   任务名称: {task.get('task_name')}")
        print(f"   模型: {task.get('model_name')}")
        print(f"   数据集: {task.get('dataset_name')}")
        print(f"   测试配置数量: {task.get('test_count')}")
        print(f"   状态: {task.get('status')}")
        return task
    else:
        print(f"❌ 创建批量测试任务失败: {result.get('error')}")
        return {}


def monitor_task_progress(task_id: int, max_wait_minutes: int = 30) -> bool:
    """监控任务执行进度"""
    print(f"开始监控任务 {task_id} 的执行进度...")
    print(f"最大等待时间: {max_wait_minutes} 分钟")
    
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    
    while True:
        # 获取任务状态
        result = make_api_request("GET", f"/performance-eval/tasks/{task_id}")
        
        if not result.get("success"):
            print(f"❌ 获取任务状态失败: {result.get('error')}")
            return False
        
        task = result.get("data", {})
        status = task.get("status", "unknown")
        elapsed_time = time.time() - start_time
        
        print(f"[{elapsed_time:.0f}s] 任务状态: {status}")
        
        if status == "completed":
            print("✅ 任务执行完成!")
            return True
        elif status == "failed":
            error_msg = task.get("error_message", "未知错误")
            print(f"❌ 任务执行失败: {error_msg}")
            return False
        elif elapsed_time > max_wait_seconds:
            print(f"⏰ 任务执行超时（超过{max_wait_minutes}分钟）")
            return False
        
        # 等待10秒后再次检查
        time.sleep(10)


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 批量性能测试示例脚本")
    print("=" * 60)
    
    # 检查服务器连接
    print("检查服务器连接...")
    health_result = make_api_request("GET", "/health")
    if not health_result.get("success"):
        print("❌ 无法连接到服务器，请确保后端服务正在运行")
        sys.exit(1)
    print("✅ 服务器连接正常")
    
    # 获取可用资源
    models = get_available_models()
    datasets = get_available_datasets()
    
    if not models:
        print("❌ 没有可用的模型")
        sys.exit(1)
    
    # 创建批量测试任务
    task = create_batch_task_from_script()
    if not task:
        sys.exit(1)
    
    task_id = task.get("id")
    if not task_id:
        print("❌ 无法获取任务ID")
        sys.exit(1)
    
    # 监控任务执行
    success = monitor_task_progress(task_id, max_wait_minutes=30)
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 批量性能测试完成!")
        print(f"📊 查看结果: {API_BASE_URL.replace('/api', '')}/perf-eval/results/{task_id}")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 批量性能测试失败或超时")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
