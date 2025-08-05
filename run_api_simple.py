#!/usr/bin/env python3
"""
简化的API启动脚本
使用应用工厂模式，避免循环导入问题
"""

import os
import sys

def main():
    """主函数"""
    print("🚀 启动LLM评估平台API服务...")
    
    try:
        # 使用应用工厂模式创建应用
        from app import create_app
        app = create_app('development')

        # 为API开发禁用CSRF保护
        app.config['WTF_CSRF_ENABLED'] = False

        print("✅ 应用创建成功")
        
        # 在应用上下文中初始化数据库
        with app.app_context():
            from app import db
            from app.models import User, AIModel, Dataset
            
            # 创建数据库表
            db.create_all()
            print("✅ 数据库表创建成功")
            
            # 检查是否需要初始化数据
            if User.query.count() == 0:
                print("📝 初始化基础数据...")
                
                # 创建管理员用户
                admin_user = User(username='admin')
                admin_user.set_password('admin')
                db.session.add(admin_user)
                
                # 创建测试用户
                test_user = User(username='test')
                test_user.set_password('test')
                db.session.add(test_user)
                
                # 创建系统模型
                system_models = [
                    {
                        'display_name': 'GPT-4o',
                        'model_identifier': 'gpt-4o',
                        'provider_name': 'OpenAI',
                        'model_type': 'openai_compatible',
                        'api_base_url': 'https://api.openai.com/v1',
                        'is_system_model': True,
                        'is_validated': True,
                        'default_temperature': 0.7,
                        'system_prompt': 'You are a helpful assistant.'
                    },
                    {
                        'display_name': 'Claude-3 Opus',
                        'model_identifier': 'claude-3-opus-20240229',
                        'provider_name': 'Anthropic',
                        'model_type': 'openai_compatible',
                        'api_base_url': 'https://api.anthropic.com/v1',
                        'is_system_model': True,
                        'is_validated': True,
                        'default_temperature': 0.7,
                        'system_prompt': 'You are Claude, an AI assistant created by Anthropic.'
                    },
                    {
                        'display_name': 'Qwen2.5-72B-Instruct',
                        'model_identifier': 'qwen/Qwen2.5-72B-Instruct',
                        'provider_name': 'ModelScope',
                        'model_type': 'openai_compatible',
                        'api_base_url': 'https://api-inference.modelscope.cn/v1',
                        'encrypted_api_key': 'ms-4038de08-d62e-4f6c-a481-e6ef3b2b4232',
                        'is_system_model': True,
                        'is_validated': True,
                        'default_temperature': 0.7,
                        'system_prompt': 'You are Qwen, created by Alibaba Cloud.'
                    }
                ]
                
                for model_data in system_models:
                    model = AIModel(**model_data)
                    db.session.add(model)
                
                # 创建示例数据集
                sample_dataset = Dataset(
                    name='示例数据集',
                    description='用于测试的示例数据集',
                    dataset_type='qa',
                    user_id=admin_user.id,
                    record_count=100
                )
                db.session.add(sample_dataset)
                
                db.session.commit()
                print("✅ 基础数据初始化完成!")
                print(f"   - 管理员账户: admin/admin")
                print(f"   - 测试账户: test/test")
                print(f"   - 系统模型: {len(system_models)}个")
                print(f"   - 示例数据集: 1个")
        
        print("🚀 启动API开发服务器...")
        print("📍 API端点: http://localhost:5000/api/")
        print("🔍 健康检查: http://localhost:5000/health")
        
        # 启动开发服务器
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
