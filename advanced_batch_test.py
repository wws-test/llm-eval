#!/usr/bin/env python3
"""
高级批量性能测试脚本
支持配置文件、多种测试场景、结果保存等功能

使用方法:
1. 修改 batch_test_config.json 配置文件
2. 运行脚本: python advanced_batch_test.py [scenario_name]
   - 不指定scenario_name时使用 run_1k_4K_equivalent
   - 可用场景: run_1k_4K_equivalent, quick_test, comprehensive_test

示例:
  python advanced_batch_test.py                    # 使用默认场景
  python advanced_batch_test.py quick_test         # 使用快速测试场景
  python advanced_batch_test.py comprehensive_test # 使用全面测试场景
"""

import requests
import json
import time
import sys
import os
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional

class BatchPerformanceTestRunner:
    """批量性能测试运行器"""
    
    def __init__(self, config_file: str = "batch_test_config.json"):
        """初始化测试运行器"""
        self.config = self.load_config(config_file)
        self.api_base_url = self.config["api_config"]["base_url"]
        self.api_token = self.config["api_config"]["token"]
        self.timeout = self.config["api_config"]["timeout"]
        
    def load_config(self, config_file: str) -> dict:
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ 配置文件 {config_file} 不存在")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ 配置文件格式错误: {e}")
            sys.exit(1)
    
    def make_api_request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """发送API请求"""
        url = f"{self.api_base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=self.timeout)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"API请求失败: {e}")
            return {"success": False, "error": str(e)}
    
    def check_server_health(self) -> bool:
        """检查服务器健康状态"""
        print("检查服务器连接...")
        result = self.make_api_request("GET", "/health")
        
        if result.get("success"):
            print("✅ 服务器连接正常")
            return True
        else:
            print(f"❌ 服务器连接失败: {result.get('error')}")
            return False
    
    def get_available_models(self) -> List[dict]:
        """获取可用的模型列表"""
        print("获取可用模型列表...")
        result = self.make_api_request("GET", "/performance-eval/models")
        
        if result.get("success"):
            models = result.get("data", [])
            print(f"找到 {len(models)} 个可用模型:")
            for model in models:
                print(f"  - ID: {model['id']}, 名称: {model['name']}, 显示名: {model['display_name']}")
            return models
        else:
            print(f"获取模型列表失败: {result.get('error')}")
            return []
    
    def get_available_datasets(self) -> List[dict]:
        """获取可用的数据集列表"""
        print("获取可用数据集列表...")
        result = self.make_api_request("GET", "/performance-eval/datasets")
        
        if result.get("success"):
            datasets = result.get("data", [])
            print(f"找到 {len(datasets)} 个可用数据集:")
            for dataset in datasets:
                print(f"  - ID: {dataset['id']}, 名称: {dataset['name']}, 描述: {dataset.get('description', 'N/A')}")
            return datasets
        else:
            print(f"获取数据集列表失败: {result.get('error')}")
            return []
    
    def create_batch_task(self, scenario_config: dict) -> Optional[dict]:
        """创建批量测试任务"""
        print(f"创建批量性能测试任务: {scenario_config['name']}")
        
        data = {
            "model_id": scenario_config["model_id"],
            "dataset_id": scenario_config["dataset_id"],
            "num_prompts_list": scenario_config["num_prompts_list"],
            "max_concurrency_list": scenario_config["max_concurrency_list"],
            "input_output_pairs": scenario_config["input_output_pairs"],
            "name": scenario_config["name"],
            "description": scenario_config["description"]
        }
        
        result = self.make_api_request("POST", "/performance-eval/batch-tasks/from-script", data)
        
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
            return None
    
    def monitor_task_progress(self, task_id: int) -> bool:
        """监控任务执行进度"""
        monitoring_config = self.config["monitoring"]
        check_interval = monitoring_config["check_interval_seconds"]
        max_wait_minutes = monitoring_config["max_wait_minutes"]
        show_progress = monitoring_config["show_progress"]
        
        print(f"开始监控任务 {task_id} 的执行进度...")
        print(f"最大等待时间: {max_wait_minutes} 分钟")
        
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        
        while True:
            # 获取任务状态
            result = self.make_api_request("GET", f"/performance-eval/tasks/{task_id}")
            
            if not result.get("success"):
                print(f"❌ 获取任务状态失败: {result.get('error')}")
                return False
            
            task = result.get("data", {})
            status = task.get("status", "unknown")
            elapsed_time = time.time() - start_time
            
            if show_progress:
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
            
            # 等待指定时间后再次检查
            time.sleep(check_interval)
    
    def save_results(self, task_id: int, scenario_name: str) -> bool:
        """保存测试结果"""
        output_config = self.config["output"]
        if not output_config["save_results"]:
            return True
        
        results_dir = output_config["results_dir"]
        os.makedirs(results_dir, exist_ok=True)
        
        # 获取任务详情
        result = self.make_api_request("GET", f"/performance-eval/tasks/{task_id}")
        if not result.get("success"):
            print(f"❌ 获取任务结果失败: {result.get('error')}")
            return False
        
        task_data = result.get("data", {})
        
        # 生成结果文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{scenario_name}_{task_id}_{timestamp}.json"
        filepath = os.path.join(results_dir, filename)
        
        # 保存结果
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(task_data, f, ensure_ascii=False, indent=2)
            print(f"📁 测试结果已保存到: {filepath}")
            return True
        except Exception as e:
            print(f"❌ 保存结果失败: {e}")
            return False
    
    def run_scenario(self, scenario_name: str) -> bool:
        """运行指定的测试场景"""
        scenarios = self.config["test_scenarios"]
        
        if scenario_name not in scenarios:
            print(f"❌ 未找到测试场景: {scenario_name}")
            print(f"可用场景: {', '.join(scenarios.keys())}")
            return False
        
        scenario_config = scenarios[scenario_name]
        
        print("=" * 60)
        print(f"🚀 开始执行测试场景: {scenario_name}")
        print(f"📝 描述: {scenario_config['description']}")
        print("=" * 60)
        
        # 检查服务器健康状态
        if not self.check_server_health():
            return False
        
        # 获取可用资源（可选，用于验证）
        models = self.get_available_models()
        datasets = self.get_available_datasets()
        
        if not models:
            print("❌ 没有可用的模型")
            return False
        
        # 创建批量测试任务
        task = self.create_batch_task(scenario_config)
        if not task:
            return False
        
        task_id = task.get("id")
        if not task_id:
            print("❌ 无法获取任务ID")
            return False
        
        # 监控任务执行
        success = self.monitor_task_progress(task_id)
        
        if success:
            # 保存结果
            self.save_results(task_id, scenario_name)
            
            print("\n" + "=" * 60)
            print("🎉 批量性能测试完成!")
            print(f"📊 查看结果: {self.api_base_url.replace('/api', '')}/perf-eval/results/{task_id}")
            print("=" * 60)
            return True
        else:
            print("\n" + "=" * 60)
            print("❌ 批量性能测试失败或超时")
            print("=" * 60)
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="高级批量性能测试脚本")
    parser.add_argument(
        "scenario", 
        nargs="?", 
        default="run_1k_4K_equivalent",
        help="测试场景名称 (默认: run_1k_4K_equivalent)"
    )
    parser.add_argument(
        "--config", 
        default="batch_test_config.json",
        help="配置文件路径 (默认: batch_test_config.json)"
    )
    
    args = parser.parse_args()
    
    # 创建测试运行器
    runner = BatchPerformanceTestRunner(args.config)
    
    # 运行测试场景
    success = runner.run_scenario(args.scenario)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
