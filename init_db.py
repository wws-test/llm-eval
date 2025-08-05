#!/usr/bin/env python3
"""
数据库初始化脚本
用于创建数据库表和初始化基础数据
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import pymysql

# 加载环境变量
load_dotenv()

def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__)
    
    # 从环境变量获取数据库配置
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '3306')
    db_user = os.environ.get('DB_USER', 'root')
    db_password = os.environ.get('DB_PASSWORD', '')
    db_name = os.environ.get('DB_NAME', 'llm_eva')
    
    # 配置应用
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'charset': 'utf8mb4',
            'autocommit': True
        }
    }
    
    return app

def test_mysql_connection():
    """测试MySQL连接"""
    try:
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_port = int(os.environ.get('DB_PORT', '3306'))
        db_user = os.environ.get('DB_USER', 'root')
        db_password = os.environ.get('DB_PASSWORD', '')
        
        print(f"🔍 测试MySQL连接: {db_user}@{db_host}:{db_port}")
        
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            charset='utf8mb4'
        )
        
        print("✅ MySQL连接成功!")
        
        # 检查数据库是否存在
        db_name = os.environ.get('DB_NAME', 'llm_eva')
        cursor = connection.cursor()
        cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
        result = cursor.fetchone()
        
        if result:
            print(f"✅ 数据库 '{db_name}' 已存在")
        else:
            print(f"⚠️  数据库 '{db_name}' 不存在，正在创建...")
            cursor.execute(f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ 数据库 '{db_name}' 创建成功!")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ MySQL连接失败: {e}")
        return False

def init_database():
    """初始化数据库表和数据"""
    print("🚀 开始初始化数据库...")
    
    # 测试MySQL连接
    if not test_mysql_connection():
        print("❌ 数据库连接失败，请检查配置")
        return False
    
    # 创建Flask应用
    app = create_app()

    with app.app_context():
        try:
            # 导入所有模型
            from app.models import User, AIModel, Dataset, ChatSession, ChatMessage, ModelEvaluation
            from app import db
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
                
                # 提交所有更改
                db.session.commit()
                print("✅ 基础数据初始化完成!")
                print(f"   - 管理员账户: admin/admin")
                print(f"   - 系统模型: {len(system_models)}个")
            else:
                print("ℹ️  数据库已有数据，跳过初始化")
            
            # 显示数据库状态
            print("\n📊 数据库状态:")
            print(f"   - 用户数量: {User.query.count()}")
            print(f"   - 模型数量: {AIModel.query.count()}")
            print(f"   - 数据集数量: {Dataset.query.count()}")
            print(f"   - 对话会话: {ChatSession.query.count()}")
            print(f"   - 评估任务: {ModelEvaluation.query.count()}")
            
            return True
            
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
            db.session.rollback()
            return False

def main():
    """主函数"""
    print("=" * 50)
    print("🗄️  LLM评估平台 - 数据库初始化")
    print("=" * 50)
    
    # 检查环境变量
    required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"❌ 缺少必需的环境变量: {', '.join(missing_vars)}")
        print("请检查 .flaskenv 文件配置")
        return False
    
    # 显示配置信息
    print("📋 数据库配置:")
    print(f"   - 主机: {os.environ.get('DB_HOST')}")
    print(f"   - 端口: {os.environ.get('DB_PORT')}")
    print(f"   - 用户: {os.environ.get('DB_USER')}")
    print(f"   - 数据库: {os.environ.get('DB_NAME')}")
    print()
    
    # 初始化数据库
    success = init_database()
    
    if success:
        print("\n🎉 数据库初始化完成!")
        print("现在可以启动应用了:")
        print("   python run_api.py")
    else:
        print("\n❌ 数据库初始化失败!")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
