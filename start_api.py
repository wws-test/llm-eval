#!/usr/bin/env python3
"""
纯净的API启动脚本，不包含任何测试代码
"""

import os
import sys
import logging
from flask import Flask
from flask_cors import CORS

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 基础配置
    app.config['SECRET_KEY'] = 'dev-secret-key-for-api-development'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///llm_eval.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['DATA_UPLOADS_DIR'] = 'data/uploads'
    app.config['DATA_OUTPUTS_DIR'] = 'data/outputs'
    
    # 初始化扩展
    from app import db, login_manager, migrate, csrf
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # 配置CORS
    CORS(app,
         origins=['http://localhost:3000', 'http://127.0.0.1:3000', 'http://localhost:4000'],
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    )
    
    # 注册API蓝图
    from app.routes.api import api_bp
    app.register_blueprint(api_bp)
    
    # 健康检查端点
    @app.route('/health')
    def health_check():
        return {'status': 'ok', 'message': 'API服务运行正常'}
    
    @app.route('/')
    def index():
        return {'message': 'LLM评估平台API服务', 'version': '1.0.0', 'endpoints': '/api/'}
    
    return app

def init_database(app):
    """初始化数据库"""
    with app.app_context():
        from app import db
        from app.models import User, AIModel, Dataset
        
        # 创建数据库表
        db.create_all()
        print("✅ 数据库表创建成功")
        
        # 创建基础数据
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

if __name__ == '__main__':
    print("🚀 启动LLM评估平台API服务...")
    
    # 创建应用
    app = create_app()
    
    # 初始化数据库
    init_database(app)
    
    print("🚀 启动API开发服务器...")
    print("📍 API端点: http://localhost:5000/api/")
    print("🔍 健康检查: http://localhost:5000/health")
    
    # 启动服务器
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
