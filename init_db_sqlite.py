#!/usr/bin/env python3
"""
数据库初始化脚本 - SQLite版本
用于快速开发和测试，使用SQLite数据库
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__)
    
    # 配置应用 - 使用SQLite
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///llm_eval.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    return app

def init_database():
    """初始化数据库表和数据"""
    print("🚀 开始初始化SQLite数据库...")

    # 创建Flask应用
    app = create_app()

    with app.app_context():
        try:
            # 初始化扩展
            db = SQLAlchemy()
            db.init_app(app)
            migrate = Migrate(app, db)

            # 导入所有模型
            from app.models import User, AIModel, Dataset, ChatSession, ChatMessage, ModelEvaluation
            print("✅ 模型导入成功")

            # 创建所有表
            print("📋 创建数据库表...")
            db.create_all()
            print("✅ 数据库表创建成功!")

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
                        'api_base_url': os.environ.get('SYSTEM_PROVIDER_BASE_URL', 'https://api-inference.modelscope.cn/v1'),
                        'encrypted_api_key': os.environ.get('SYSTEM_PROVIDER_API_KEY'),
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
                
                # 提交所有更改
                db.session.commit()
                print("✅ 基础数据初始化完成!")
                print(f"   - 管理员账户: admin/admin")
                print(f"   - 测试账户: test/test")
                print(f"   - 系统模型: {len(system_models)}个")
                print(f"   - 示例数据集: 1个")
            else:
                print("ℹ️  数据库已有数据，跳过初始化")
            
            # 显示数据库状态
            print("\n📊 数据库状态:")
            print(f"   - 用户数量: {User.query.count()}")
            print(f"   - 模型数量: {AIModel.query.count()}")
            print(f"   - 数据集数量: {Dataset.query.count()}")
            print(f"   - 对话会话: {ChatSession.query.count()}")
            print(f"   - 评估任务: {ModelEvaluation.query.count()}")
            
            # 显示数据库文件位置
            db_path = os.path.abspath('llm_eval.db')
            print(f"\n📁 数据库文件: {db_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

def main():
    """主函数"""
    print("=" * 50)
    print("🗄️  LLM评估平台 - SQLite数据库初始化")
    print("=" * 50)
    
    # 初始化数据库
    success = init_database()
    
    if success:
        print("\n🎉 SQLite数据库初始化完成!")
        print("现在可以启动应用了:")
        print("   python run_api.py")
        print("\n💡 提示:")
        print("   - 使用SQLite进行开发和测试")
        print("   - 生产环境建议使用MySQL")
        print("   - 数据库文件: llm_eval.db")
    else:
        print("\n❌ 数据库初始化失败!")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
