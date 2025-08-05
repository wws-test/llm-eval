# 批量性能测试功能说明

## 📋 概述

本文档介绍了新增的批量性能测试功能，该功能完全支持 EvalScope 的模型性能压测能力，并提供了比原 `run_1k_4K.sh` 脚本更强大和灵活的测试框架。

## ✨ 主要特性

### ✅ 完全兼容 EvalScope 压测功能

- **并发测试配置**: 支持定义多组不同的并发数进行压测
- **固定输入测试**: 支持精确控制输入和输出 token 长度
- **远程服务器测试**: 支持对部署在其他服务器上的大模型服务进行压测
- **测试架构分离**: 测试发起端只负责发起测试请求和收集结果

### 🚀 增强功能

- **批量测试配置**: 一次性配置多组测试参数，自动执行
- **脚本样式兼容**: 直接支持原 `run_1k_4K.sh` 脚本的参数格式
- **结果聚合展示**: 统一展示和对比多组测试结果
- **任务监控**: 实时监控测试进度和状态
- **结果保存**: 自动保存测试结果到文件

## 🏗️ 架构设计

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   测试发起端    │    │   后端服务      │    │   远程模型服务  │
│                 │    │                 │    │                 │
│ • 批量测试脚本  │───▶│ • 批量测试API   │───▶│ • 大模型服务    │
│ • 配置管理      │    │ • 任务调度      │    │ • OpenAI API    │
│ • 结果收集      │    │ • 结果聚合      │    │ • vLLM/其他     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📦 安装和配置

### 1. 数据库迁移

首先需要为数据库添加批量测试支持的字段：

```bash
python migrate_performance_eval_table.py
```

### 2. 重启后端服务

确保后端服务包含了新的批量测试功能：

```bash
python start_api.py
```

## 🚀 使用方法

### 方法一：使用高级批量测试脚本（推荐）

1. **配置测试参数**

编辑 `batch_test_config.json` 文件：

```json
{
  "api_config": {
    "base_url": "http://localhost:5000/api",
    "token": "1"
  },
  "test_scenarios": {
    "run_1k_4K_equivalent": {
      "name": "Qwen3-235B-A22B_批量压测",
      "model_id": 1,
      "dataset_id": -1,
      "num_prompts_list": [8, 16, 16, 48, 256, 384, 512, 512, 1024],
      "max_concurrency_list": [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024],
      "input_output_pairs": [
        [128, 128],
        [256, 256],
        [128, 2048],
        [2048, 128],
        [1024, 1024],
        [2048, 2048]
      ]
    }
  }
}
```

2. **运行测试**

```bash
# 使用默认场景（等效于原 run_1k_4K.sh）
python advanced_batch_test.py

# 使用快速测试场景
python advanced_batch_test.py quick_test

# 使用全面测试场景
python advanced_batch_test.py comprehensive_test
```

### 方法二：使用简单批量测试脚本

```bash
python batch_performance_test_example.py
```

### 方法三：通过 API 直接调用

```python
import requests

# 创建批量测试任务
data = {
    "model_id": 1,
    "dataset_id": -1,
    "num_prompts_list": [8, 16, 48, 256],
    "max_concurrency_list": [1, 2, 8, 32],
    "input_output_pairs": [[128, 128], [1024, 1024]],
    "name": "我的批量测试",
    "description": "测试描述"
}

response = requests.post(
    "http://localhost:5000/api/performance-eval/batch-tasks/from-script",
    json=data,
    headers={"Authorization": "Bearer 1"}
)

print(response.json())
```

## 📊 测试结果

### 结果查看

1. **Web界面**: 访问 `http://localhost:5000/perf-eval/results/{task_id}`
2. **API接口**: `GET /api/performance-eval/tasks/{task_id}`
3. **保存的文件**: 在 `./batch_test_results/` 目录下

### 结果格式

批量测试结果包含：

- **整体汇总**: 总测试数、成功率、失败率
- **单项结果**: 每个配置的详细性能指标
- **对比分析**: 不同配置间的性能对比

## 🔧 配置说明

### 测试场景配置

```json
{
  "scenario_name": {
    "name": "测试名称",
    "description": "测试描述",
    "model_id": 1,                    // 模型ID
    "dataset_id": -1,                 // 数据集ID（-1为内置数据集）
    "num_prompts_list": [10, 20],     // 请求数量列表
    "max_concurrency_list": [1, 4],   // 并发数列表
    "input_output_pairs": [           // 输入输出长度对
      [128, 128],
      [1024, 1024]
    ]
  }
}
```

### API配置

```json
{
  "api_config": {
    "base_url": "http://localhost:5000/api",  // API基础URL
    "token": "1",                             // 认证token
    "timeout": 30                             // 请求超时时间
  }
}
```

## 🆚 与原脚本对比

| 功能 | 原 run_1k_4K.sh | 新批量测试框架 |
|------|-----------------|----------------|
| 并发测试 | ✅ | ✅ |
| 固定输入输出 | ✅ | ✅ |
| 远程服务测试 | ✅ | ✅ |
| 批量配置 | ❌ | ✅ |
| 任务监控 | ❌ | ✅ |
| 结果聚合 | ❌ | ✅ |
| Web界面 | ❌ | ✅ |
| API接口 | ❌ | ✅ |
| 配置文件 | ❌ | ✅ |
| 结果保存 | 基础日志 | 结构化数据 |

## 🔍 故障排除

### 常见问题

1. **数据库迁移失败**
   - 检查数据库连接
   - 确保有足够的权限
   - 手动执行SQL语句

2. **API请求失败**
   - 检查后端服务是否运行
   - 验证API token是否正确
   - 检查网络连接

3. **模型或数据集不存在**
   - 使用 `python advanced_batch_test.py` 查看可用资源
   - 更新配置文件中的ID

### 调试模式

在配置文件中启用详细日志：

```json
{
  "monitoring": {
    "show_progress": true,
    "check_interval_seconds": 5
  }
}
```

## 📈 性能优化建议

1. **合理设置并发数**: 根据服务器性能调整并发数
2. **分批执行**: 对于大量测试配置，考虑分批执行
3. **监控资源**: 监控CPU、内存、网络使用情况
4. **调整超时**: 根据模型响应时间调整超时设置

## 🤝 贡献

欢迎提交问题和改进建议！

## 📄 许可证

与主项目保持一致的开源许可证。
