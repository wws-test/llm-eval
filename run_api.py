#!/usr/bin/env python3
"""
API开发专用启动脚本
专注于API功能开发，暂时跳过复杂的评估服务依赖
"""

import os
import sys
import datetime
import logging

# 使用应用工厂模式创建应用
def create_api_app():
    """创建API开发专用的Flask应用"""
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    from flask_login import LoginManager
    from flask_migrate import Migrate
    from flask_wtf.csrf import CSRFProtect
    from flask_cors import CORS

    # 创建Flask应用
    app = Flask(__name__)

    # 基础配置
    app.config['SECRET_KEY'] = 'dev-secret-key-for-api-development'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///llm_eval.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # API开发时禁用CSRF

    # 初始化扩展
    from app import db, login_manager, migrate, csrf
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # 配置CORS
    CORS(app,
         origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    )

    # 配置日志
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    return app

# 创建应用实例
app = create_api_app()

# 导入模型（确保数据库表能正确创建）
try:
    from app.models import User, AIModel, Dataset, ChatSession, ChatMessage, ModelEvaluation
    print("✅ 模型导入成功")
except Exception as e:
    print(f"❌ 模型导入失败: {e}")

# 注册API蓝图
try:
    from app.routes.api import api_bp
    app.register_blueprint(api_bp)
    print("✅ API蓝图注册成功")
except Exception as e:
    print(f"❌ API蓝图注册失败: {e}")

# 错误处理
@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"500 Internal Server Error: {error}")
    db.session.rollback()
    
    from flask import request, jsonify
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': '服务器内部错误',
            'timestamp': datetime.datetime.utcnow().isoformat()
        }), 500
    
    return "Internal Server Error", 500

@app.errorhandler(404)
def not_found_error(error):
    from flask import request, jsonify
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': '接口不存在',
            'timestamp': datetime.datetime.utcnow().isoformat()
        }), 404
    
    return "Not Found", 404

# 健康检查端点
@app.route('/health')
def health_check():
    return {'status': 'ok', 'message': 'API服务运行正常'}

# 根路径重定向到健康检查
@app.route('/')
def index():
    return {'message': 'LLM评估平台API服务', 'version': '1.0.0', 'endpoints': '/api/'}

if __name__ == '__main__':
    # 创建数据库表
    with app.app_context():
        try:
            from app import db
            db.create_all()
            print("✅ 数据库表创建成功")

            # 创建一些测试数据
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
                
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
    
    print("🚀 启动API开发服务器...")
    print("📍 API端点: http://localhost:5000/api/")
    print("🔍 健康检查: http://localhost:5000/health")
    print("📖 API文档: 查看各个API蓝图文件")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
